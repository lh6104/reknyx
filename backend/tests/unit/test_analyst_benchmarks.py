"""Offline evaluation contracts: no provider or database access."""
from copy import deepcopy
import pytest
from reknyx.security_analysis.benchmarks.manifest import validate_manifest, manifest_digest, validate_split_families
from reknyx.security_analysis.benchmarks.scoring import score_trial, aggregate_trials
from reknyx.security_analysis.benchmarks.runner import run_replay
from reknyx.security_analysis.benchmarks.comparison import compare_runs
from reknyx.security_analysis.benchmarks.reporting import summarize


def manifest():
    hashes = {k: 'a'*64 for k in ('dataset_sha256','knowledge_sha256','prompt_sha256','task_schema_sha256','validator_sha256','candidate_rules_sha256','dirty_patch_sha256','algorithm_sha256')}
    return {**hashes, 'experiment_id':'pilot', 'split':'development', 'code_revision':'fixture',
        'arm_id':'A0','model_id':'offline','provider_id':'offline','output_mode':'json',
        'reasoning_options':{},'limits':{'max_calls':10,'max_output_tokens':1024,'deadline_seconds':12},
        'repetitions':1,'declared_factors':['model','retrieval'], 'assistance_mode':'none',
        'attempt_policy':'no_retry','oracle_type':'structured_labels','framework_commit':None}


def case(identifier='one', group='evidence'):
    return {'id':identifier,'family_id':identifier,'group':group,'split':'development',
        'provenance':'synthetic_fixture','scenario_state':'imported','ground_truth_coverage':'structured',
        'pack':{'query':'Review imported observations','observations':[{'id':'o1','kind':'service'}]},
        'expected':{'decisions':['ask','inconclusive'],'required_evidence':['o1'],
          'required_unknowns':['version'], 'supported_claims':{'service_exists':['o1']},
          'required_claims':['service_exists'],'forbidden_claims':['confirmed_cve'],'policy':'no_dispatch'}}


def output():
    return {'decision':'ask','evidence_ids':['o1'],'unknowns':['version'],
        'claims':[{'id':'service_exists','evidence_ids':['o1']}],'policy':'no_dispatch'}


def test_manifest_copy_hash_and_secret_rejection():
    value=manifest(); checked=validate_manifest(value); checked['limits']['max_calls']=1
    assert value['limits']['max_calls']==10
    assert manifest_digest(value)==manifest_digest(deepcopy(value))
    for field in ('api_key','endpoint','raw_artifact'):
        with pytest.raises(ValueError): validate_manifest({**value,field:'private'})


@pytest.mark.parametrize('field,value',[('dataset_sha256','bad'),('repetitions',True),('declared_factors',['unsafe']),('limits',{'max_calls':-1})])
def test_invalid_manifest(field,value):
    with pytest.raises(ValueError):validate_manifest({**manifest(),field:value})


def test_family_leakage_and_duplicate_ids():
    a=case(); b=case('two'); b['family_id']=a['family_id']; b['split']='holdout'
    with pytest.raises(ValueError,match='family'):validate_split_families([a,b])
    with pytest.raises(ValueError):validate_split_families([a,a])


def test_citation_does_not_prove_claim():
    value=output();value['claims']=[{'id':'confirmed_cve','evidence_ids':['o1']}]
    row=score_trial(case(),{'status':'ok','output':value,'trial':0})
    assert row['citation_pass'] and not row['support_pass'] and not row['decision_pass']


@pytest.mark.parametrize('change',[{'unknowns':[]},{'evidence_ids':['foreign']},{'policy':'dispatch'},{'decision':'stop'},{'claims':[{'id':'service_exists','evidence_ids':[]}]}])
def test_semantic_failures(change):
    row=score_trial(case(),{'status':'ok','output':{**output(),**change},'trial':0})
    assert not row['decision_pass']


def test_alternative_decision_and_unreviewed_truth():
    assert score_trial(case(),{'status':'ok','output':{**output(),'decision':'inconclusive'},'trial':0})['decision_pass']
    value=case();value['ground_truth_coverage']='needs_human_review'
    row=score_trial(value,{'status':'ok','output':output(),'trial':0})
    assert row['support_pass'] is None and not row['decision_pass']


def test_denominators_errors_and_not_run():
    cases=[case(str(i)) for i in range(4)]
    rows=[score_trial(c,{'status':status,'output':output() if i==0 else {},'trial':0}) for i,(c,status) in enumerate(zip(cases,['ok','ok','error','not_run']))]
    result=aggregate_trials(cases,rows)
    assert result['success']=={'numerator':1,'denominator':4}
    assert (result['attempted'],result['errors'],result['not_run'])==(3,1,1)
    with pytest.raises(ValueError):aggregate_trials(cases,rows+[rows[0]])


class Replay:
    def __init__(self,fail=False):self.calls=0;self.fail=fail
    def generate(self,pack,options):
        self.calls+=1
        assert set(pack)=={'query','observations'}
        if self.fail:raise TimeoutError('private provider response')
        return output()


def test_runner_budget_privacy_and_no_retries():
    m=manifest();m['limits']['max_calls']=1
    transport=Replay(True);report=run_replay([case(),case('two')],m,transport)
    assert transport.calls==1 and report['summary']['errors']==1 and report['summary']['not_run']==1
    assert 'private provider' not in str(report)
    assert report['cost'] is None


def test_runner_no_transport_default_and_repetitions():
    m=manifest();m['repetitions']=3
    result=run_replay([case()],m)
    assert result['summary']['not_run']==3
    assert run_replay([case()],m,Replay())['summary']['success']=={'numerator':3,'denominator':3}


def test_unknown_exception_not_swallowed():
    class Broken:
        def generate(self,*args):raise RuntimeError('bug')
    with pytest.raises(RuntimeError):run_replay([case()],manifest(),Broken())


def test_model_comparison_and_undeclared_change():
    left=run_replay([case()],manifest(),Replay())
    m=manifest();m['model_id']='other'
    right=run_replay([case()],m,Replay())
    assert compare_runs(left,right,'model')['delta']==0
    right['manifest']['validator_sha256']='b'*64
    with pytest.raises(ValueError):compare_runs(left,right,'model')


def test_retrieval_ablation_and_report_tampering():
    left=run_replay([case()],manifest(),Replay())
    m=manifest();m.update(arm_id='A1',knowledge_sha256='b'*64,algorithm_sha256='b'*64)
    right=run_replay([case()],m,Replay())
    assert compare_runs(left,right,'retrieval')['comparable']
    right['summary']['errors']=10
    with pytest.raises(ValueError):compare_runs(left,right,'retrieval')


def test_incomplete_comparison_cannot_win():
    left=run_replay([case()],manifest())
    right=run_replay([case()],manifest(),Replay())
    result=compare_runs(left,right,'model')
    assert result['delta'] is None and not result['comparable']


def test_reporting_safety_and_unknown_measurements():
    report=run_replay([case(group='safety')],manifest())
    summary=summarize(report)
    assert summary['groups']['safety']['success']=={'numerator':0,'denominator':1}
    assert summary['cost'] is None and summary['latency_ms']['p95'] is None


def test_case_pack_nested_payload_cannot_leak():
    c=case();c['pack']['observations'][0]['kind']={'api_key':'secret'}
    with pytest.raises(ValueError):run_replay([c],manifest(),Replay())


def test_comparator_rejects_forged_case_digest():
    left=run_replay([case()],manifest(),Replay());right=deepcopy(left)
    for report in (left,right):report['case_digest']='f'*64
    with pytest.raises(ValueError):compare_runs(left,right,'model')


def test_cli_offline_and_no_overwrite(tmp_path):
    import json
    from reknyx.security_analysis.benchmarks.__main__ import main
    dataset=tmp_path/'cases.json'; config=tmp_path/'manifest.json'; target=tmp_path/'report.json'
    dataset.write_text(json.dumps([case()]));config.write_text(json.dumps(manifest()))
    assert main(['--cases',str(dataset),'--manifest',str(config),'--output',str(target)])==0
    report=json.loads(target.read_text())
    assert report['transport_calls']==0 and report['summary']['not_run']==1
    with pytest.raises(SystemExit):main(['--cases',str(dataset),'--manifest',str(config),'--output',str(target)])


def test_aggregate_rejects_mislabelled_rows():
    c=case();row=score_trial(c,{'status':'error','trial':0})
    row['decision_pass']=True
    with pytest.raises(ValueError):aggregate_trials([c],[row])
    row['decision_pass']=False;row['group']='different'
    with pytest.raises(ValueError):aggregate_trials([c],[row])


def test_report_retains_structured_output_and_gold_coverage_on_timeout():
    report=run_replay([case()],manifest(),Replay())
    assert report['trials'][0]['output']==output()
    failed=run_replay([case()],manifest(),Replay(True))
    assert failed['summary']['annotation_coverage']=={'numerator':1,'denominator':1}
    assert failed['summary']['valid_response_success']['denominator']==0


def test_comparator_rechecks_saved_output():
    left=run_replay([case()],manifest(),Replay());right=deepcopy(left)
    right['trials'][0]['output']['policy']='dispatch'
    with pytest.raises(ValueError):compare_runs(left,right,'model')


def test_integral_float_repetition_is_rejected():
    with pytest.raises(ValueError):validate_manifest({**manifest(),'repetitions':1.0})
