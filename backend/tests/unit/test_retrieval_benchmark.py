from datetime import datetime,timezone
import json,math
from pathlib import Path
from copy import deepcopy
import pytest
from reknyx.security_analysis.knowledge import load_snapshot
from reknyx.security_analysis.benchmarks.retrieval import score_ranking, run_retrieval_benchmark

BASE=Path(__file__).parents[1]/'fixtures/knowledge'
NOW=datetime(2026,11,9,tzinfo=timezone.utc)


def inputs():
    return load_snapshot(json.loads((BASE/'synthetic-snapshot-v1.json').read_text())),json.loads((BASE/'retrieval-development-v1.json').read_text())


def test_ranking_metrics_use_correct_denominators():
    result=score_ranking(['CWE-89','CWE-79'],['CWE-79'],k=2)
    assert result['recall']==1 and result['reciprocal_rank']==.5
    assert result['ndcg']==pytest.approx(1/math.log2(3))
    empty=score_ranking(['CWE-89'],[],k=2)
    assert empty['recall'] is None and empty['empty_gold_correct'] is False


def test_exact_baseline_covers_all_cases_without_retrieval_or_model_calls():
    snapshot,dataset=inputs()
    report=run_retrieval_benchmark(None,snapshot,dataset,as_of=NOW,modes=('exact',))
    arm=report['arms']['exact']
    assert arm['coverage']=={'numerator':5,'denominator':5}
    assert arm['metrics']['recall_at_k']=={'sum':1.0,'denominator':4,'value':.25}
    assert report['provider_calls']==0 and report['snapshot_sha256']==snapshot['sha256']
    assert report['label_status']=='project_authored_not_independently_reviewed'


def test_fts_failure_remains_in_full_denominator():
    snapshot,dataset=inputs()
    class Broken:
        def execute(self,*args,**kwargs):raise ValueError('private internal error')
    report=run_retrieval_benchmark(Broken(),snapshot,dataset,as_of=NOW)
    arm=report['arms']['exact_fts']
    assert arm['errors']==4 and arm['coverage']=={'numerator':5,'denominator':5}
    assert arm['metrics']['recall_at_k']['denominator']==4
    assert arm['metrics']['empty_gold_correct']=={'numerator':0,'denominator':1}
    assert 'private internal error' not in str(report)


def test_unknown_gold_or_duplicate_case_is_rejected_before_sql():
    snapshot,dataset=inputs()
    class Forbidden:
        def execute(self,*args,**kwargs):pytest.fail('invalid labels reached SQL')
    bad=deepcopy(dataset);bad['cases'][0]['relevant_ids']=['CWE-999999']
    with pytest.raises(ValueError):run_retrieval_benchmark(Forbidden(),snapshot,bad,as_of=NOW)
    dataset['cases'].append(deepcopy(dataset['cases'][0]))
    with pytest.raises(ValueError):run_retrieval_benchmark(Forbidden(),snapshot,dataset,as_of=NOW)
