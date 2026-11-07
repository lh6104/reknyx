"""Actual PostgreSQL import/review checks with synthetic source bytes."""
import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from reknyx.config import Settings
from reknyx.contracts import validate
from reknyx.infrastructure.auth import hash_password
from reknyx.main import create_app
from reknyx.orchestration.import_worker import process_one

URL = os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='isolated PostgreSQL URL not supplied')


@pytest.mark.parametrize('kind', ['zap_json', 'nmap_xml', 'greenbone_xml', 'malformed'])
def test_real_import_review_and_raw_trace(tmp_path, kind):
    from reknyx.infrastructure.models import ObservationRecord, FindingRecord
    password = uuid4().hex
    settings = Settings(database_url=URL, artifact_root=tmp_path,
                        username='import_' + uuid4().hex, password_hash=hash_password(password),
                        actor_id=str(uuid4()), allowed_origins=('http://localhost:3000',))
    app = create_app(settings)
    with TestClient(app) as client:
        session = client.post('/api/v1/auth/login', headers={'Origin': 'http://localhost:3000'},
                              json={'username': settings.username, 'password': password})
        assert session.status_code == 200, session.text
        headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'],
                   'Idempotency-Key': uuid4().hex}
        cases = json.loads((Path(__file__).resolve().parents[3] / 'contracts/examples/schema-cases.json').read_text())['cases']
        scope = next(c['payload'] for c in cases if c['id'] == 'valid-ScopeInput')
        created = client.post('/api/v1/assessments', headers=headers,
                              json={'name': 'Import acceptance fixture', 'request': 'Review synthetic source', 'scope': scope})
        assert created.status_code == 201, created.text
        assessment_id = created.json()['assessment']['id']
        path = '/api/v1/assessments/' + assessment_id
        raw = json.dumps({'@programName': 'ZAP', '@version': 'synthetic', 'site': [
            {'@name': 'https://lab.example', 'alerts': [{'pluginid': '1', 'alert': '<script>Synthetic alert</script>',
                'riskcode': '3', 'confidence': '2', 'count': '1', 'solution': 'Review configuration',
                'instances': [{'uri': 'https://lab.example/login', 'method': 'GET'}]}]}]}).encode()
        if kind == 'nmap_xml':
            raw = b'<nmaprun scanner="nmap" version="synthetic"><host><address addrtype="ipv4" addr="192.0.2.1"/><ports><port protocol="tcp" portid="80"><state state="open"/></port></ports></host><runstats><finished exit="success"/></runstats></nmaprun>'
        elif kind == 'greenbone_xml':
            raw = (Path(__file__).parents[1] / 'fixtures/greenbone/synthetic-report.xml').read_bytes()
        elif kind == 'malformed':
            raw = b'{"invalid":true}'
        content_type = 'application/xml' if kind in ('nmap_xml','greenbone_xml') else 'application/json'
        metadata = {'kind': kind if kind in ('nmap_xml','greenbone_xml') else 'zap_json', 'observed_at': 'null', 'provenance': 'synthetic_fixture', 'source_label': 'Synthetic source shape'}
        headers['Idempotency-Key'] = uuid4().hex
        result = client.post(path + '/imports', headers=headers, data=metadata,
                             files={'file': ('fixture', raw, content_type)})
        assert result.status_code == 202, result.text
        replay = client.post(path + '/imports', headers=headers, data=metadata,
                             files={'file': ('renamed', raw, content_type)})
        assert replay.status_code == 202 and replay.json() == result.json()
        assert process_one(app.state.session_factory, app.state.artifact_store)
        status = client.get(result.json()['status_url'])
        assert status.status_code == 200, status.text
        validate('Import', status.json())
        assert status.json()['state'] == ('failed' if kind == 'malformed' else 'succeeded'), status.text
        artifact_id = status.json()['artifact_id']
        assert client.get(path + '/artifacts/' + artifact_id + '/download').content == raw
        with app.state.session_factory() as db:
            observations = list(db.scalars(select(ObservationRecord).where(ObservationRecord.assessment_id == assessment_id)))
            findings = list(db.scalars(select(FindingRecord).where(FindingRecord.assessment_id == assessment_id)))
            if kind == 'malformed':
                assert observations == findings == []
                return
            if kind == 'nmap_xml':
                assert len(observations) == 1 and findings == []
                assert observations[0].data['kind'] == 'service'
                return
            assert len(observations) == len(findings) == 1
            observation, finding = observations[0].data, findings[0].data
        if kind == 'greenbone_xml':
            assert observation['source_tool'] == 'greenbone'
            assert finding['cvss'] == 7.5
        assert finding['validation_status'] == 'suspected'
        assert finding['priority'] == 'review_first'
        assert finding['observation_ids'] == [observation['id']]
        artifact_id = observation['artifact_id']
        assert client.get(path + '/artifacts/' + artifact_id + '/download').content == raw
        review = {'expected_revision': 1, 'disposition': 'accepted', 'rationale': 'Synthetic review', 'evidence_ids': [observation['id']]}
        headers['Idempotency-Key'] = uuid4().hex
        reviewed = client.post(path + '/findings/' + finding['id'] + '/review', headers=headers, json=review)
        assert reviewed.status_code == 201, reviewed.text
        validate('ReviewRecord', reviewed.json())
        headers['Idempotency-Key'] = uuid4().hex
        assert client.post(path + '/findings/' + finding['id'] + '/review', headers=headers, json=review).status_code == 409
