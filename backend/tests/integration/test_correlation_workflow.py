"""Analyst correlation over synthetic retained imports, with real PostgreSQL."""
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from reknyx.config import Settings
from reknyx.contracts import validate
from reknyx.infrastructure.auth import hash_password
from reknyx.infrastructure.models import FindingRecord, ObservationRecord, ReviewRecord
from reknyx.main import create_app
from reknyx.orchestration.import_worker import process_one

pytestmark=pytest.mark.skipif(not os.getenv('REKNYX_TEST_DATABASE_URL'),reason='isolated PostgreSQL required')


@pytest.fixture
def workspace(tmp_path):
    password=uuid4().hex
    settings=Settings(database_url=os.environ['REKNYX_TEST_DATABASE_URL'],artifact_root=tmp_path,
        username='correlation_'+uuid4().hex,password_hash=hash_password(password),actor_id=str(uuid4()),
        allowed_origins=('http://localhost:3000',))
    app=create_app(settings)
    with TestClient(app,client=('correlation_'+uuid4().hex,50000)) as c:
        login=c.post('/api/v1/auth/login',headers={'Origin':'http://localhost:3000'},json={'username':settings.username,'password':password})
        assert login.status_code==200,login.text
        headers={'Origin':'http://localhost:3000','X-CSRF-Token':login.json()['csrf_token']}
        def post(path,value,key=None):
            return c.post(path,headers={**headers,'Idempotency-Key':key or uuid4().hex},json=value)
        cases=json.loads(Path('contracts/examples/schema-cases.json').read_text())['cases']
        scope=next(case['payload'] for case in cases if case['id']=='valid-ScopeInput')
        def create():
            response=post('/api/v1/assessments',{'name':'Correlation fixture','request':'Synthetic evidence only','scope':scope})
            assert response.status_code==201,response.text
            return '/api/v1/assessments/'+response.json()['assessment']['id']
        path=create()
        alerts=[]
        for rule,risk,location in [('10','1','/login'),('10','3','/login'),('11','3','/login'),('10','3','/different')]:
            alerts.append({'pluginid':rule,'alert':'Same title cannot prove a duplicate','riskcode':risk,'confidence':'1',
                           'count':'1','solution':'Synthetic source remedy',
                           'instances':[{'uri':'http://192.0.2.10'+location,'method':'GET'}]})
        raw=json.dumps({'@programName':'ZAP','@version':'synthetic','site':[{'@name':'http://192.0.2.10','alerts':alerts}]}).encode()
        result=c.post(path+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},
            data={'kind':'zap_json','observed_at':'null','provenance':'synthetic_fixture','source_label':'Synthetic correlation fixture'},
            files={'file':('fixture.json',raw,'application/json')})
        assert result.status_code==202,result.text
        assert process_one(app.state.session_factory,app.state.artifact_store)
        imported=c.get(result.json()['status_url']).json()
        assert imported['state']=='succeeded'
        observation_ids=imported['observation_ids']
        findings=c.get(path+'/findings').json()['items']
        finding=next(f for f in findings if f['observation_ids']==[observation_ids[0]])
        yield app,c,path,post,headers,observation_ids,finding,create,raw


def test_link_is_attributed_conservative_replayable_and_frozen_in_snapshot(workspace):
    app,c,path,post,headers,ids,finding,_,raw=workspace
    assert post(path+'/findings/'+finding['id']+'/review',{'expected_revision':1,'disposition':'accepted',
        'rationale':'Original low source reviewed','evidence_ids':[ids[0]]}).status_code==201
    rev=c.get(path).json()['assessment']['state_revision']
    before=post(path+'/reports',{'expected_revision':rev,'include_suspected':True})
    assert before.status_code==202,before.text
    frozen=c.get(before.json()['status_url']+'/snapshot').json()
    key=uuid4().hex
    body={'finding_id':finding['id'],'observation_ids':[ids[1]],'decision':'link','expected_revision':2,
          'rationale':'Same capture, native rule and request location; severity conflict retained.'}
    result=post(path+'/correlations/review',body,key)
    assert result.status_code==201,result.text
    validate('ReviewRecord',result.json())
    assert result.json()['actor_id']==app.state.settings.actor_id
    assert result.json()['correlation_decision']=='link'
    assert post(path+'/correlations/review',body,key).json()==result.json()
    updated=c.get(path+'/findings/'+finding['id']).json()
    validate('Finding',updated)
    assert set(updated['observation_ids'])==set(ids[:2])
    assert updated['revision']==3 and updated['analyst_disposition']=='needs_review'
    assert updated['validation_status']=='suspected'
    assert updated['severity']=='high' and updated['priority']=='review_first'
    assert any('disagree' in unknown for unknown in updated['unknowns'])
    assert updated['confidence_value']==finding['confidence_value']
    assert updated['risk_input_sources'][0]['observation_ids']==[ids[1]]
    # Source findings and every raw membership stay accessible; no silent deduplication.
    assert len(c.get(path+'/findings').json()['items'])==4
    assert c.get(before.json()['status_url']+'/snapshot').json()==frozen
    rev=c.get(path).json()['assessment']['state_revision']
    after=post(path+'/reports',{'expected_revision':rev,'include_suspected':True})
    snapshot=c.get(after.json()['status_url']+'/snapshot').json()
    assert any(r['id']==result.json()['id'] for r in snapshot['reviews'])
    assert any('not deduplicated' in item for item in snapshot['limitations'])
    with app.state.session_factory() as db:
        assert len(list(db.scalars(select(ReviewRecord).where(ReviewRecord.assessment_id==finding['assessment_id']))))==2
        rows=list(db.scalars(select(ObservationRecord).where(ObservationRecord.assessment_id==finding['assessment_id'])))
        assert len(rows)==4
    for item in snapshot['artifacts']:
        assert c.get(item['download_url']).content==raw


@pytest.mark.parametrize('mode',['rule','location','stale','foreign','foreign_observation','mixed','keep_existing','separate','long_rationale'])
def test_correlation_denials_and_keep_separate(workspace,mode):
    app,c,path,post,headers,ids,finding,create,_=workspace
    target={'rule':ids[2],'location':ids[3]}.get(mode,ids[1])
    body={'finding_id':finding['id'],'observation_ids':[target],
          'decision':'keep_separate' if mode in ('separate','keep_existing') else 'link',
          'expected_revision':99 if mode=='stale' else 1,
          'rationale':'x'*2000 if mode=='long_rationale' else 'Synthetic analyst decision'}
    if mode=='mixed':body['observation_ids']=[ids[1],ids[2]]
    if mode=='keep_existing':body['observation_ids']=[ids[0]]
    if mode=='foreign_observation':
        foreign=create()
        result=c.post(foreign+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},
            data={'kind':'zap_json','observed_at':'null','provenance':'synthetic_fixture','source_label':'Foreign synthetic fixture'},
            files={'file':('fixture.json',workspace[-1],'application/json')})
        assert result.status_code==202,result.text
        assert process_one(app.state.session_factory,app.state.artifact_store)
        body['observation_ids']=c.get(result.json()['status_url']).json()['observation_ids'][:1]
    request_path=create() if mode=='foreign' else path
    key=uuid4().hex
    response=post(request_path+'/correlations/review',body,key)
    assert response.status_code==({'stale':409,'foreign':404,'foreign_observation':404,'separate':201,'long_rationale':201}.get(mode,422)),response.text
    assert post(request_path+'/correlations/review',body,key).json()==response.json()
    updated=c.get(path+'/findings/'+finding['id']).json()
    assert updated['observation_ids']==(ids[:2] if mode=='long_rationale' else [ids[0]])
    assert updated['revision']==(2 if mode in ('separate','long_rationale') else 1)
    if mode=='separate':
        assert response.json()['correlation_decision']=='keep_separate'
        assert updated['severity']=='low' and updated['analyst_disposition']=='needs_review'


def test_link_preserves_explicit_cvss_attribution_for_older_imported_findings(workspace):
    app,c,path,post,headers,_,_,_,_=workspace
    raw=(Path('backend/tests/fixtures/greenbone/synthetic-report.xml')).read_bytes()
    ids=[]
    for index in range(2):
        result=c.post(path+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},
            data={'kind':'greenbone_xml','observed_at':'2026-11-08T00:00:00Z','provenance':'synthetic_fixture','source_label':'Synthetic Greenbone fixture'},
            files={'file':('fixture.xml',raw+b'\n'*index,'application/xml')})
        assert result.status_code==202,result.text
        assert process_one(app.state.session_factory,app.state.artifact_store)
        status=c.get(result.json()['status_url']).json()
        assert status['state']=='succeeded'
        ids+=status['observation_ids']
    finding=next(f for f in c.get(path+'/findings').json()['items'] if f['observation_ids']==ids[:1])
    # Simulate a pre-attribution finding without modifying immutable native evidence.
    with app.state.session_factory() as db:
        record=db.get(FindingRecord,finding['id'])
        record.data={**record.data,'risk_input_sources':[]}
        db.commit()
    result=post(path+'/correlations/review',{'finding_id':finding['id'],'observation_ids':ids[1:],
        'decision':'link','expected_revision':1,'rationale':'Distinct capture bytes with the same recorded time and native rule.'})
    assert result.status_code==201,result.text
    linked=c.get(path+'/findings/'+finding['id']).json()
    assert linked['cvss']==finding['cvss']==7.5
    assert linked['cvss_vector']==finding['cvss_vector']
    assert linked['cvss_source']==finding['cvss_source']
    cvss=next(entry for entry in linked['risk_input_sources'] if entry['field']=='cvss')
    assert cvss['observation_ids']==ids[:1]
