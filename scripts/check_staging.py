#!/usr/bin/env python3
"""Read-only staging configuration preflight. Never print resolved secrets."""
import argparse
import base64
import json
from pathlib import Path
import re
import stat
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def _database_url(value):
    try:
        url = urlsplit(value)
        if url.scheme == 'postgresql+psycopg' and url.hostname == 'db' and url.port == 5432 and url.path == '/reknyx' and not url.query and not url.fragment:
            return unquote(url.username or ''), unquote(url.password or '')
    except (TypeError, ValueError):
        pass
    return '', ''


def _password_hash(value):
    try:
        kind, n, r, p, salt, digest = value.split('$')
        return ((kind, n, r, p) == ('scrypt', '16384', '8', '1') and
                len(base64.b64decode(salt, altchars=b'-_', validate=True)) == 16 and
                len(base64.b64decode(digest, altchars=b'-_', validate=True)) == 32)
    except (ValueError, TypeError):
        return False


def validate_config(config):
    """Validate resolved Compose boundaries; errors contain field names only."""
    errors = []
    services = config.get('services', {})
    expected = {'db', 'migrate', 'api', 'worker', 'frontend', 'proxy'}
    if set(services) != expected:
        return ['staging requires exactly db, migrate, api, worker, frontend and proxy']
    for name, service in services.items():
        if not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}', service.get('image', '')) or service.get('build'):
            errors.append(f'{name}: require an image digest and no build configuration')
        if name != 'proxy' and service.get('ports'):
            errors.append(f'{name}: internal service must not publish ports')
        if (service.get('privileged') or service.get('network_mode') or service.get('pid') or
                service.get('devices') or service.get('cap_add')):
            errors.append(f'{name}: host privileges are unsupported')
        for mount in service.get('volumes', []):
            if mount.get('type') == 'bind' and any('docker.sock' in mount.get(key, '') or 'containerd.sock' in mount.get(key, '') for key in ('source', 'target')):
                errors.append(f'{name}: container runtime sockets are forbidden')
    if len({services[name].get('image') for name in ('api', 'worker', 'migrate')}) != 1:
        errors.append('api, worker and migrate must use the same backend digest')
    for name in ('app', 'data'):
        if config.get('networks', {}).get(name, {}).get('internal') is not True:
            errors.append(f'{name}: network must be internal')
    expected_networks = {'db': {'data'}, 'migrate': {'data'}, 'api': {'app', 'data'},
                         'worker': {'data'}, 'frontend': {'edge', 'app'}, 'proxy': {'edge'}}
    for name, networks in expected_networks.items():
        if set(services[name].get('networks', {})) != networks:
            errors.append(f'{name}: unexpected network membership')
    publications = services['proxy'].get('ports', [])
    if sorted((int(port['target']), str(port['published']), port.get('protocol', 'tcp')) for port in publications) != [(80, '80', 'tcp'), (443, '443', 'tcp')]:
        errors.append('proxy: publish only TCP 80 and 443 on matching host ports')
    host = services['proxy'].get('environment', {}).get('REKNYX_STAGING_HOST', '')
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host) or '.' not in host:
        errors.append('proxy: require a DNS hostname without scheme, path or port')
    db = services['db'].get('environment', {})
    owner, runtime = db.get('POSTGRES_PASSWORD', ''), db.get('REKNYX_RUNTIME_PASSWORD', '')
    if min(len(owner), len(runtime)) < 24 or owner == runtime or any('CHANGE_ME' in value for value in (owner, runtime)):
        errors.append('db: require distinct owner/runtime passwords of at least 24 characters')
    if _database_url(services['migrate'].get('environment', {}).get('REKNYX_DATABASE_URL', '')) != ('postgres', owner):
        errors.append('migrate: database URL must match the configured owner login')
    for name in ('api', 'worker'):
        service = services[name]
        env = service.get('environment', {})
        if _database_url(env.get('REKNYX_DATABASE_URL', '')) != ('reknyx_app', runtime):
            errors.append(f'{name}: database URL must match the non-owner runtime login')
        if env.get('REKNYX_ALLOWED_ORIGINS') != 'https://' + host:
            errors.append(f'{name}: require the exact public HTTPS origin')
        if env.get('REKNYX_ANALYSIS_PROVIDER') != 'deterministic' or env.get('REKNYX_GROQ_API_KEY'):
            errors.append(f'{name}: this staging increment permits local deterministic review only')
        if not _password_hash(env.get('REKNYX_PASSWORD_HASH', '')):
            errors.append(f'{name}: require a valid application scrypt hash')
        if any(key in env for key in ('REKNYX_MIGRATION_DATABASE_URL', 'POSTGRES_PASSWORD', 'REKNYX_RUNTIME_PASSWORD')):
            errors.append(f'{name}: do not supply database provisioning credentials')
        if not any(m.get('type') == 'volume' and m.get('source') == 'artifacts' and m.get('target') == '/var/lib/reknyx' for m in service.get('volumes', [])):
            errors.append(f'{name}: require the persistent private artifacts volume')
    if not any(m.get('type') == 'volume' and m.get('source') == 'database' and m.get('target') == '/var/lib/postgresql/data' for m in services['db'].get('volumes', [])):
        errors.append('db: require the persistent database volume')
    for name, user in (('api', '10001:10001'), ('worker', '10001:10001'), ('frontend', 'node')):
        service = services[name]
        if service.get('user') != user or not service.get('read_only') or 'ALL' not in service.get('cap_drop', []) or 'no-new-privileges:true' not in service.get('security_opt', []):
            errors.append(f'{name}: require the non-root, read-only, unprivileged runtime')
    if services['frontend'].get('environment', {}).get('REKNYX_BACKEND_ORIGIN') != 'http://api:8000':
        errors.append('frontend: require the fixed private backend origin')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / 'deploy/staging/.env')
    args = parser.parse_args(argv)
    try:
        env_file = args.env_file.absolute()
        info = env_file.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Use a regular private environment file with mode 0600')
        rendered = subprocess.run(['docker', 'compose', '--project-name', 'reknyx-staging',
            '--env-file', str(env_file), '-f', str(ROOT / 'deploy/staging/compose.yml'),
            'config', '--format', 'json'], capture_output=True, text=True, timeout=30)
        if rendered.returncode:
            raise ValueError('Compose configuration failed; check required variables and Compose compatibility locally')
        config = json.loads(rendered.stdout)
        # `compose config` escapes dollars for a second Compose parse. Inspect
        # the actual environment bytes rather than its round-trip encoding.
        for service in config.get('services', {}).values():
            for key, value in service.get('environment', {}).items():
                if isinstance(value, str):
                    service['environment'][key] = value.replace('$$', '$')
        errors = validate_config(config)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        print('Staging preflight failed: check private env-file, required configuration and Docker Compose installation')
        return 1
    if errors:
        for error in errors:
            print('FAIL: ' + error)
        return 1
    print('PASS: offline staging configuration boundaries; no deployment, provider request or scanner execution performed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
