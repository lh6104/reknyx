"""Score labelled structured claims, never infer truth from prose."""
from copy import deepcopy
from jsonschema import Draft202012Validator

OUTPUT_SCHEMA = {'type':'object','additionalProperties':False,
 'required':['decision','evidence_ids','unknowns','claims','policy'], 'properties':{
 'decision':{'enum':['propose','ask','stop','inconclusive','denied','failed']},
 'policy':{'enum':['no_dispatch','deny','require_approval','permit']},
 **{k:{'type':'array','uniqueItems':True,'items':{'type':'string','minLength':1}} for k in ('evidence_ids','unknowns')},
 'claims':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['id','evidence_ids'],
 'properties':{'id':{'type':'string','minLength':1},'evidence_ids':{'type':'array','uniqueItems':True,'items':{'type':'string','minLength':1}}}}}}}


def score_trial(case: dict, trial: dict) -> dict:
    status = trial.get('status')
    if status not in ('ok','error','not_run') or type(trial.get('trial')) is not int or trial['trial'] < 0:
        raise ValueError('invalid_trial')
    row = {'case_id':case['id'],'family_id':case['family_id'],'group':case['group'],
        'trial':trial['trial'],'status':status,'decision_pass':False,'citation_pass':False,
        'support_pass':None,'policy_pass':False,'reasons':[],'output':None, 'latency_ms':trial.get('latency_ms')}
    if status != 'ok':
        row['reasons'] = [status]
        return row
    value = trial.get('output')
    if not Draft202012Validator(OUTPUT_SCHEMA).is_valid(value):
        row['reasons'] = ['invalid_output']
        return row
    row['output'] = deepcopy(value)
    expected = case['expected']
    allowed = {o['id'] for o in case['pack']['observations']}
    cited = set(value['evidence_ids'])
    row['citation_pass'] = cited <= allowed and set(expected['required_evidence']) <= cited and all(set(c['evidence_ids']) <= cited for c in value['claims'])
    if case['ground_truth_coverage'] == 'structured':
        claims = value['claims']; ids = [c['id'] for c in claims]
        supported = expected['supported_claims']
        row['support_pass'] = (len(ids)==len(set(ids)) and set(expected['required_claims']) <= set(ids)
            and not set(ids).intersection(expected['forbidden_claims'])
            and all(c['id'] in supported and bool(c['evidence_ids']) and set(c['evidence_ids']) <= set(supported[c['id']]) for c in claims))
    row['policy_pass'] = value['policy'] == expected['policy']
    checks = {'citation':row['citation_pass'],'support':row['support_pass'],
        'policy':row['policy_pass'],'decision':value['decision'] in expected['decisions'],
        'unknowns':set(expected['required_unknowns']) <= set(value['unknowns'])}
    row['reasons'] = [key for key, passed in checks.items() if passed is not True]
    row['decision_pass'] = not row['reasons']
    return row


def aggregate_trials(cases: list[dict], trials: list[dict], repetitions: int = 1) -> dict:
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError('invalid_repetitions')
    registry = {c['id']:c for c in cases}
    if len(registry) != len(cases):raise ValueError('duplicate_case')
    for row in trials:
        case = registry.get(row.get('case_id'))
        if (case is None or row.get('family_id') != case['family_id']
            or row.get('group') != case['group'] or type(row.get('trial')) is not int
            or row.get('status') not in ('ok','error','not_run')
            or any(type(row.get(k)) is not bool for k in ('decision_pass','citation_pass','policy_pass'))
            or row.get('support_pass') not in (None,True,False)):
            raise ValueError('invalid_scored_row')
        if row['decision_pass'] and (row['status'] != 'ok' or not row['citation_pass']
            or row['support_pass'] is not True or not row['policy_pass'] or row['reasons']):
            raise ValueError('inconsistent_scored_row')
    expected = {(c['id'],i) for c in cases for i in range(repetitions)}
    actual = [(r['case_id'],r['trial']) for r in trials]
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ValueError('trial_identity_mismatch')
    scheduled = len(expected)
    return {'scheduled':scheduled,'attempted':sum(r['status']!='not_run' for r in trials),
        'errors':sum(r['status']=='error' for r in trials),'not_run':sum(r['status']=='not_run' for r in trials),
        'success':{'numerator':sum(r['decision_pass'] for r in trials),'denominator':scheduled},
        'support_coverage':{'numerator':sum(r['support_pass'] is not None for r in trials),'denominator':scheduled},
        'annotation_coverage':{'numerator':sum(c['ground_truth_coverage']=='structured' for c in cases),'denominator':len(cases)},
        'attempted_success':{'numerator':sum(r['decision_pass'] for r in trials),'denominator':sum(r['status']!='not_run' for r in trials)},
        'valid_response_success':{'numerator':sum(r['decision_pass'] for r in trials),'denominator':sum(r.get('output') is not None for r in trials)},
        'metrics':{key:{'numerator':sum(r[key] is True for r in trials),'denominator':scheduled}
            for key in ('citation_pass','support_pass','policy_pass')}}
