"""Actual HTTP authorization, replay, filtering and foreign-evidence checks."""
import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from reknyx.config import Settings
from reknyx.contracts import validate
from reknyx.infrastructure.auth import hash_password
from reknyx.main import create_app
from reknyx.orchestration.import_worker import process_one

URL = os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='isolated PostgreSQL URL not supplied')


def test_import_http_boundaries(tmp_path):
    password = uuid4().hex
    settings = Settings(database_url=URL, artifact_root=tmp_path, username='boundaries_' + uuid4().hex,
                        password_hash=hash_password(password), actor_id=str(uuid4()),
                        allowed_origins=('http://localhost:3000',))
    app = create_app(settings)
    cases = json.loads((Path(__file__).resolve().parents[3] / 'contracts/examples/schema-cases.json').read_text())['cases']
    scope = next(c['payload'] for c in cases if c['id'] == 'valid-ScopeInput')
    def assessment(client, headers):
        headers['Idempotency-Key'] = uuid4().hex
        response = client.post('/api/v1/assessments', headers=headers, json={'name': 'Boundaries fixture', 'request': 'Synthetic import review', 'scope': scope})
        assert response.status_code == 201, response.text
        return '/api/v1/assessments/' + response.json()['assessment']['id']

    with TestClient(app, client=('boundary-' + uuid4().hex, 50000)) as client:
        login = client.post('/api/v1/auth/login', headers={'Origin': 'http://localhost:3000'}, json={'username': settings.username, 'password': password})
        assert login.status_code == 200, login.text
        headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': login.json()['csrf_token'], 'Idempotency-Key': uuid4().hex}
        path, second_path = assessment(client, headers), assessment(client, headers)
        raw = json.dumps({'@programName': 'ZAP', '@version': 'synthetic', 'site': [
            {'@name': 'https://lab.example', 'alerts': [
                {'pluginid': str(i), 'alert': title, 'riskcode': risk, 'confidence': '2', 'count': '1',
                 'instances': [{'uri': 'https://lab.example/' + str(i), 'method': 'GET'}]}
                for i, title, risk in [(1, 'Needle configuration', '3'), (2, 'Other source alert', '1')]]}]}).encode()
        metadata = {'kind': 'zap_json', 'observed_at': 'null', 'provenance': 'synthetic_fixture', 'source_label': 'Synthetic boundaries fixture'}
        for content, media, expected in [(b'', 'application/json', 422), (raw, 'application/pdf', 415), (raw, 'text/plain', 415)]:
            headers['Idempotency-Key'] = uuid4().hex
            rejected = client.post(path + '/imports', headers=headers, data=metadata, files={'file': ('fixture', content, media)})
            assert rejected.status_code == expected, rejected.text
        headers['Idempotency-Key'] = uuid4().hex
        accepted = client.post(path + '/imports', headers=headers, data=metadata, files={'file': ('fixture.json', raw, 'application/json')})
        assert accepted.status_code == 202, accepted.text
        conflict = client.post(path + '/imports', headers=headers, data=metadata, files={'file': ('fixture.json', raw + b' ', 'application/json')})
        assert conflict.status_code == 409, conflict.text
        assert process_one(app.state.session_factory, app.state.artifact_store)
        status = client.get(accepted.json()['status_url']).json()
        assert status['state'] == 'succeeded'
        findings_response = client.get(path + '/findings')
        assert findings_response.status_code == 200, findings_response.text
        findings = findings_response.json()['items']
        assert len(findings) == 2
        high = next(f for f in findings if f['severity'] == 'high')
        low = next(f for f in findings if f['severity'] == 'low')
        for filters in ['severity=high', 'priority=review_first', 'search=Needle', 'severity=high&priority=review_first&search=Needle']:
            response = client.get(path + '/findings?' + filters)
            assert response.status_code == 200, response.text
            assert [f['id'] for f in response.json()['items']] == [high['id']], filters
        assert client.get(path + '/findings?search=missing').json()['items'] == []
        assert client.get(path + '/findings?search=%25').json()['items'] == []
        review = {'expected_revision': 1, 'disposition': 'accepted', 'rationale': 'Synthetic analyst decision', 'evidence_ids': high['observation_ids']}
        headers['Idempotency-Key'] = uuid4().hex
        reviewed = client.post(path + '/findings/' + high['id'] + '/review', headers=headers, json=review)
        assert reviewed.status_code == 201, reviewed.text
        assert client.post(path + '/findings/' + high['id'] + '/review', headers=headers, json=review).json() == reviewed.json()
        filtered = client.get(path + '/findings?disposition=accepted')
        assert filtered.status_code == 200, filtered.text
        assert [f['id'] for f in filtered.json()['items']] == [high['id']]
        assert client.get(path + '/findings/' + high['id']).json()['validation_status'] == 'suspected'
        headers['Idempotency-Key'] = uuid4().hex
        foreign = client.post(path + '/findings/' + low['id'] + '/review', headers=headers,
                              json={**review, 'evidence_ids': high['observation_ids']})
        assert foreign.status_code == 422, foreign.text
        revision = client.get(path).json()['assessment']['state_revision']
        headers['Idempotency-Key'] = uuid4().hex
        report = client.post(path + '/reports', headers=headers, json={'expected_revision': revision, 'include_suspected': True})
        assert report.status_code == 202, report.text
        report_id, import_id, artifact_id = report.json()['resource_id'], accepted.json()['resource_id'], status['artifact_id']
        workspace_findings = client.get('/api/v1/workspace/findings')
        assert workspace_findings.status_code == 200, workspace_findings.text
        validate('WorkspaceFindingPage', workspace_findings.json())
        assert {item['finding']['id'] for item in workspace_findings.json()['items']} == {high['id'], low['id']}
        assert all(item['assessment']['id'] == path.rsplit('/', 1)[1] for item in workspace_findings.json()['items'])
        partial_page = client.get('/api/v1/workspace/findings?limit=1')
        assert partial_page.status_code == 200, partial_page.text
        validate('WorkspaceFindingPage', partial_page.json())
        assert len(partial_page.json()['items']) == 1 and partial_page.json()['next_cursor']
        for filters in ['severity=high', 'priority=review_first', 'search=Needle', 'disposition=accepted', 'severity=high&priority=review_first&search=Needle&disposition=accepted']:
            filtered_workspace = client.get('/api/v1/workspace/findings?' + filters)
            assert filtered_workspace.status_code == 200, filtered_workspace.text
            validate('WorkspaceFindingPage', filtered_workspace.json())
            assert [item['finding']['id'] for item in filtered_workspace.json()['items']] == [high['id']], filters
        workspace_reports = client.get('/api/v1/workspace/reports')
        assert workspace_reports.status_code == 200, workspace_reports.text
        validate('WorkspaceReportPage', workspace_reports.json())
        assert [item['report']['id'] for item in workspace_reports.json()['items']] == [report_id]
        workspace_timeline = client.get('/api/v1/workspace/timeline')
        assert workspace_timeline.status_code == 200, workspace_timeline.text
        validate('TimelineEventPage', workspace_timeline.json())
        assert workspace_timeline.json()['items']
        assert {item['assessment_id'] for item in workspace_timeline.json()['items']} <= {path.rsplit('/', 1)[1], second_path.rsplit('/', 1)[1]}
        summary_response = client.get('/api/v1/workspace/summary')
        assert summary_response.status_code == 200, summary_response.text
        validate('WorkspaceSummary', summary_response.json())
        summary = summary_response.json()
        assert {key: summary[key] for key in ('assessment_count', 'finding_count', 'report_count', 'pending_approval_count', 'failed_latest_execution_count')} == {'assessment_count': 2, 'finding_count': 2, 'report_count': 1, 'pending_approval_count': 0, 'failed_latest_execution_count': 0}
        suffixes = ['/imports/' + import_id, '/findings/' + high['id'], '/artifacts/' + artifact_id,
                    '/artifacts/' + artifact_id + '/download', '/reports/' + report_id,
                    '/reports/' + report_id + '/snapshot', '/reports/' + report_id + '/download']
        for suffix in suffixes:
            assert client.get(second_path + suffix).status_code == 404, suffix
        with TestClient(app, client=('anonymous-' + uuid4().hex, 50001)) as anonymous:
            for suffix in suffixes:
                assert anonymous.get(path + suffix).status_code == 401, suffix
        other_password = uuid4().hex
        other_settings = Settings(database_url=URL, artifact_root=tmp_path, username='other_' + uuid4().hex,
                                  password_hash=hash_password(other_password), actor_id=str(uuid4()),
                                  allowed_origins=('http://localhost:3000',))
        with TestClient(create_app(other_settings), client=('other-' + uuid4().hex, 50002)) as other:
            other_login = other.post('/api/v1/auth/login', headers={'Origin': 'http://localhost:3000'}, json={'username': other_settings.username, 'password': other_password})
            assert other_login.status_code == 200, other_login.text
            empty_summary = other.get('/api/v1/workspace/summary')
            assert empty_summary.status_code == 200, empty_summary.text
            validate('WorkspaceSummary', empty_summary.json())
            assert all(empty_summary.json()[key] == 0 for key in ('assessment_count', 'finding_count', 'report_count'))
            for resource, schema in [('findings', 'WorkspaceFindingPage'), ('reports', 'WorkspaceReportPage'), ('timeline', 'TimelineEventPage')]:
                projection = other.get('/api/v1/workspace/' + resource)
                assert projection.status_code == 200, projection.text
                validate(schema, projection.json())
                assert projection.json()['items'] == []
            other_headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': other_login.json()['csrf_token'], 'Idempotency-Key': uuid4().hex}
            for suffix in suffixes:
                assert other.get(path + suffix).status_code == 404, suffix
            assert other.post(path + '/imports', headers=other_headers, data=metadata, files={'file': ('fixture.json', raw, 'application/json')}).status_code == 404
