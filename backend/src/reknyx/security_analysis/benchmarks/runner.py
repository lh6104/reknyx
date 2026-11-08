"""Offline replay with injected transport. No credentials, networking or dispatch."""
from copy import deepcopy
import hashlib
from time import perf_counter
from reknyx.contracts import canonical_request
from .manifest import validate_manifest, validate_cases
from .scoring import aggregate_trials, score_trial


def run_replay(cases: list[dict], manifest: dict, transport=None) -> dict:
    manifest = validate_manifest(manifest)
    validate_cases(cases)
    if any(c['split'] != manifest['split'] or c['provenance'] != 'synthetic_fixture' for c in cases):
        raise ValueError('offline_synthetic_split_required')
    # Bind the actual cases including labels independently of the user-supplied dataset identity.
    case_digest = hashlib.sha256(canonical_request(cases)).hexdigest()
    rows, calls = [], 0
    for case in cases:
        for trial in range(manifest['repetitions']):
            result = {'trial':trial,'status':'not_run'}
            if transport is not None and calls < manifest['limits']['max_calls']:
                calls += 1
                start = perf_counter()
                try:
                    # Explicit projection; labels and arbitrary case/pack fields never cross this seam.
                    pack = {'query':case['pack']['query'], 'observations':[
                        {k:o[k] for k in ('id','kind')} for o in case['pack']['observations']]}
                    result.update(status='ok',output=transport.generate(deepcopy(pack),deepcopy(manifest['limits'])))
                except (TimeoutError, ValueError):
                    result.update(status='error')
                result['latency_ms'] = (perf_counter()-start)*1000
            rows.append(score_trial(case,result))
    return {'version':'analyst-offline-v1','manifest':manifest,'case_digest':case_digest,
        'cases':deepcopy(cases),'trials':rows,'summary':aggregate_trials(cases,rows,manifest['repetitions']),
        'transport_calls':calls,'cost':None,'evidence_level':'synthetic_offline',
        'limitations':['Structured claim labels are not open-text entailment or live acceptance.',
            'Transport deadlines are advisory in offline replay; no live transport is provided.']}
