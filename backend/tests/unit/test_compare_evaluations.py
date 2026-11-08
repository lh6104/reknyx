from copy import deepcopy
import pytest
from reknyx.security_analysis.evaluation import load_dataset,run
from reknyx.security_analysis.compare_evaluations import compare


def reports():
    data,digest=load_dataset()
    a=run(data,digest);b=deepcopy(a)
    b['provider']='groq';b['model_options']={'model':'openai/gpt-oss-120b'}
    return a,b


def test_comparison_matches_by_case_and_cannot_hide_regression():
    a,b=reports()
    b['cases'][0]['status']='failed';b['selection_passes']['numerator']-=1
    result=compare(a,b)
    assert result['paired_counts']['candidate_regression']==1
    assert result['paired_counts']['both_passed']==7
    assert result['provider_requests_sent'] is False

@pytest.mark.parametrize('key',['dataset_sha256','algorithm_sha256','prompt_sha256','schema_sha256','split','selection_policy_version'])
def test_different_evaluation_authority_is_not_comparable(key):
    a,b=reports();b[key]='changed'
    with pytest.raises(ValueError):compare(a,b)


def test_partial_and_inconsistent_reports_are_explicit():
    a,b=reports()
    b['cases'][0]['status']='not_run';b.update(attempted=7,complete=False,not_run=1)
    b['selection_passes']={'numerator':7,'denominator':7}
    b['coverage']={'numerator':7,'denominator':8}
    assert compare(a,b)['paired_counts']['not_comparable']==1
    b['selection_passes']['numerator']=8
    with pytest.raises(ValueError):compare(a,b)


def test_duplicate_case_cannot_count_twice():
    a,b=reports();b['cases'][1]['id']=b['cases'][0]['id']
    with pytest.raises(ValueError):compare(a,b)


def test_inconsistent_coverage_is_rejected():
    a,b=reports();b['coverage']={'numerator':1,'denominator':999}
    with pytest.raises(ValueError):compare(a,b)


def test_non_object_report_is_rejected():
    a,_=reports()
    with pytest.raises(ValueError):compare(a,[])
