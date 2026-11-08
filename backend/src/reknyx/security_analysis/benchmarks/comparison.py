"""Descriptive paired comparisons with explicitly declared experimental factors."""
import hashlib
from reknyx.contracts import canonical_request
from .manifest import validate_manifest, validate_cases
from .scoring import aggregate_trials, score_trial

CHANGES = {'model':{'model_id','provider_id','output_mode'},
 'retrieval':{'knowledge_sha256','algorithm_sha256','arm_id'},
 'architecture':{'knowledge_sha256','algorithm_sha256','arm_id'},
 'prompt':{'prompt_sha256'},'reasoning':{'reasoning_options'}}


def compare_runs(left: dict, right: dict, factor: str) -> dict:
    if factor not in CHANGES:raise ValueError('invalid_factor')
    a,b = validate_manifest(left['manifest']), validate_manifest(right['manifest'])
    if factor not in a['declared_factors'] or factor not in b['declared_factors']:
        raise ValueError('undeclared_factor')
    for field in a:
        if field not in CHANGES[factor] | {'experiment_id'} and a[field] != b[field]:
            raise ValueError('incompatible_metadata: '+field)
    if left['case_digest'] != right['case_digest'] or left['cases'] != right['cases']:
        raise ValueError('case_mismatch')
    for report in (left,right):
        validate_cases(report['cases'])
        if hashlib.sha256(canonical_request(report['cases'])).hexdigest() != report['case_digest']:
            raise ValueError('invalid_case_digest')
        registry={c['id']:c for c in report['cases']}
        for row in report['trials']:
            if row.get('case_id') not in registry:raise ValueError('invalid_case')
            rescored=score_trial(registry[row['case_id']],row)
            if rescored != row:raise ValueError('score_output_mismatch')
        checked=aggregate_trials(report['cases'],report['trials'],report['manifest']['repetitions'])
        if checked != report['summary']:raise ValueError('inconsistent_counters')
    l={(r['case_id'],r['trial']):r for r in left['trials']}
    r={(v['case_id'],v['trial']):v for v in right['trials']}
    pairs=[{'case_id':key[0],'trial':key[1],'baseline':l[key]['decision_pass'],
        'candidate':r[key]['decision_pass']} for key in l]
    complete=not left['summary']['not_run'] and not right['summary']['not_run']
    n=len(pairs)
    return {'factor':factor,'baseline_manifest':a,'candidate_manifest':b,'comparable':complete,
        'delta':sum(int(p['candidate'])-int(p['baseline']) for p in pairs)/n if complete and n else None,
        'pairs':pairs,'limitations':['Descriptive paired delta only; no significance or generalization claim.']}
