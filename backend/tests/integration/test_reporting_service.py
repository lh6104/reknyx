"""Real PostgreSQL/API/import/PDF pipeline with labelled synthetic bytes."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from reknyx.config import Settings
from reknyx.contracts import validate
from reknyx.infrastructure.auth import hash_password
from reknyx.main import create_app
from reknyx.orchestration.import_worker import process_one as import_one
from reknyx.reporting.service import process_one as report_one

URL = os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='isolated PostgreSQL URL not supplied')


@pytest.mark.parametrize('unsupported_glyph,publication_failure', [(False, False), (True, False), (False, True)])
def test_frozen_report_survives_review_changes_and_restart(tmp_path, monkeypatch, unsupported_glyph, publication_failure):
    password = uuid4().hex
    settings = Settings(database_url=URL, artifact_root=tmp_path, username='report_' + uuid4().hex,
                        password_hash=hash_password(password), actor_id=str(uuid4()),
                        allowed_origins=('http://localhost:3000',))
    app = create_app(settings)
    with TestClient(app, client=('report_' + uuid4().hex, 50000)) as client:
        session = client.post('/api/v1/auth/login', headers={'Origin': 'http://localhost:3000'},
                              json={'username': settings.username, 'password': password})
        assert session.status_code == 200, session.text
        headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token']}
        def post(path, value):
            return client.post(path, headers={**headers, 'Idempotency-Key': uuid4().hex}, json=value)
        cases = json.loads((Path(__file__).resolve().parents[3] / 'contracts/examples/schema-cases.json').read_text())['cases']
        scope = next(c['payload'] for c in cases if c['id'] == 'valid-ScopeInput')
        created = post('/api/v1/assessments', {'name': 'Report fixture', 'request': 'Review synthetic import', 'scope': scope})
        assert created.status_code == 201, created.text
        path = '/api/v1/assessments/' + created.json()['assessment']['id']
        raw = json.dumps({'@programName': 'ZAP', '@version': 'synthetic', 'site': [
            {'@name': 'https://lab.example', 'alerts': [{'pluginid': '1', 'alert': '<b>Synthetic alert</b>' + ('\U0001f680' if unsupported_glyph else ''),
                'riskcode': '3', 'confidence': '2', 'count': '1', 'solution': 'Review configuration',
                'instances': [{'uri': 'https://lab.example/login', 'method': 'GET'}]}]}]}).encode()
        imported = client.post(path + '/imports', headers={**headers, 'Idempotency-Key': uuid4().hex},
                               data={'kind': 'zap_json', 'observed_at': 'null', 'provenance': 'synthetic_fixture', 'source_label': 'Synthetic report fixture'},
                               files={'file': ('fixture.json', raw, 'application/json')})
        assert imported.status_code == 202, imported.text
        assert import_one(app.state.session_factory, app.state.artifact_store)
        finding = client.get(path + '/findings').json()['items'][0]
        assert post(path + '/findings/' + finding['id'] + '/review', {'expected_revision': finding['revision'],
                    'disposition': 'accepted', 'rationale': 'Synthetic fixture review', 'evidence_ids': finding['observation_ids']}).status_code == 201
        revision = client.get(path).json()['assessment']['state_revision']
        payload = {'expected_revision': revision, 'include_suspected': True}
        report_headers = {**headers, 'Idempotency-Key': uuid4().hex}
        queued = client.post(path + '/reports', headers=report_headers, json=payload)
        assert queued.status_code == 202, queued.text
        assert client.post(path + '/reports', headers=report_headers, json=payload).json() == queued.json()
        report_path = queued.json()['status_url']
        assert client.get(report_path + '/download').status_code == 409
        frozen = client.get(report_path + '/snapshot')
        assert frozen.status_code == 200, frozen.text
        validate('ReportSnapshot', frozen.json())
        assert frozen.json()['counts']['accepted_findings'] == 1
        assert 'zap_traditional_json_v1.0' in frozen.json()['tool_summary'][0]
        assert 'synthetic_fixture' in frozen.json()['tool_summary'][0]
        if publication_failure:
            def disk_full(_content):
                raise OSError('Injected disk failure after genuine import and rendering')
            monkeypatch.setattr(app.state.artifact_store, 'put', disk_full)
        assert report_one(app.state.session_factory, app.state.artifact_store,
                          assessment_id=created.json()['assessment']['id'])
        ready = client.get(report_path)
        worker_events = [row for row in client.get(path + '/timeline').json()['items']
                         if row['kind'] in ('report.ready', 'report.failed')]
        assert worker_events and all(row['actor_type'] == 'worker' and row['actor_id'] is None for row in worker_events)
        if unsupported_glyph or publication_failure:
            assert ready.json()['state'] == 'failed', ready.text
            assert ready.json()['failure_code'] == ('publication_failed' if publication_failure else 'render_failed')
            assert ready.json()['artifact_id'] is None
            assert client.get(report_path + '/snapshot').json() == frozen.json()
            assert client.get(report_path + '/download').status_code == 409
            return
        assert ready.json()['state'] == 'ready', ready.text
        artifact_events = [row for row in client.get(path + '/timeline').json()['items']
                           if row['kind'] == 'artifact.stored' and row['resource_id'] == ready.json()['artifact_id']]
        assert len(artifact_events) == 1
        assert artifact_events[0]['actor_type'] == 'worker' and artifact_events[0]['actor_id'] is None
        pdf = client.get(report_path + '/download')
        assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF-'), pdf.text[:200]
        report_text = subprocess.check_output(['pdftotext', '-', '-'], input=pdf.content).decode()
        assert 'zap_traditional_json_v1.0' in report_text
        assert 'Synthetic report fixture' in report_text
        assert 'synthetic_fixture' in report_text
        digest = hashlib.sha256(pdf.content).hexdigest()
        updated_finding = client.get(path + '/findings').json()['items'][0]
        assert post(path + '/findings/' + finding['id'] + '/review', {'expected_revision': updated_finding['revision'],
                    'disposition': 'rejected', 'rationale': 'Later synthetic disposition', 'evidence_ids': finding['observation_ids']}).status_code == 201
        assert post(path + '/reports', payload).status_code == 409
        assert client.get(report_path + '/snapshot').json() == frozen.json()
        cookies = dict(client.cookies)
    foreign_settings = Settings(database_url=URL, artifact_root=tmp_path, username='foreign_' + uuid4().hex,
                        password_hash=hash_password(password), actor_id=str(uuid4()),
                        allowed_origins=('http://localhost:3000',))
    with TestClient(create_app(foreign_settings), client=('foreign_' + uuid4().hex, 50000)) as foreign:
        assert foreign.post('/api/v1/auth/login', headers={'Origin': 'http://localhost:3000'},
                    json={'username': foreign_settings.username, 'password': password}).status_code == 200
        assert foreign.get(report_path + '/snapshot').status_code == 404
        assert foreign.get(report_path + '/download').status_code == 404
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get(report_path + '/download').status_code == 401
        restarted.cookies.update(cookies)
        assert hashlib.sha256(restarted.get(report_path + '/download').content).hexdigest() == digest
