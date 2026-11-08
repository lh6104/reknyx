"""Local PostgreSQL analysis checks; fake Groq transport, no external calls."""
import json
import os
from pathlib import Path
from uuid import uuid4
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,text
from sqlalchemy.exc import DBAPIError

from reknyx.config import Settings
from reknyx.infrastructure.auth import hash_password
from reknyx.infrastructure.models import AnalysisAttempt,AnalysisDecision
from reknyx.main import create_app
from reknyx.orchestration.import_worker import process_one
from reknyx.security_analysis.evidence_analysis import local_review
from reknyx.security_analysis.model_providers import groq

URL=os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark=pytest.mark.skipif(not URL,reason='dedicated analysis PostgreSQL not configured')

@pytest.fixture
def workspace(tmp_path):
    password=uuid4().hex
    settings=Settings(database_url=URL,artifact_root=tmp_path,username='analysis_'+uuid4().hex,
       password_hash=hash_password(password),actor_id=str(uuid4()),allowed_origins=('http://localhost:3000',))
    app=create_app(settings)
    with TestClient(app,client=('analysis_'+uuid4().hex,50000)) as client:
        login=client.post('/api/v1/auth/login',headers={'Origin':'http://localhost:3000'},json={'username':settings.username,'password':password})
        assert login.status_code==200,login.text
        headers={'Origin':'http://localhost:3000','X-CSRF-Token':login.json()['csrf_token']}
        cases=json.loads(Path('contracts/examples/schema-cases.json').read_text())['cases']
        scope=next(c['payload'] for c in cases if c['id']=='valid-ScopeInput')
        scope=json.loads(json.dumps(scope))
        scope['budget'].update(max_model_calls=1,max_input_tokens=20000,max_output_tokens=1024)
        def post(path,body,key=None):return client.post(path,json=body,headers={**headers,'Idempotency-Key':key or uuid4().hex})
        created=post('/api/v1/assessments',{'name':'Analysis fixture','request':'Synthetic review only','scope':scope})
        assert created.status_code==201,created.text
        path='/api/v1/assessments/'+created.json()['assessment']['id']
        yield app,client,path,post,headers

def upload(workspace,provenance='synthetic_fixture'):
    app,client,path,post,headers=workspace
    raw=b'<nmaprun scanner="nmap" version="synthetic"><host><address addr="192.0.2.10" addrtype="ipv4"/><ports><port protocol="tcp" portid="80"><state state="open"/></port></ports></host><runstats><finished exit="success"/></runstats></nmaprun>'
    response=client.post(path+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},data={'kind':'nmap_xml','observed_at':'null','provenance':provenance,'source_label':'Synthetic analysis fixture'},files={'file':('fixture.xml',raw,'application/xml')})
    assert response.status_code==202,response.text
    assert process_one(app.state.session_factory,app.state.artifact_store)

def test_local_review_is_explicit_replayable_and_immutable(workspace):
    app,c,path,post,_=workspace
    appended=post(path+'/messages',{'expected_revision':1,'content':'Do not infer on append'})
    assert appended.status_code==201
    assert c.get(path+'/decisions').json()['items']==[]
    key=uuid4().hex
    payload={'expected_revision':2,'retry':None}
    response=post(path+'/plans',payload,key)
    assert response.status_code==200,response.text
    decision=response.json()['decision']
    assert decision['source']=='deterministic' and decision['proposal_id'] is None
    assert response.json()['proposal'] is None
    assert post(path+'/plans',payload,key).json()==response.json()
    assert post(path+'/plans',{'expected_revision':3,'retry':None},key).status_code==409
    assert c.get(path+'/actions').json()['items']==[]
    assert len(c.get(path+'/decisions').json()['items'])==1
    assert c.get(path+'/messages').json()['items'][-1]['source']=='deterministic'
    with app.state.session_factory() as db:
        with pytest.raises(DBAPIError):db.execute(text('UPDATE analysis_decisions SET data=data WHERE id=:id'),{'id':decision['id']})

def test_provider_failure_is_recorded_and_never_silently_retried(workspace,monkeypatch):
    app,c,path,post,_=workspace
    app.state.settings=replace(app.state.settings,analysis_provider='groq')
    calls=[]
    monkeypatch.setattr(groq,'review',lambda *args:calls.append(1))
    key=uuid4().hex
    payload={'expected_revision':1,'retry':None}
    response=post(path+'/plans',payload,key)
    assert response.status_code==503,response.text
    app.state.settings=replace(app.state.settings,analysis_provider='deterministic')
    assert post(path+'/plans',payload,key).json()==response.json()
    assert calls==[]
    d=c.get(path+'/decisions').json()['items'][0]
    assert d['source']=='llm' and d['failure_code']=='provider_not_configured'
    assert not any('selected review topics' in item for item in d['limitations'])
    assert c.get(path+'/messages').json()['items']==[]

@pytest.mark.parametrize('mode',['valid','foreign','stale','uncovered','overrun'])
def test_provider_output_freshness_ownership_and_budget(workspace,monkeypatch,mode):
    app,c,path,post,_=workspace
    upload(workspace,'public_format_reference' if mode=='uncovered' else 'synthetic_fixture')
    app.state.settings=replace(app.state.settings,analysis_provider='groq',groq_api_key='fixture-only',groq_synthetic_enabled=True,groq_free_plan_confirmed=True)
    calls=[]
    def fake(context,_api_key,options=None):
        calls.append(context)
        with app.state.engine.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction'"))==0
        if mode=='stale':
            rev=c.get(path).json()['assessment']['state_revision']
            assert post(path+'/messages',{'expected_revision':rev,'content':'Concurrent edit'}).status_code==201
        if mode=='valid':
            duplicate=post(path+'/plans',payload,key)
            assert duplicate.status_code==409 and duplicate.json()['error']['code']=='operation_in_progress'
            assert duplicate.json()['error']['details'][0]['resource_id']
        output=local_review(context)
        if mode=='foreign':output['basis_observation_ids']=[str(uuid4())]
        return {'http_status':200,'value':output,'usage':{'prompt_tokens':30000 if mode=='overrun' else 100,'completion_tokens':30},'request_id':'fake-groq'}
    monkeypatch.setattr(groq,'review',fake)
    rev=c.get(path).json()['assessment']['state_revision']
    payload={'expected_revision':rev,'retry':None}
    key=uuid4().hex
    response=post(path+'/plans',payload,key)
    assert response.status_code==({'valid':200,'foreign':503,'stale':409,'uncovered':503,'overrun':503}[mode]),response.text
    assert len(calls)==(0 if mode=='uncovered' else 1)
    assert post(path+'/plans',payload,key).json()==response.json()
    if mode=='valid':
        decision=response.json()['decision']
        assert decision['source']=='llm' and decision['budget_remaining']['max_model_calls']==0
        rev=c.get(path).json()['assessment']['state_revision']
        exhausted=post(path+'/plans',{'expected_revision':rev,'retry':None})
        assert exhausted.status_code==503 and 'model_budget_exhausted' in exhausted.text
        assert len(calls)==1
    else:
        assert c.get(path+'/decisions').json()['items'][0]['outcome']=='failed'
        if mode=='overrun':
            with app.state.session_factory() as db:
                attempt=db.scalar(select(AnalysisAttempt).where(AnalysisAttempt.assessment_id==path.rsplit('/',1)[1]))
                assert attempt.data['provider_http_status']==200


def test_foreign_assessment_and_retry_do_not_expose_records(workspace):
    app,c,path,post,_=workspace
    assert post('/api/v1/assessments/'+str(uuid4())+'/plans',{'expected_revision':1,'retry':None}).status_code==404
    assert post(path+'/plans',{'expected_revision':1,'retry':{'kind':'decision','prior_id':str(uuid4()),'reason':'Synthetic retry'}}).status_code==404


def test_groq_key_does_not_imply_free_plan_or_data_use_authorization(workspace,monkeypatch):
    app,c,path,post,_=workspace
    upload(workspace)
    app.state.settings=replace(app.state.settings,analysis_provider='groq',groq_api_key='fixture-only',groq_synthetic_enabled=True)
    calls=[]
    monkeypatch.setattr(groq,'review',lambda *args:calls.append(1))
    rev=c.get(path).json()['assessment']['state_revision']
    response=post(path+'/plans',{'expected_revision':rev,'retry':None})
    assert response.status_code==503 and 'provider_free_plan_not_confirmed' in response.text
    assert calls==[]


@pytest.mark.skipif(not os.getenv('REKNYX_TEST_ADMIN_DATABASE_URL'),reason='isolated admin URL required for revocation fixture')
def test_membership_revoked_during_inference_records_failure_without_publishing(workspace,monkeypatch):
    from sqlalchemy import create_engine,delete
    from reknyx.infrastructure.models import Membership,Message
    app,c,path,post,_=workspace
    upload(workspace)
    app.state.settings=replace(app.state.settings,analysis_provider='groq',groq_api_key='fixture-only',groq_synthetic_enabled=True,groq_free_plan_confirmed=True)
    assessment_id=path.rsplit('/',1)[1]
    def fake(context,key,options=None):
        engine=create_engine(os.environ['REKNYX_TEST_ADMIN_DATABASE_URL'])
        try:
            with engine.begin() as conn:conn.execute(delete(Membership).where(Membership.assessment_id==assessment_id))
        finally:engine.dispose()
        return {'value':local_review(context),'usage':None,'request_id':'revoked-fixture'}
    monkeypatch.setattr(groq,'review',fake)
    rev=c.get(path).json()['assessment']['state_revision']
    response=post(path+'/plans',{'expected_revision':rev,'retry':None})
    assert response.status_code==404,response.text
    with app.state.session_factory() as db:
        decision=db.scalar(select(AnalysisDecision).where(AnalysisDecision.assessment_id==assessment_id))
        assert decision.data['failure_code']=='assessment_access_revoked'
        assert db.scalar(select(AnalysisAttempt).where(AnalysisAttempt.assessment_id==assessment_id)).data['state']=='failed'
        assert list(db.scalars(select(Message).where(Message.assessment_id==assessment_id)))==[]


def test_context_v2_bounds_normalized_facts_and_excludes_imported_addresses(workspace):
    from reknyx.infrastructure.models import Assessment
    from reknyx.security_analysis.evidence_context import build_context
    app,c,path,post,headers=workspace
    hosts=''.join(f'<host><address addr="192.0.2.{i+1}" addrtype="ipv4"/><ports><port protocol="tcp" portid="443"><state state="open"/><service product="Private banner must not leave context"/></port></ports></host>' for i in range(34))
    raw=('<nmaprun scanner="nmap" version="synthetic">'+hosts+'<runstats><finished exit="success"/></runstats></nmaprun>').encode()
    result=c.post(path+'/imports',headers={**headers,'Idempotency-Key':uuid4().hex},data={'kind':'nmap_xml','observed_at':'null','provenance':'synthetic_fixture','source_label':'Private source label'},files={'file':('fixture.xml',raw,'application/xml')})
    assert result.status_code==202,result.text
    assert process_one(app.state.session_factory,app.state.artifact_store)
    with app.state.session_factory() as db:
        context=build_context(db,db.get(Assessment,path.rsplit('/',1)[1]))
    assert len(context['observations'])==32 and context['truncated']
    assert context['version']=='bounded-observations-v2'
    assert context['observations'][0]['facts']=={'severity':'unknown','transport':'tcp','port':443,'historical':True}
    assert '192.0.2.' not in json.dumps(context) and 'Private' not in json.dumps(context)
