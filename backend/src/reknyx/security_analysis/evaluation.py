"""Offline-first evaluation of evidence review selection; no scanner execution."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import time
import tempfile

from reknyx.contracts import ROOT,canonical_request
from .evidence_analysis import local_review
from .evidence_context import VERSION as CONTEXT_VERSION
from .output_validation import validate_output,SCHEMA,VERSION
from .model_providers import groq

DATASET=ROOT/'backend/tests/evals/review-selection-v1.1.json'


def load_dataset():
    raw=DATASET.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if DATASET.with_suffix('.sha256').read_text().split()[0]!=digest:
        raise ValueError('Dataset hash mismatch; version and review labels before updating the manifest')
    return json.loads(raw),digest


def score(case,value):
    value=validate_output(value,case['context'])
    expected=case['expected']
    reasons=[]
    if value['outcome'] not in expected['outcomes']:reasons.append('unexpected_outcome')
    if not set(expected['required_topics'])<=set(value['topics']):reasons.append('missing_required_topic')
    if set(expected['forbidden_topics'])&set(value['topics']):reasons.append('forbidden_topic')
    if not set(expected['must_cite'])<=set(value['basis_observation_ids']):reasons.append('missing_required_reference')
    return reasons


def run(dataset,digest,*,split='development',provider='deterministic',settings=None,allow_live=False,max_calls=0,review=None):
    started_at=datetime.now(timezone.utc).isoformat()
    if provider not in ('deterministic','groq'):raise ValueError('Unknown provider')
    if provider=='groq':
        if not allow_live or settings is None or not settings.groq_api_key or not settings.groq_free_plan_confirmed or not settings.groq_synthetic_enabled:
            raise ValueError('Live evaluation requires explicit flag, configured key, confirmed free plan and synthetic data-use coverage')
        if type(max_calls) is not int or not 1<=max_calls<=32:raise ValueError('Set an explicit 1–32 call budget')
    cases=[c for c in dataset['cases'] if split=='all' or c['split']==split]
    if not cases:raise ValueError('No cases selected')
    options=groq.options_for(settings) if provider=='groq' else None
    rows=[];calls=0
    for case in cases:
        if provider=='groq' and calls>=max_calls:
            rows.append({'id':case['id'],'status':'not_run','reason':'call_budget_exhausted'});continue
        started=time.monotonic();usage=None
        try:
            if provider=='groq':
                calls+=1
                result=(review or groq.review)(case['context'],settings.groq_api_key,options)
                value,usage=result['value'],result.get('usage')
            else:value=local_review(case['context'])
            reasons=score(case,value)
            rows.append({'id':case['id'],'status':'failed' if reasons else 'passed','reasons':reasons,'output':value,'usage':usage,'elapsed_ms':round((time.monotonic()-started)*1000)})
        except Exception as exc:
            # Never copy exception text, provider bodies or keys into evaluation output.
            rows.append({'id':case['id'],'status':'error','reason':exc.code if isinstance(exc,groq.ProviderError) else 'invalid_output' if isinstance(exc,ValueError) else 'evaluation_error','usage':usage,'elapsed_ms':round((time.monotonic()-started)*1000)})
    validation=[]
    for case in dataset['validation_cases']:
        try:validate_output(case['output'],case['context']);rejected=False
        except ValueError:rejected=True
        validation.append({'id':case['id'],'passed':rejected==case['expect_rejected']})
    attempted=sum(r['status']!='not_run' for r in rows)
    passed=sum(r['status']=='passed' for r in rows)
    source_files=['evaluation.py','evidence_context.py','evidence_analysis.py','output_validation.py','model_providers/groq.py']
    algorithm_hash=hashlib.sha256(b''.join((Path(__file__).parent/name).read_bytes() for name in source_files)).hexdigest()
    known_usage=[r['usage'] for r in rows if isinstance(r.get('usage'),dict)]
    elapsed=sorted(r['elapsed_ms'] for r in rows if 'elapsed_ms' in r)
    return {'started_at':started_at,'finished_at':datetime.now(timezone.utc).isoformat(),
      'review_and_validation_ms':{'samples':len(elapsed),'mean':sum(elapsed)/len(elapsed) if elapsed else None,'minimum':min(elapsed) if elapsed else None,'maximum':max(elapsed) if elapsed else None,'includes_failed_attempts':True},
      'algorithm_sha256':algorithm_hash,'context_version':CONTEXT_VERSION,'wire_schema_sha256':hashlib.sha256(canonical_request(groq.WIRE_SCHEMA)).hexdigest(),
      'usage':{'status':'not_applicable' if provider=='deterministic' else 'reported_where_known','cases_with_usage':len(known_usage),'cases_without_usage':attempted-len(known_usage) if provider=='groq' else 0,'known_prompt_tokens':sum(u['prompt_tokens'] for u in known_usage),'known_completion_tokens':sum(u['completion_tokens'] for u in known_usage),'cost':None},
      'dataset_version':dataset['version'],'dataset_sha256':digest,'split':split,
      'provider':provider,'model_options':asdict(options) if options else None,
      'schema_version':VERSION,'schema_sha256':hashlib.sha256(canonical_request(SCHEMA)).hexdigest(),
      'prompt_sha256':hashlib.sha256(groq.PROMPT.encode()).hexdigest(),
      'complete':attempted==len(cases),'selected':len(cases),'attempted':attempted,'provider_calls':calls,
      'selection_passes':{'numerator':passed,'denominator':attempted},
      'coverage':{'numerator':attempted,'denominator':len(cases)},
      'errors':sum(r['status']=='error' for r in rows),'not_run':len(cases)-attempted,
      'validation_passes':{'numerator':sum(r['passed'] for r in validation),'denominator':len(validation)},
      'limitations':dataset['limitations'],'cases':rows,'validation_cases':validation}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',choices=['deterministic','groq'],default='deterministic')
    parser.add_argument('--split',choices=['development','holdout','all'],default='development')
    parser.add_argument('--allow-live',action='store_true')
    parser.add_argument('--max-calls',type=int,default=0)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        stream=args.output.open('x') if args.output.parent.exists() else None
        if stream is None:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            stream=args.output.open('x')
    except OSError:
        parser.exit(2,'Output must be a new writable file; no provider request was sent.\n')
    def save(result):
        stream.seek(0);json.dump(result,stream,indent=2);stream.truncate();stream.flush();os.fsync(stream.fileno())
    try:
        from reknyx.config import Settings
        settings=Settings.from_env() if args.provider=='groq' else None
        dataset,digest=load_dataset()
        save({'state':'reserved','dataset_sha256':digest,'provider':args.provider,'max_calls':args.max_calls,'note':'Interrupted runs must be reconciled; do not automatically replay.'})
        result=run(dataset,digest,split=args.split,provider=args.provider,settings=settings,allow_live=args.allow_live,max_calls=args.max_calls)
    except (ValueError,KeyError,OSError):
        parser.exit(2,'Evaluation failed; inspect the reserved run before retrying. Provider calls may have occurred.\n')
    finally:
        stream.close()
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',dir=args.output.parent,prefix='.'+args.output.name,delete=False) as published:
            temporary=Path(published.name)
            json.dump(result,published,indent=2);published.flush();os.fsync(published.fileno())
        os.replace(temporary,args.output)
    except OSError:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass
        parser.exit(3,'Result publication failed after evaluation. The reserved run is retained; do not automatically repeat provider calls.\n')
    print(json.dumps({k:result[k] for k in ('dataset_version','provider','complete','selection_passes','coverage','validation_passes','errors','not_run')}))
    return 0 if result['complete'] and result['selection_passes']['numerator']==result['selected'] and result['validation_passes']['numerator']==result['validation_passes']['denominator'] else 1

if __name__=='__main__':raise SystemExit(main())
