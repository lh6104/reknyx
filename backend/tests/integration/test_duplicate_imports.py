"""Repeat-import identity with real PostgreSQL and retained synthetic bytes."""
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from test_correlation_workflow import workspace
from reknyx.infrastructure.models import AuditEvent, FindingCaptureKey, FindingRecord, ObservationRecord
from reknyx.orchestration.import_worker import process_one

pytestmark=pytest.mark.skipif(not os.getenv('REKNYX_TEST_DATABASE_URL'),reason='isolated PostgreSQL required')


def repeat(workspace, *, path=None, raw=None, observed_at='null', provenance='synthetic_fixture'):
    app,c,original_path,_,headers,_,_,_,original_raw=workspace
    path=path or original_path
    response=c.post(path+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},
        data={'kind':'zap_json','observed_at':observed_at,'provenance':provenance,'source_label':'Repeated synthetic capture'},
        files={'file':('repeat.json',raw if raw is not None else original_raw,'application/json')})
    assert response.status_code==202,response.text
    assert process_one(app.state.session_factory,app.state.artifact_store)
    return c.get(response.json()['status_url']).json()


def test_duplicate_retains_sources_review_and_snapshot_but_not_another_finding(workspace):
    app,c,path,post,_,ids,finding,_,raw=workspace
    review=post(path+'/findings/'+finding['id']+'/review',{'expected_revision':1,'disposition':'accepted',
        'rationale':'Original capture reviewed','evidence_ids':[ids[0]]})
    assert review.status_code==201,review.text
    rev=c.get(path).json()['assessment']['state_revision']
    report=post(path+'/reports',{'expected_revision':rev,'include_suspected':True})
    frozen=c.get(report.json()['status_url']+'/snapshot').json()
    imported=repeat(workspace)
    assert imported['state']=='succeeded'
    findings=c.get(path+'/findings').json()['items']
    assert len(findings)==4
    updated=c.get(path+'/findings/'+finding['id']).json()
    assert updated['revision']==3 and updated['analyst_disposition']=='accepted'
    assert updated['validation_status']==finding['validation_status']=='suspected'
    assert updated['severity']==finding['severity'] and updated['cvss']==finding['cvss']
    assert updated['observation_ids']==[ids[0],imported['observation_ids'][0]]
    assert c.get(report.json()['status_url']+'/snapshot').json()==frozen
    rev=c.get(path).json()['assessment']['state_revision']
    after=post(path+'/reports',{'expected_revision':rev,'include_suspected':True})
    snapshot=c.get(after.json()['status_url']+'/snapshot').json()
    assert len(snapshot['findings'])==4 and len(snapshot['observations'])==8
    assert any('Exact-capture' in item for item in snapshot['limitations'])
    assert len(snapshot['artifacts'])==2
    assert all(c.get(artifact['download_url']).content==raw for artifact in snapshot['artifacts'])
    assert any(record['id']==review.json()['id'] for record in snapshot['reviews'])
    with app.state.session_factory() as db:
        keys=list(db.scalars(select(FindingCaptureKey).where(FindingCaptureKey.assessment_id==finding['assessment_id'])))
        assert len(keys)==4
        assert len(list(db.scalars(select(ObservationRecord).where(ObservationRecord.assessment_id==finding['assessment_id']))))==8


@pytest.mark.parametrize('mode',['bytes','time','provenance','assessment'])
def test_distinct_capture_or_context_remains_separate(workspace,mode):
    app,c,path,post,_,_,finding,create,raw=workspace
    target=create() if mode=='assessment' else path
    imported=repeat(workspace,path=target,raw=raw+b'\n' if mode=='bytes' else raw,
        observed_at='2026-11-08T00:00:00Z' if mode=='time' else 'null',
        provenance='public_format_reference' if mode=='provenance' else 'synthetic_fixture')
    assert imported['state']=='succeeded'
    assert len(c.get(path+'/findings').json()['items'])==(4 if mode=='assessment' else 8)
    if mode=='assessment':assert len(c.get(target+'/findings').json()['items'])==4
    assert c.get(path+'/findings/'+finding['id']).json()['revision']==1


def test_keep_separate_review_prevents_automatic_attachment(workspace):
    app,c,path,post,_,ids,finding,_,_=workspace
    result=post(path+'/correlations/review',{'finding_id':finding['id'],'observation_ids':[ids[1]],
        'decision':'keep_separate','expected_revision':1,'rationale':'Require manual decisions on this finding.'})
    assert result.status_code==201,result.text
    imported=repeat(workspace)
    assert imported['state']=='succeeded'
    original=c.get(path+'/findings/'+finding['id']).json()
    assert original['revision']==2 and original['observation_ids']==ids[:1]
    assert len(c.get(path+'/findings').json()['items'])==5


def test_index_is_immutable_and_rejects_foreign_assessment_binding(workspace):
    app,c,path,post,_,_,finding,create,_=workspace
    other=create().rsplit('/',1)[-1]
    with app.state.session_factory() as db:
        key=db.scalar(select(FindingCaptureKey).where(FindingCaptureKey.finding_id==finding['id']))
        assert key is not None
        for sql in ['UPDATE finding_capture_keys SET fingerprint=fingerprint WHERE finding_id=:id',
                    'DELETE FROM finding_capture_keys WHERE finding_id=:id',
                    'TRUNCATE finding_capture_keys']:
            with pytest.raises(DBAPIError),db.begin_nested():db.execute(text(sql),{'id':finding['id']})
        with pytest.raises(DBAPIError),db.begin_nested():
            db.add(FindingCaptureKey(assessment_id=other,fingerprint='f'*64,finding_id=finding['id'],created_at=key.created_at))
            db.flush()


def test_bounded_duplicate_failure_publishes_no_partial_observations_or_findings(workspace):
    app,c,path,post,_,ids,finding,_,_=workspace
    # Fail on the third instance, after earlier updates have been staged in the savepoint.
    finding=next(f for f in c.get(path+'/findings').json()['items'] if f['observation_ids']==[ids[2]])
    with app.state.session_factory() as db:
        row=db.get(FindingRecord,finding['id'])
        row.data={**row.data,'correlation_reason':'x'*2000}
        db.commit()
    imported=repeat(workspace)
    assert imported['state']=='failed' and imported['failure_code']=='finding_trace_limit'
    assert imported['observation_ids']==[]
    assert c.get(path+'/findings/'+finding['id']).json()['revision']==1
    findings=c.get(path+'/findings').json()['items']
    assert len(findings)==4
    assert all(row['revision']==1 and len(row['observation_ids'])==1 for row in findings)
    with app.state.session_factory() as db:
        assert len(list(db.scalars(select(ObservationRecord).where(ObservationRecord.assessment_id==finding['assessment_id']))))==4
        assert list(db.scalars(select(AuditEvent).where(AuditEvent.assessment_id==finding['assessment_id'],
            AuditEvent.data['kind'].astext=='finding.duplicate_linked')))==[]
    assert c.get(path+'/artifacts/'+imported['artifact_id']+'/download').status_code==200


def test_two_worker_publications_serialize_the_same_capture(workspace):
    app,c,path,post,headers,_,finding,_,raw=workspace
    jobs=[]
    for _ in range(2):
        result=c.post(path+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},
            data={'kind':'zap_json','observed_at':'null','provenance':'synthetic_fixture','source_label':'Concurrent synthetic capture'},
            files={'file':('repeat.json',raw,'application/json')})
        assert result.status_code==202,result.text
        jobs.append(result.json()['status_url'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(process_one,app.state.session_factory,app.state.artifact_store) for _ in jobs]
        assert all(future.result() for future in futures)
    assert all(c.get(path).json()['state']=='succeeded' for path in jobs)
    assert len(c.get(path+'/findings').json()['items'])==4
    updated=c.get(path+'/findings/'+finding['id']).json()
    assert len(updated['observation_ids'])==3 and updated['revision']==3
