#!/usr/bin/env python3
"""Run PostgreSQL tests in a fresh, loopback-only, memory-backed container.

Never uses an existing application/test database URL or persistent volume.
Requires a running Docker context and cached postgres:17-alpine image.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres:17-alpine'


def child_environment(inherited, owner_url, runtime_url):
    env = {k:v for k,v in inherited.items()
           if not k.startswith(('REKNYX_','PYTEST_')) and k not in ('GROQ_API_KEY','PYTHONPATH')}
    env.update(REKNYX_DATABASE_URL=runtime_url, REKNYX_TEST_DATABASE_URL=runtime_url,
               REKNYX_TEST_ADMIN_DATABASE_URL=owner_url, REKNYX_ANALYSIS_PROVIDER='deterministic',
               PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker-context', required=True)
    parser.add_argument('tests', nargs='*', default=['backend/tests/integration/test_analysis_workflow.py'])
    args = parser.parse_args(argv)
    for value in args.tests:
        path = (ROOT/value).resolve()
        if not path.is_relative_to(ROOT/'backend/tests') or not path.exists():
            parser.error('Only existing backend/tests paths are accepted.')
    docker = ['docker','--context',args.docker_context]
    name = 'reknyx-test-db-' + secrets.token_hex(10)
    owner_password, runtime_password = secrets.token_hex(24), secrets.token_hex(24)
    container_id = None
    creation_attempted = False
    redactions = [owner_password,runtime_password]

    def emit(value):
        for secret in redactions:
            value = value.replace(secret,'[redacted]')
        print(value, end='' if value.endswith('\n') else '\n', flush=True)

    def command(cmd, *, env=None, cwd=ROOT):
        result = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            emit(result.stdout)
            raise RuntimeError('Disposable database command failed.')
        return result.stdout.strip()

    status = 2
    try:
        command(docker+['info','--format','{{.ServerVersion}}'])
        image_id = command(docker+['image','inspect','--format','{{.Id}}',IMAGE])
        # Values use environment forwarding, not password-bearing command arguments.
        container_env = {**os.environ, 'POSTGRES_PASSWORD':owner_password}
        creation_attempted = True
        container_id = command(docker+['create','--pull','never','--name',name,
            '--label','reknyx.disposable-test=true','--label','reknyx.test-run='+name,'--memory','512m','--cpus','1',
            '--publish','127.0.0.1::5432','--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=256m',
            '--env','POSTGRES_PASSWORD','--env','POSTGRES_DB=reknyx_test',IMAGE],env=container_env)
        command(docker+['start',container_id])
        binding = command(docker+['port',container_id,'5432/tcp'])
        port = int(binding.split(':')[-1])
        owner_dsn = f'postgresql://postgres:{owner_password}@127.0.0.1:{port}/reknyx_test'
        deadline = time.monotonic()+45
        while True:
            try:
                with psycopg.connect(owner_dsn,connect_timeout=2,autocommit=True) as connection:
                    version = connection.execute('SHOW server_version').fetchone()[0]
                    connection.execute(sql.SQL('CREATE ROLE reknyx_test_app LOGIN PASSWORD {}').format(sql.Literal(runtime_password)))
                break
            except psycopg.OperationalError:
                if time.monotonic()>=deadline:
                    raise RuntimeError('Disposable PostgreSQL did not become ready.') from None
                time.sleep(.3)
        owner_url = owner_dsn.replace('postgresql://','postgresql+psycopg://',1)
        runtime_url = f'postgresql+psycopg://reknyx_test_app:{runtime_password}@127.0.0.1:{port}/reknyx_test'
        env = child_environment(os.environ,owner_url,runtime_url)
        command([sys.executable,'-m','alembic','upgrade','head'], env={**env,'REKNYX_DATABASE_URL':owner_url},cwd=ROOT/'backend')
        with psycopg.connect(owner_dsn,autocommit=True) as connection:
            connection.execute('GRANT reknyx_runtime TO reknyx_test_app')
        runtime_dsn = runtime_url.replace('postgresql+psycopg://','postgresql://',1)
        with psycopg.connect(runtime_dsn) as connection:
            role = connection.execute("SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user").fetchone()
            owns = connection.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner=current_user").fetchone()[0]
            if any(role) or owns:
                raise RuntimeError('Test runtime role has excessive database authority.')
        emit(json.dumps({'database':'fresh_disposable','container':name,'postgres_version':version,
            'image_id':image_id,'runtime_non_owner':True,'tests':args.tests}))
        result = subprocess.run([sys.executable,'-m','pytest',*args.tests,'-q'],cwd=ROOT,env=env,
                                text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        emit(result.stdout)
        status = result.returncode
    except (OSError,ValueError,RuntimeError,psycopg.Error):
        emit('Disposable database setup/test failed; no existing database was selected.')
    finally:
        if creation_attempted:
            try:
                owned = command(docker+['container','ls','--all',
                    '--filter','name=^/'+name+'$', '--filter','label=reknyx.test-run='+name,
                    '--format','{{.ID}}']).splitlines()
                for identifier in owned:
                    command(docker+['rm','--force',identifier])
                emit('Disposable PostgreSQL resources reconciled; no persistent volume was used.')
            except (OSError,RuntimeError):
                emit('Cleanup incomplete for '+name+'; reconcile this disposable container.')
                status=2
    return status


if __name__=='__main__':
    raise SystemExit(main())
