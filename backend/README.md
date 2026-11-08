# Reknyx backend foundation

This backend provides the initial session, assessment, message, audit and private
artifact services, durable Nmap/ZAP/Greenbone imports, finding review and immutable draft PDF reports.
Scanner execution remains in development. Explicit evidence review is implemented; real Groq evaluation remains pending. G0 verification is recorded in
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
holds the local backend connection, admin password hash and optional Groq settings
with mode 0600. It must not be committed or used as production configuration. An operator may load
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
`nmap_xml`, traditional `zap_json` and `greenbone_xml` original bytes with declared provenance.
Live scanners remain unavailable. The worker claims durable rows,
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

Greenbone import supports one completed (`scan_run_status=Done`) XML report,
either standalone or inside a successful GMP `get_reports_response`/report wrapper.
It rejects document types/entities, multi-report exports, malformed hosts/ports and
resource limits. Non-XML/base64 and incomplete scans are unsupported. Result-count
truncation is labelled partial. Findings retain source severity and uncalibrated QoD;
log/error records remain informational observations. Original bytes and native NVT
fields remain traceable. Only an explicit supported CVSS 3.0/3.1 score/vector pair
populates canonical CVSS; missing/other native CVSS fields remain in source evidence.
Verification uses the labelled synthetic fixture under `tests/fixtures/greenbone/`;
a permitted native capture and broader format acceptance remain separate gates.

## Explicit evidence review and Groq setup

`POST /api/v1/assessments/{id}/plans` performs bounded evidence review;
`GET /api/v1/assessments/{id}/decisions` lists immutable decisions. Message append
never invokes review. The default `REKNYX_ANALYSIS_PROVIDER=deterministic` uses
local rules and labels the source accordingly. It performs no model call.

Groq is the first optional provider. Use a Groq free-plan account and configure
`REKNYX_ANALYSIS_PROVIDER=groq`, `REKNYX_GROQ_API_KEY` privately,
`REKNYX_GROQ_FREE_PLAN_CONFIRMED=true` after verifying the account is on the free plan, and
`REKNYX_GROQ_SYNTHETIC_ENABLED=true` only when the synthetic projection is covered
for transmission. The default model is `openai/gpt-oss-120b`, at Groq's fixed chat
completions endpoint. Free-plan limits and account billing remain controlled by
Groq; the app neither upgrades plans nor falls back to another provider.

The initial adapter sends only generated observation IDs, kinds and source tools
from at most 32 observations. It excludes request/message text, target addresses,
raw evidence and artifact download links. Only synthetic-fixture observations are
eligible. The model selects fixed review topics and valid observation IDs; server
templates render the explanation. This is not general natural-language answering,
scanner planning or vulnerability confirmation. Missing evidence/data-use/key or
budget produces a recorded error; no silent local fallback occurs in Groq mode.

Choose a nonzero model allowance when creating a new assessment (optional model
budget section); existing scopes require an explicit scope revision via the API.
Each Groq attempt reserves one call, a conservative input byte bound and the configured output-token cap (default 1024). Calls have a 12-second outer deadline, no retries and no tools. Unknown
usage retains its reservation; monetary cost remains unknown. The API holds no
transaction across inference and rejects stale output after state/scope changes.

Same-key requests replay the stored success or failure. A crash may leave a durable
pending reservation: do not blindly replay/reclaim it. A new explicit retry can
reference an owned completed decision, never an uncertain scanner execution.
Tests use synthetic data and fake transport; no real Groq quality, quota, latency
or billing claim is established without a separately configured provider run.

Groq format and current model/plan references: [Structured outputs](https://console.groq.com/docs/structured-outputs), [rate limits](https://console.groq.com/docs/rate-limits). Account-specific access is not established by these documents.

Use only `backend/.env` for this local checkout. Set `REKNYX_GROQ_API_KEY` there;
the application does not automatically load dotenv files. From `backend/`, load it
with `set -a; source .env; set +a` before starting the API.

Check setup without contacting Groq after loading the backend environment:

```bash
python -m reknyx.security_analysis.check_setup
```

Exit code 0 means local mode or Groq configuration is present, 1 means Groq setup
is incomplete, and 2 means backend configuration is invalid. This does not validate
the key, quota, account billing state or provider output. Settings → Evidence analysis
shows the same sanitized status; use Refresh after server configuration changes.

Configure the model request in `backend/.env`:

```bash
export REKNYX_GROQ_MODEL=openai/gpt-oss-120b
export REKNYX_GROQ_TEMPERATURE=0.1
export REKNYX_GROQ_REASONING_EFFORT=low
export REKNYX_GROQ_MAX_OUTPUT_TOKENS=1024
```

For an explicit light-model run, change `REKNYX_GROQ_MODEL` to
`openai/gpt-oss-20b`. Both choices use strict JSON Schema; no automatic model
fallback is performed. Temperature is bounded to 0–2, reasoning effort to
low/medium/high, and output tokens to 128–4096. Restart the API after editing.
Output limits must also fit the assessment's remaining model budget.
Evidence-reference checks and disabled direct execution are enforced invariants,
not optional flags. Automatic retries remain disabled; explicit new-intent retry
preserves attempt identity and budget accounting.

The prepared disposable setup now uses app and PostgreSQL runtime login
`admin`/`admin`; maintenance migrations use `postgres`/`admin`. Its existing database
names and artifacts are preserved. These credentials belong only to local testing.

## Review selection benchmark

From the repository root, run the frozen synthetic dataset offline:

```bash
backend/.venv/bin/python -m reknyx.security_analysis.evaluation --provider deterministic --split all --output eval-results/review-local-001.json
```

Choose a new output filename for each run. The CLI claims it before evaluation and
never overwrites an existing run. Reports include dataset/source/prompt/schema
hashes, provider/model options, case results, exact pass and coverage denominators,
validation rejection results, usage where known, and errors. A partial run reports
`complete=false`; attempted-case pass rate alone does not establish full coverage.
Exit codes are 0 for complete passing runs, 1 for failed/partial results, 2 for
setup/run failure, and 3 for result-publication failure. A reserved file left after
interruption requires reconciliation before repeating any provider calls.

For an explicitly authorized Groq comparison, load `backend/.env` and use the same
split and dataset with a bounded call allowance:

```bash
backend/.venv/bin/python -m reknyx.security_analysis.evaluation --provider groq --split development --allow-live --max-calls 8 --output eval-results/review-groq-001.json
```

This command sends up to eight synthetic cases; it is not part of default tests.
The key, confirmed free-plan flag and synthetic data-use flag must be configured.
There is no retry or automatic switch to the light model. Budget-limited cases
remain visibly not-run. Unknown usage and cost stay unknown. Run local review on
`--split development` for a comparison with the same eight cases; compare hashes
and case IDs before comparing results.

Dataset `review-selection-synthetic-v1.1` has 16 project-authored cases (8 development,
8 holdout) and 8 rejected-output cases under `tests/evals/`. Labels and partitions
are not independently adjudicated or a real-world generalization study. It scores
review-topic/reference selection, not vulnerability detection, calibrated risk,
remediation correctness or pentest success. No raw malicious instructions are sent:
privacy tests verify their exclusion; rejection cases test the local output validator.
Context v2 includes only generated IDs, kind/tool and normalized severity, transport,
port and historical status. Native captures, broader reasoning labels, real-provider
comparison and authorized scanner execution retain separate evidence gates.
