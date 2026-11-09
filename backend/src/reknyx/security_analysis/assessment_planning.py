"""Short durable reservations, transaction-free inference and immutable decisions."""
import hashlib
import time
from uuid import uuid4
from sqlalchemy import select

from reknyx.assessments.service import require_membership
from reknyx.contracts import canonical_request,validate
from reknyx.infrastructure.errors import DomainError,error_body
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.models import AnalysisAttempt,AnalysisDecision,AuthSession,IdempotencyRecord,Message,ScopeRevision,Assessment,Membership
from reknyx.shared.time import now,timestamp
from .evidence_context import build_context
from .evidence_analysis import local_review,render_review,review_unknowns
from .evidence_interpretation import interpret_evidence, VERSION as INTERPRETATION_VERSION
from .output_validation import validate_output,SCHEMA,VERSION,ReviewValidationError
from .review_policy import VERSION as POLICY_VERSION
from .model_providers import groq


def remaining_budget(db,assessment_id,budget):
    remaining=dict(budget)
    for attempt in db.scalars(select(AnalysisAttempt).where(AnalysisAttempt.assessment_id==assessment_id)):
        usage=attempt.data.get('usage') or {}
        for field,value in attempt.data.get('reserved',{}).items():
            actual=usage.get({'max_input_tokens':'prompt_tokens','max_output_tokens':'completion_tokens'}.get(field,''),0)
            remaining[field]=max(0,remaining[field]-max(value,actual))
    return remaining


def create_plan(db,auth,settings,assessment_id,value,record,request_id):
    namespace=record.namespace
    identifier=record.body['operation_id']
    instant=now()
    options=groq.options_for(settings)
    try:
        assessment=require_membership(db,auth.actor_id,assessment_id,lock=True)
        if value['expected_revision']!=assessment.data['state_revision']:raise DomainError(409,'stale_revision')
        retry=value['retry']
        if retry:
            prior=db.get(AnalysisDecision,retry['prior_id']) if retry['kind']=='decision' else None
            if prior is None or prior.assessment_id!=assessment_id:raise DomainError(404,'not_found')
        scope=db.get(ScopeRevision,(assessment_id,assessment.data['scope_version'])).data
        context=build_context(db,assessment)
        interpretation=interpret_evidence(context)
        budget=remaining_budget(db,assessment_id,scope['budget'])
        reserved={}
        failure=None
        provider=settings.analysis_provider
        if provider=='groq':
            if not settings.groq_api_key:failure='provider_not_configured'
            elif not settings.groq_free_plan_confirmed:failure='provider_free_plan_not_confirmed'
            elif not settings.groq_synthetic_enabled or not context['synthetic_only']:failure='model_data_use_not_covered'
            else:
                required={'max_model_calls':1,'max_input_tokens':groq.input_reservation(context,options),'max_output_tokens':options.max_output_tokens}
                if any(budget[k]<n for k,n in required.items()):failure='model_budget_exhausted'
                else:
                    reserved=required
                    budget={k:n-required.get(k,0) for k,n in budget.items()}
        attempt=AnalysisAttempt(id=identifier,assessment_id=assessment_id,created_at=instant,data={
            'state':'reserved','actor_id':auth.actor_id,'operation_namespace':namespace,'provider':provider,'model':options.model if provider=='groq' else None,
            'request_options':{'model':options.model,'temperature':options.temperature,'reasoning_effort':options.reasoning_effort,'max_output_tokens':options.max_output_tokens},'free_plan_confirmed':settings.groq_free_plan_confirmed,'adapter_version':'groq-chat-strict-v2' if provider=='groq' else 'local-review-v2','endpoint':groq.ENDPOINT if provider=='groq' else None,'source':'llm' if provider=='groq' else 'deterministic',
            'state_revision':assessment.data['state_revision'],'scope_version':scope['version'],'scope_hash':scope['hash'],
            'context':context,'http_request_id':request_id,'context_hash':context['sha256'],'context_version':context['version'],'schema_version':VERSION,
            'selection_policy_version':POLICY_VERSION,
            'interpretation_version':INTERPRETATION_VERSION,
            'interpretation_hash':interpretation['sha256'],'interpretation':interpretation,
            'schema_hash':hashlib.sha256(canonical_request(SCHEMA)).hexdigest(),
            'wire_schema_hash':hashlib.sha256(canonical_request(groq.WIRE_SCHEMA)).hexdigest(),
            'prompt_hash':hashlib.sha256(groq.PROMPT.encode()).hexdigest(),'reserved':reserved,
            'usage':None,'cost':None,'cost_status':'unknown' if reserved else 'not_applicable','attempt_count':1 if reserved else 0,'failure_code':None,'elapsed_ms':None})
        db.add(attempt)
        db.commit()  # No transaction or row lock crosses the provider boundary.
    except DomainError as exc:
        record.status,record.body=exc.status,error_body(exc,request_id)
        db.commit()
        return record.status,record.body,None

    started=time.monotonic()
    result=None
    provider_metadata=None
    provider_http_status=None
    validation_failure=None
    if failure is None:
        try:
            if provider=='groq':
                provider_metadata=groq.review(context,settings.groq_api_key,options)
                provider_http_status=provider_metadata.get('http_status')
                usage=provider_metadata.get('usage')
                if usage and (usage['prompt_tokens']>reserved['max_input_tokens'] or usage['completion_tokens']>reserved['max_output_tokens']):
                    raise groq.ProviderError('provider_usage_exceeds_reservation')
                result=validate_output(provider_metadata['value'],context)
            else:result=local_review(context)
        except groq.ProviderError as exc:
            failure=exc.code
            provider_http_status=exc.http_status if exc.http_status is not None else provider_http_status
        except ReviewValidationError as exc:
            failure='invalid_model_output'
            validation_failure=exc.code
        except (ValueError,TypeError,KeyError):failure='invalid_model_output'
        except Exception:failure='analysis_unavailable'
    elapsed=int((time.monotonic()-started)*1000)
    # Refresh identities before accepting output; analyst changes can occur during inference.
    db.expire_all()
    record=db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.namespace==namespace).with_for_update())
    assessment=db.scalar(select(Assessment).where(Assessment.id==assessment_id).with_for_update())
    if assessment is None:raise DomainError(404,'not_found')
    if db.get(Membership,(assessment_id,auth.actor_id)) is None:failure='assessment_access_revoked'
    current_auth=db.get(AuthSession,auth.token_hash,populate_existing=True)
    if current_auth is None or current_auth.revoked or current_auth.expires_at<=now():
        failure='session_expired'
    attempt=db.get(AnalysisAttempt,identifier)
    frozen=attempt.data
    if failure not in ('assessment_access_revoked','session_expired') and (assessment.data['state_revision']!=frozen['state_revision'] or assessment.data['scope_version']!=frozen['scope_version']):
        failure='stale_analysis'
    rationale=render_review(result,context) if failure is None else 'Evidence analysis did not complete: '+failure+'. No action was proposed.'
    limitations=['No scanner execution or action proposal is available from evidence review.',
                  'Local deterministic review; no language model was called.' if provider=='deterministic' else 'Groq did not produce an accepted evidence review.' if failure else 'Groq selected review topics and evidence references; server templates render the explanation.']
    if context['truncated']:limitations.append('Context is limited to the latest 32 observations; this is not a complete assessment review.')
    budget=remaining_budget(db,assessment_id,scope['budget'])
    if provider_metadata and provider_metadata.get('usage'):
        for field,usage_field in [('max_input_tokens','prompt_tokens'),('max_output_tokens','completion_tokens')]:
            budget[field]=max(0,budget[field]-max(0,provider_metadata['usage'][usage_field]-reserved.get(field,0)))
    decision={'id':identifier,'assessment_id':assessment_id,'state_revision':frozen['state_revision'],
       'scope_version':frozen['scope_version'],'created_at':timestamp(now()),'source':frozen['source'],
       'candidate_profile':None,'basis_observation_ids':result['basis_observation_ids'] if failure is None else [],
       'proposal_id':None,'rationale':rationale,'policy_result':None,'budget_remaining':budget,
       'outcome':result['outcome'] if failure is None else 'failed',
       'unknowns':review_unknowns(result,context) if failure is None else ['Evidence analysis failed; source applicability remains unknown.'],
       'limitations':limitations,'failure_code':failure,'retry_of':value['retry']}
    validate('DecisionRecord',decision)
    db.add(AnalysisDecision(id=identifier,assessment_id=assessment_id,created_at=now(),data=decision))
    attempt.data={**frozen,'state':'failed' if failure else 'completed','failure_code':failure,'elapsed_ms':elapsed,
                  'validation_failure_code':validation_failure,
                  'provider_http_status':provider_http_status,'usage':provider_metadata.get('usage') if provider_metadata else None,
                  'provider_request_id':provider_metadata.get('request_id') if provider_metadata else None,
                  'output_hash':hashlib.sha256(canonical_request(provider_metadata['value'])).hexdigest() if provider_metadata else None,
                  'validated_output':result if failure is None else None,
                  'accepted_interpretation':interpret_evidence(context,result['basis_observation_ids']) if failure is None else None}
    # Keep conservative reservations even when usage is unknown. No automatic refund/retry.
    status=200
    body={'decision':decision,'proposal':None}
    if failure:
        status=404 if failure=='assessment_access_revoked' else 409 if failure=='stale_analysis' else 401 if failure=='session_expired' else 503
        body=error_body(DomainError(status,'not_found' if status==404 else 'stale_revision' if status==409 else 'unauthenticated' if status==401 else 'dependency_unavailable',
             'Evidence analysis failed: '+failure,details=[{'field':None,'reason':failure,'resource_id':identifier}]),request_id)
    else:
        assessment.data={**assessment.data,'state_revision':assessment.data['state_revision']+1}
        message={'id':str(uuid4()),'assessment_id':assessment_id,'role':'assistant','content':rationale,
             'created_at':timestamp(now()),'actor_id':None,'state_revision':assessment.data['state_revision'],
             'basis_observation_ids':decision['basis_observation_ids'],'proposal_ids':[],
             'source':decision['source'],'limitations':limitations}
        validate('ConversationMessage',message)
        db.add(Message(id=message['id'],assessment_id=assessment_id,created_at=now(),data=message))
        validate('PlanResult',body)
    append_event(db,None,assessment_id,'analysis.failed' if failure else 'analysis.completed',identifier,
                 'Explicit evidence review; source '+decision['source']+('; '+failure if failure else ''),'failed' if failure else 'succeeded',actor_type='system')
    record.status,record.body,record.location=status,body,None
    db.commit()
    return status,body,None
