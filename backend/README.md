# Reknyx backend foundation

This backend provides the initial session, assessment, message, audit and private
artifact services, durable Nmap/ZAP imports, finding review and immutable draft PDF reports.
Scanner execution and planning remain in development. G0 verification is recorded in
`contracts/review-status.json`; full browser acceptance is reported separately.

Use Python 3.13 and `uv`; dependencies are locked in `uv.lock`.

```bash
cd backend
uv sync --frozen
```

Provision an isolated PostgreSQL database and two separate credentials: a migration
owner with permission to create the `reknyx_runtime` role, and a non-owner runtime
login granted membership in that role. The migration creates the NOLOGIN role and
grants its table permissions. Grant that role to the runtime login using a trusted
database administrator; never use the database owner for the application process.
The migration does not create the runtime login or its password.

Set `REKNYX_MIGRATION_DATABASE_URL` and `REKNYX_RUNTIME_DATABASE_URL` privately to
their respective `postgresql+psycopg://` connection URLs, then apply migrations:

```bash
REKNYX_DATABASE_URL="$REKNYX_MIGRATION_DATABASE_URL" uv run alembic upgrade head
```

Set an absolute private artifact directory and the exact allowed frontend origin.
Create `REKNYX_PASSWORD_HASH` with `reknyx.infrastructure.auth.hash_password` in a
private setup process; never put plaintext passwords in source or shell history.
The application accepts one configured account, default username `admin`, and an
eight-hour absolute session. For this local checkout an ignored `backend/.env`
holds the requested local admin password hash with mode 0600. It has no database
credentials and must not be used as a production credential. An operator may load
it with `set -a; . ./.env; set +a` from this directory.

```bash
export REKNYX_DATABASE_URL="$REKNYX_RUNTIME_DATABASE_URL"
export REKNYX_ARTIFACT_ROOT="/absolute/private/reknyx-artifacts"
export REKNYX_ALLOWED_ORIGINS="http://localhost:3000"
uv run uvicorn reknyx.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

The browser frontend remains an explicit synthetic preview until its owner wires
API mode. Use `GET /api/v1/health/live` and `/api/v1/health/ready` for process and
database/migration status; neither proves scanner or platform readiness. Authenticated
session creation requires the configured origin. Planned routes return typed 501.

For local API reference, set `REKNYX_ENABLE_API_DOCS=true` before starting the API,
then open `http://127.0.0.1:8000/docs` (use your configured API port). The page
loads Swagger UI assets from a CDN and displays the reviewed contract, including
planned operations; `/api/v1/capabilities` reports runtime availability. Docs are
disabled by default. Swagger requests still require authentication, CSRF and the
exact configured origin; opening docs on the API origin does not bypass these checks.

The artifact service stores raw bytes with private permissions, SHA-256 and durable
publication receipts. Its reconciliation method reports orphaned/missing artifacts
without deleting them. This is not a backup/restore solution. Pending idempotency
reservations after a crash remain pending until a trusted recovery procedure proves
their outcome; no automatic recovery endpoint is exposed yet.

Run unit tests with `uv run pytest tests/unit -q`. Integration tests require a
**dedicated disposable** migrated PostgreSQL database, with `REKNYX_TEST_DATABASE_URL`
set to the non-owner runtime URL and `REKNYX_TEST_ADMIN_DATABASE_URL` to its owner
URL. The tests remove login rate-limit rows in that database and create synthetic
records; never point them at user data. Then run `uv run pytest tests -q`.

## Import and report worker

Run a separate process with the same runtime database URL and private artifact root:

```bash
cd backend
uv run python -m reknyx.orchestration.worker
```

`--once` processes at most one queued import and one pending report. Imports accept
`nmap_xml` and traditional `zap_json` original bytes with declared provenance.
Greenbone and live scanners remain unavailable. The worker claims durable rows,
parses in a separate process (10 seconds/512 MiB), and renders frozen snapshots in
a separate process (30 seconds/512 MiB). Nmap open services stay observations;
ZAP candidates retain suspected technical validation after analyst acceptance.

Reports remain drafts, retain parser versions and raw artifact hashes, and serve
stored PDF bytes after readiness. Unsupported font glyphs fail rendering explicitly.
Queued work survives restart. A crash after claim leaves `parsing` or `rendering`
visible for trusted reconciliation; no automatic replay or recovery command is
implemented. Publication receipts and orphan diagnostics must be inspected before
an operator changes unresolved state. Do not requeue blindly. Backup/restore and
operational pilot acceptance are separate work.

Root `docker-compose.yml` describes the local DB/migration/API/worker/frontend
stack. Copy `.env.example` into ignored `.env`, set unique passwords and a scrypt
hash, and use separately URL-encoded migration-owner/runtime connection URLs.
The DB init script grants the application runtime role; initialization applies only
to a fresh database volume. Never replace existing volumes to apply credential
changes. API and frontend ports bind to loopback. The Compose configuration is not
production deployment acceptance.
