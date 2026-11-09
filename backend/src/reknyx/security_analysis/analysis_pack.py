"""Local evidence/knowledge review packs; no provider, execution or canonical writes.

Packs must remain server-owned: their digest is identity, not a signature or client
input authentication. Observation facts and knowledge references stay separate.
The output vocabulary deliberately cannot express arbitrary factual assertions.
"""
from copy import deepcopy
import hashlib

from reknyx.contracts import canonical_request
from .evidence_interpretation import interpret_evidence
from .evidence_analysis import local_review
from .output_validation import validate_output

VERSION = 'local-analysis-pack-v1'
MAX_PACK_BYTES = 128 * 1024


def _digest(value):
    return hashlib.sha256(canonical_request(value)).hexdigest()


def assemble_pack(*, actor_id, assessment_id, state_revision, scope_version,
                  context, knowledge, query):
    """Pure assembly of already authorized context and verified knowledge pack.

    Application callers use analysis_service.prepare_analysis_pack to enforce
    membership first. This pure function cannot establish ownership by itself.
    """
    if (not all(isinstance(v,str) and 1 <= len(v) <= 128 for v in (actor_id,assessment_id))
            or any(type(v) is not int or v < 1 for v in (state_revision,scope_version))
            or not isinstance(query,str) or len(query)>1000):
        raise ValueError('invalid_analysis_identity')
    interpretation=interpret_evidence(context)
    # Project only existing minimal metadata, not raw messages/assets or extra fields.
    observations=[]
    for fact in interpretation['facts']:
        observations.append({'id':fact['observation_id'],'kind':fact['kind'],'source_tool':fact['source_tool'],
            'facts':{'severity':fact['observed']['source_severity'],'transport':fact['observed']['transport'],
                     'port':fact['observed']['port'],'historical':fact['historical']}})
    evidence={'version':'analysis-evidence-v1','observations':observations,'truncated':interpretation['truncated']}
    if not isinstance(knowledge,dict) or not isinstance(knowledge.get('references'),list) or len(knowledge['references'])>10:
        raise ValueError('invalid_knowledge_pack')
    references=[r.get('reference_id') for r in knowledge['references']]
    if (any(not isinstance(r,str) or not r.startswith('knowledge:') for r in references)
            or len(references)!=len(set(references))
            or set(references).intersection(o['id'] for o in observations)):
        raise ValueError('ambiguous_reference_namespace')
    value={'version':VERSION,'actor_id':actor_id,'assessment_id':assessment_id,
           'state_revision':state_revision,'scope_version':scope_version,
           'context_sha256':_digest(context),'evidence':evidence,'interpretation':interpretation,
           'query':query,'knowledge':deepcopy(knowledge),'execution_authority':'none',
           'limitations':['Local review enrichment only; no provider request or executable proposal.',
               'Valid references do not establish applicability, claim entailment or technical confirmation.']}
    if len(canonical_request(value))>MAX_PACK_BYTES:
        raise ValueError('analysis_pack_size_limit')
    return {**value,'sha256':_digest(value)}


def check_pack(pack):
    if not isinstance(pack,dict) or pack.get('version')!=VERSION or pack.get('execution_authority')!='none':
        raise ValueError('invalid_analysis_pack')
    value={k:v for k,v in pack.items() if k!='sha256'}
    if len(canonical_request(value))>MAX_PACK_BYTES or _digest(value)!=pack.get('sha256'):
        raise ValueError('analysis_pack_digest_mismatch')


def validate_review(pack, output):
    """Restricted topics/reference validation, not arbitrary prose entailment."""
    check_pack(pack)
    fields={'outcome','basis_observation_ids','topics','knowledge_reference_ids'}
    if not isinstance(output,dict) or set(output)!=fields:
        raise ValueError('invalid_analysis_review')
    projected={k:v for k,v in output.items() if k!='knowledge_reference_ids'}
    validate_output(projected,pack['evidence'])
    citations=output['knowledge_reference_ids']
    allowed={r['reference_id'] for r in pack['knowledge']['references']}
    if (not isinstance(citations,list) or len(citations)>10
            or any(not isinstance(r,str) for r in citations) or len(set(citations))!=len(citations)
            or not set(citations)<=allowed):
        raise ValueError('invalid_knowledge_reference')
    return deepcopy(output)


def local_analysis(pack):
    check_pack(pack)
    review=local_review(pack['evidence'])
    return validate_review(pack,{**review,'knowledge_reference_ids':[
        r['reference_id'] for r in pack['knowledge']['references']]})
