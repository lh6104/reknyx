"""Actual PostgreSQL HTTP integration; use a dedicated disposable database."""
import json
import hashlib
import os
import threading
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from reknyx.config import Settings
from reknyx.infrastructure.auth import hash_password
from reknyx.main import create_app
from reknyx.contracts import validate

URL = os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='isolated PostgreSQL URL not supplied')
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def setup(tmp_path):
    # The database belongs to this test run; isolate login rate-limit state.
    engine = create_engine(os.getenv('REKNYX_TEST_ADMIN_DATABASE_URL', URL))
    with engine.begin() as connection:
        connection.execute(text('DELETE FROM login_buckets'))
    engine.dispose()
    password = uuid4().hex
    username = 'test_' + uuid4().hex
    settings = Settings(database_url=URL, artifact_root=tmp_path, username=username,
                        password_hash=hash_password(password), actor_id=str(uuid4()),
                        allowed_origins=('http://localhost:3000',))
    with TestClient(create_app(settings)) as client:
        yield client, settings, password


def login(client, settings, password):
    return client.post('/api/v1/auth/login', headers={'Origin': 'http://localhost:3000'},
                       json={'username': settings.username, 'password': password})


def input_data():
    cases = json.loads((ROOT / 'contracts/examples/schema-cases.json').read_text())['cases']
    scope = next(c['payload'] for c in cases if c['id'] == 'valid-ScopeInput')
    return {'name': 'Synthetic assessment', 'request': 'Review local fixture', 'scope': scope}


def test_authenticated_persistence_replay_and_conflicts(setup):
    client, settings, password = setup
    assert client.get('/api/v1/health/ready').status_code == 200
    assert client.post('/api/v1/assessments', json={}).status_code == 401
    assert login(client, settings, 'wrong').status_code == 401
    session = login(client, settings, password)
    assert session.status_code == 200, session.text
    validate('Session', session.json())
    assert 'httponly' in session.headers['set-cookie'].lower()
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'create-1'}
    assert client.post('/api/v1/assessments', headers={'Origin': 'http://localhost:3000'}, json=input_data()).status_code == 403
    created = client.post('/api/v1/assessments', headers=headers, json=input_data())
    assert created.status_code == 201, created.text
    validate('AssessmentDetail', created.json())
    assessment_id = created.json()['assessment']['id']
    assert client.post('/api/v1/assessments', headers=headers, json=input_data()).json() == created.json()
    changed = input_data(); changed['name'] = 'Different intent'
    assert client.post('/api/v1/assessments', headers=headers, json=changed).status_code == 409
    path = f'/api/v1/assessments/{assessment_id}'
    assert client.get(path).json() == created.json()
    message = {'content': 'Synthetic note', 'expected_revision': 1}
    headers['Idempotency-Key'] = 'message-1'
    result = client.post(path + '/messages', headers=headers, json=message)
    assert result.status_code == 201, result.text
    validate('ConversationMessage', result.json())
    assert client.post(path + '/messages', headers=headers, json=message).json() == result.json()
    assert len(client.get(path + '/messages').json()['items']) == 1
    headers['Idempotency-Key'] = 'message-2'
    assert client.post(path + '/messages', headers=headers, json=message).status_code == 409
    headers['Idempotency-Key'] = 'scope-1'
    scope = client.put(path + '/scope', headers=headers, json={'expected_version': 1, 'scope': input_data()['scope']})
    assert scope.status_code == 200, scope.text
    validate('Scope', scope.json())
    assert scope.json()['version'] == 2
    assert client.post('/api/v1/auth/logout', headers=headers).status_code == 204
    assert client.get(path).status_code == 401


def test_other_actor_cannot_read_assessment(setup, tmp_path):
    client, settings, password = setup
    session = login(client, settings, password)
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'actor-create'}
    created = client.post('/api/v1/assessments', headers=headers, json=input_data())
    assert created.status_code == 201, created.text
    assessment_id = created.json()['assessment']['id']
    other_password = uuid4().hex
    other = Settings(database_url=URL, artifact_root=tmp_path, username='other_' + uuid4().hex,
                     password_hash=hash_password(other_password), actor_id=str(uuid4()),
                     allowed_origins=('http://localhost:3000',))
    with TestClient(create_app(other)) as second:
        assert login(second, other, other_password).status_code == 200
        assert second.get(f'/api/v1/assessments/{assessment_id}').status_code == 404


def test_artifact_round_trip_and_restart(setup):
    from reknyx.evidence.service import ArtifactService

    client, settings, password = setup
    session = login(client, settings, password)
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'artifact-owner'}
    created = client.post('/api/v1/assessments', headers=headers, json=input_data())
    assert created.status_code == 201, created.text
    assessment_id = created.json()['assessment']['id']
    raw = b'{"synthetic": "original bytes"}\r\n'
    metadata = {'source': 'import', 'content_type': 'application/json', 'observed_at': None,
                'provenance': 'synthetic_fixture', 'historical': True}
    with client.app.state.session_factory() as db:
        manifest = ArtifactService(db, client.app.state.artifact_store, settings.actor_id).put_bytes(assessment_id, raw, metadata)
        db.commit()
    response = client.get(manifest['download_url'])
    assert response.status_code == 200
    assert response.content == raw
    assert response.headers['X-Content-SHA256'] == hashlib.sha256(raw).hexdigest()
    with TestClient(create_app(settings)) as restarted:
        assert login(restarted, settings, password).status_code == 200
        assert restarted.get(f'/api/v1/assessments/{assessment_id}').status_code == 200
        assert restarted.get(manifest['download_url']).content == raw


def test_concurrent_replay_reports_durable_in_progress(setup, monkeypatch):
    from reknyx.assessments.service import AssessmentService

    client, settings, password = setup
    session = login(client, settings, password)
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'concurrent-create'}
    entered, release = threading.Event(), threading.Event()
    original = AssessmentService.create

    def blocked(service, value):
        entered.set()
        assert release.wait(10)
        return original(service, value)

    monkeypatch.setattr(AssessmentService, 'create', blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(client.post, '/api/v1/assessments', headers=headers, json=input_data())
        try:
            assert entered.wait(5)
            duplicate = client.post('/api/v1/assessments', headers=headers, json=input_data())
            assert duplicate.status_code == 409, duplicate.text
            assert duplicate.json()['error']['code'] == 'operation_in_progress'
            assert duplicate.headers['Retry-After']
            assert duplicate.json()['error']['details'][0]['resource_id']
        finally:
            release.set()
        result = first.result(timeout=10)
    assert result.status_code == 201, result.text
    assert client.post('/api/v1/assessments', headers=headers, json=input_data()).json() == result.json()


def test_creation_replay_rechecks_revoked_membership(setup):
    client, settings, password = setup
    session = login(client, settings, password)
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'revoked-create'}
    result = client.post('/api/v1/assessments', headers=headers, json=input_data())
    assert result.status_code == 201, result.text
    admin = create_engine(os.getenv('REKNYX_TEST_ADMIN_DATABASE_URL', URL))
    with admin.begin() as connection:
        connection.execute(text('DELETE FROM assessment_memberships WHERE assessment_id=:assessment_id AND actor_id=:actor_id'),
                           {'assessment_id': result.json()['assessment']['id'], 'actor_id': settings.actor_id})
    admin.dispose()
    assert client.post('/api/v1/assessments', headers=headers, json=input_data()).status_code == 404


def test_runtime_role_cannot_change_audit_history(setup):
    client, settings, password = setup
    session = login(client, settings, password)
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'audit-create'}
    assert client.post('/api/v1/assessments', headers=headers, json=input_data()).status_code == 201
    engine = create_engine(URL)
    for statement in ('DELETE FROM audit_events', 'UPDATE audit_events SET data = data', 'TRUNCATE audit_events'):
        with pytest.raises(DBAPIError):
            with engine.begin() as connection:
                connection.execute(text(statement))
    engine.dispose()


def test_known_database_failure_is_recorded_and_replayed(setup, monkeypatch):
    from reknyx.assessments.service import AssessmentService
    from sqlalchemy.exc import SQLAlchemyError

    client, settings, password = setup
    session = login(client, settings, password)
    headers = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'failed-create'}
    attempts = []

    def failed(*_):
        attempts.append(1)
        raise SQLAlchemyError('synthetic database failure')

    monkeypatch.setattr(AssessmentService, 'create', failed)
    first = client.post('/api/v1/assessments', headers=headers, json=input_data())
    assert first.status_code == 503
    second = client.post('/api/v1/assessments', headers=headers, json=input_data())
    assert second.status_code == 503, second.text
    assert second.json()['error']['code'] == 'dependency_unavailable'
    assert len(attempts) == 1


def test_real_http_survives_process_restart(setup, tmp_path):
    _, settings, password = setup
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = {**os.environ, 'REKNYX_DATABASE_URL': URL, 'REKNYX_ARTIFACT_ROOT': str(tmp_path),
           'REKNYX_USERNAME': settings.username, 'REKNYX_PASSWORD_HASH': settings.password_hash,
           'REKNYX_ACTOR_ID': settings.actor_id, 'REKNYX_ALLOWED_ORIGINS': 'http://localhost:3000'}
    origin = {'Origin': 'http://localhost:3000'}

    def start():
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'reknyx.main:create_app', '--factory',
                                    '--host', '127.0.0.1', '--port', str(port), '--no-access-log'],
                                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail('API process exited during startup')
            try:
                if httpx.get(f'http://127.0.0.1:{port}/api/v1/health/ready', timeout=0.5).status_code == 200:
                    return process
            except httpx.TransportError:
                pass
            time.sleep(0.05)
        process.terminate()
        process.wait(timeout=5)
        pytest.fail('API process did not become ready')

    def stop(process):
        process.terminate()
        process.wait(timeout=10)

    process = start()
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}') as client:
            session = client.post('/api/v1/auth/login', headers=origin,
                                  json={'username': settings.username, 'password': password})
            assert session.status_code == 200, session.text
            headers = {**origin, 'X-CSRF-Token': session.json()['csrf_token'], 'Idempotency-Key': 'restart-create'}
            created = client.post('/api/v1/assessments', headers=headers, json=input_data())
            assert created.status_code == 201, created.text
            assessment_id = created.json()['assessment']['id']
    finally:
        stop(process)
    process = start()
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}') as client:
            assert client.post('/api/v1/auth/login', headers=origin,
                               json={'username': settings.username, 'password': password}).status_code == 200
            assert client.get(f'/api/v1/assessments/{assessment_id}').json() == created.json()
    finally:
        stop(process)
