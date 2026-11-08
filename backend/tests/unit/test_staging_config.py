"""Offline deployment checks: no cloud, Docker daemon, or credentials required."""
import copy
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / 'scripts/check_staging.py'


def validator():
    assert SCRIPT.is_file(), 'Staging preflight has not been implemented'
    spec = importlib.util.spec_from_file_location('staging_check', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_config


@pytest.fixture
def config():
    digest = 'registry.test/app@sha256:' + 'a' * 64
    runtime = {
        'REKNYX_DATABASE_URL': 'postgresql+psycopg://reknyx_app:runtime-secret-0123456789@db:5432/reknyx',
        'REKNYX_PASSWORD_HASH': 'scrypt$16384$8$1$MDEyMzQ1Njc4OWFiY2RlZg==$MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=',
        'REKNYX_ALLOWED_ORIGINS': 'https://staging.reknyx.test',
        'REKNYX_ANALYSIS_PROVIDER': 'deterministic',
    }
    artifacts = [{'type': 'volume', 'source': 'artifacts', 'target': '/var/lib/reknyx'}]
    result = {'services': {name: {'image': digest, 'networks': {'data': None}}
                           for name in ('api', 'worker', 'migrate', 'frontend', 'proxy', 'db')},
              'networks': {'data': {'internal': True}, 'app': {'internal': True}, 'edge': {}},
              'volumes': {'database': {}, 'artifacts': {}, 'caddy_data': {}, 'caddy_config': {}}}
    services = result['services']
    for name in ('api', 'worker'):
        services[name].update(environment=copy.deepcopy(runtime), volumes=copy.deepcopy(artifacts),
                              user='10001:10001', read_only=True,
                              cap_drop=['ALL'], security_opt=['no-new-privileges:true'])
    services['api']['networks'] = {'app': None, 'data': None}
    services['frontend'].update(networks={'edge': None, 'app': None},
        environment={'REKNYX_BACKEND_ORIGIN': 'http://api:8000'}, user='node', read_only=True,
        cap_drop=['ALL'], security_opt=['no-new-privileges:true'])
    services['proxy'].update(networks={'edge': None},
        environment={'REKNYX_STAGING_HOST': 'staging.reknyx.test'},
        ports=[{'target': 80, 'published': '80'}, {'target': 443, 'published': '443'}])
    services['db'].update(environment={'POSTGRES_PASSWORD': 'owner-secret-012345678901',
        'REKNYX_RUNTIME_PASSWORD': 'runtime-secret-0123456789'},
        volumes=[{'type': 'volume', 'source': 'database', 'target': '/var/lib/postgresql/data'}])
    services['migrate']['environment'] = {
        'REKNYX_DATABASE_URL': 'postgresql+psycopg://postgres:owner-secret-012345678901@db:5432/reknyx'}
    return result


def test_accepts_private_digest_pinned_import_only_staging(config):
    assert validator()(config) == []


@pytest.mark.parametrize('change', ['floating-image', 'public-db', 'http-origin', 'owner-runtime',
    'same-password', 'provider', 'socket', 'privileged', 'ephemeral-artifacts',
    'public-network', 'owner-secret-leak', 'different-worker-image', 'root-api'])
def test_rejects_deployment_that_breaks_boundaries(config, change):
    services = config['services']
    if change == 'floating-image': services['api']['image'] = 'registry.test/app:latest'
    elif change == 'public-db': services['db']['ports'] = [{'target': 5432, 'published': '5432'}]
    elif change == 'http-origin': services['api']['environment']['REKNYX_ALLOWED_ORIGINS'] = 'http://staging.reknyx.test'
    elif change == 'owner-runtime': services['api']['environment']['REKNYX_DATABASE_URL'] = services['migrate']['environment']['REKNYX_DATABASE_URL']
    elif change == 'same-password': services['db']['environment']['REKNYX_RUNTIME_PASSWORD'] = services['db']['environment']['POSTGRES_PASSWORD']
    elif change == 'provider': services['api']['environment']['REKNYX_ANALYSIS_PROVIDER'] = 'groq'
    elif change == 'socket': services['worker']['volumes'].append({'type': 'bind', 'source': '/var/run/docker.sock', 'target': '/run/docker.sock'})
    elif change == 'privileged': services['worker']['privileged'] = True
    elif change == 'ephemeral-artifacts': services['api']['volumes'] = []
    elif change == 'public-network': config['networks']['data']['internal'] = False
    elif change == 'owner-secret-leak': services['api']['environment']['REKNYX_MIGRATION_DATABASE_URL'] = services['migrate']['environment']['REKNYX_DATABASE_URL']
    elif change == 'different-worker-image': services['worker']['image'] = 'registry.test/app@sha256:' + 'b' * 64
    elif change == 'root-api': services['api']['user'] = '0:0'
    errors = validator()(config)
    assert errors, f'Unsafe deployment was accepted: {change}'
    assert 'owner-secret-' not in str(errors)
    assert 'runtime-secret-' not in str(errors)


@pytest.mark.skipif(not shutil.which('docker'), reason='Docker Compose CLI required; no daemon used')
def test_preflight_resolves_real_compose_and_literal_dollar_hash(tmp_path):
    """A valid scrypt hash must survive Compose's escaped config serialization."""
    path = tmp_path / '.env'
    values = {
        'REKNYX_STAGING_HOST': 'staging.reknyx.test',
        'REKNYX_POSTGRES_PASSWORD': 'owner-secret-012345678901',
        'REKNYX_RUNTIME_PASSWORD': 'runtime-secret-0123456789',
        'REKNYX_MIGRATION_DATABASE_URL': 'postgresql+psycopg://postgres:owner-secret-012345678901@db:5432/reknyx',
        'REKNYX_RUNTIME_DATABASE_URL': 'postgresql+psycopg://reknyx_app:runtime-secret-0123456789@db:5432/reknyx',
        'REKNYX_PASSWORD_HASH': 'scrypt$16384$8$1$MDEyMzQ1Njc4OWFiY2RlZg==$MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=',
    }
    for key in ('BACKEND', 'FRONTEND', 'POSTGRES', 'PROXY'):
        values['REKNYX_' + key + '_IMAGE'] = 'registry.test/app@sha256:' + 'a' * 64
    path.touch(mode=0o600)
    path.write_text(''.join(f"{key}='{value}'\n" for key, value in values.items()))
    env = {key: value for key, value in os.environ.items() if not key.startswith('REKNYX_')}
    result = subprocess.run([sys.executable, str(SCRIPT), '--env-file', str(path)],
                            capture_output=True, text=True, env=env, timeout=40)
    assert result.returncode == 0, result.stdout
    assert 'PASS: offline' in result.stdout
    assert 'owner-secret' not in result.stdout + result.stderr


def test_cli_captures_compose_errors_without_echoing_secrets(tmp_path):
    env_file = tmp_path / '.env'
    env_file.touch(mode=0o600)
    docker = tmp_path / 'docker'
    docker.write_text(f'#!{sys.executable}\nimport sys\nprint("synthetic-private-secret", file=sys.stderr)\nsys.exit(3)\n')
    docker.chmod(0o700)
    result = subprocess.run([sys.executable, str(SCRIPT), '--env-file', str(env_file)],
        env={**os.environ, 'PATH': str(tmp_path)}, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert 'Staging preflight failed' in result.stdout
    assert 'synthetic-private-secret' not in result.stdout + result.stderr


def test_cli_rejects_public_environment_file_before_invoking_compose(tmp_path):
    env_file = tmp_path / '.env'
    env_file.touch(mode=0o644)
    env_file.chmod(0o644)
    sentinel = tmp_path / 'called'
    docker = tmp_path / 'docker'
    docker.write_text(f'#!{sys.executable}\nfrom pathlib import Path\nPath({str(sentinel)!r}).touch()\n')
    docker.chmod(0o700)
    result = subprocess.run([sys.executable, str(SCRIPT), '--env-file', str(env_file)],
        env={**os.environ, 'PATH': str(tmp_path)}, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert not sentinel.exists()
