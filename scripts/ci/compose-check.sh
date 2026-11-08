#!/usr/bin/env bash
# Destructive cleanup is restricted to this invocation's disposable project.
set -euo pipefail
cd "$(dirname "$0")/../.."
task_python="${REKNYX_CI_PYTHON:-$PWD/backend/.venv/bin/python}"
for dependency in docker npm pdftotext; do command -v "$dependency" >/dev/null; done
test -x "$task_python"
docker compose version >/dev/null
docker info >/dev/null
task_dir="$(mktemp -d "${TMPDIR:-/tmp}/reknyx-ci.XXXXXXXX")"
export REKNYX_CI_ENV_FILE="$task_dir/environment" REKNYX_CI_STATE="$task_dir/persistence.json"
"$task_python" - <<'PY'
import os, secrets, shlex, socket
from pathlib import Path
from reknyx.infrastructure.auth import hash_password

ports = []
sockets = []
try:
    for _ in range(3):
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        sockets.append(sock)
        ports.append(sock.getsockname()[1])
finally:
    for sock in sockets:
        sock.close()
owner, runtime, password = (secrets.token_hex(24) for _ in range(3))
values = {
    'REKNYX_CI_PROJECT': 'reknyx-ci-' + secrets.token_hex(8),
    'REKNYX_POSTGRES_PASSWORD': owner,
    'REKNYX_RUNTIME_PASSWORD': runtime,
    'REKNYX_PASSWORD_HASH': hash_password(password),
    'REKNYX_MIGRATION_DATABASE_URL': f'postgresql+psycopg://postgres:{owner}@db:5432/reknyx',
    'REKNYX_RUNTIME_DATABASE_URL': f'postgresql+psycopg://reknyx_app:{runtime}@db:5432/reknyx',
    'REKNYX_TEST_ADMIN_DATABASE_URL': f'postgresql+psycopg://postgres:{owner}@127.0.0.1:{ports[2]}/reknyx',
    'REKNYX_TEST_DATABASE_URL': f'postgresql+psycopg://reknyx_app:{runtime}@127.0.0.1:{ports[2]}/reknyx',
    'REKNYX_FRONTEND_PORT': str(ports[0]), 'REKNYX_API_PORT': str(ports[1]),
    'REKNYX_CI_DB_PORT': str(ports[2]),
    'REKNYX_ALLOWED_ORIGINS': f'http://127.0.0.1:{ports[0]}',
    'REKNYX_BROWSER_ORIGIN': f'http://127.0.0.1:{ports[0]}',
    'REKNYX_BROWSER_USERNAME': 'admin', 'REKNYX_BROWSER_PASSWORD': password,
    'REKNYX_ANALYSIS_PROVIDER': 'deterministic', 'REKNYX_GROQ_API_KEY': '',
    'REKNYX_GROQ_FREE_PLAN_CONFIRMED': 'false', 'REKNYX_GROQ_SYNTHETIC_ENABLED': 'false',
}
path = Path(os.environ['REKNYX_CI_ENV_FILE'])
path.touch(mode=0o600, exist_ok=False)
path.write_text(''.join(f'{key}={shlex.quote(value)}\n' for key, value in values.items()))
PY
# This file was generated above, never supplied by a caller.
set -a
source "$REKNYX_CI_ENV_FILE"
set +a
compose=(docker compose --project-name "$REKNYX_CI_PROJECT" --env-file "$REKNYX_CI_ENV_FILE" -f docker-compose.yml -f deploy/ci/compose.yml)
cleanup() {
    task_status=$?
    trap - EXIT
    if ! "${compose[@]}" down --volumes --remove-orphans; then
        printf '%s\n' "Cleanup incomplete for $REKNYX_CI_PROJECT; private recovery configuration retained at $task_dir" >&2
        exit 1
    fi
    rm -rf -- "$task_dir"
    exit "$task_status"
}
trap cleanup EXIT
"${compose[@]}" config --quiet
"${compose[@]}" build
"${compose[@]}" up --detach --wait db
"${compose[@]}" run --rm --no-deps migrate
"$task_python" -m pytest backend/tests -q
"${compose[@]}" up --detach api worker frontend
wait_for_stack() {
    "$task_python" - <<'PY'
import os, time
import httpx
origin = os.environ['REKNYX_BROWSER_ORIGIN']
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    try:
        with httpx.Client(timeout=3, trust_env=False) as client:
            if client.get(origin + '/api/v1/health/ready').status_code == 200 and client.get(origin).status_code == 200:
                break
    except httpx.HTTPError:
        pass
    time.sleep(0.5)
else:
    raise SystemExit('Disposable frontend/API did not become ready')
PY
}
wait_for_stack
# Password is always present: the existing browser suite cannot skip for setup.
npm --prefix frontend run test:api
"$task_python" scripts/ci/check-persistence.py capture
# No jobs remain pending after browser completion. This proves clean restart only.
"${compose[@]}" stop --timeout 45 api worker frontend db
"${compose[@]}" up --detach api worker frontend
wait_for_stack
"$task_python" scripts/ci/check-persistence.py verify
