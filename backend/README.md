# Reknyx backend foundation

This backend provides the initial session, assessment, message, audit and private
artifact services, durable Nmap/ZAP/Greenbone imports, finding review and immutable draft PDF reports.
Scanner execution remains in development. Analyst evidence correlation and the contract's ordinal review-priority rules are implemented. Explicit evidence review and a bounded synthetic Groq development benchmark are implemented; broader AI acceptance remains pending. G0 verification is recorded in
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

## Exact-capture repeat imports

Migration `0004_finding_capture_keys` adds an immutable same-assessment capture
index. Apply `alembic upgrade head` with the migration-owner connection before
starting the updated API and worker, following the setup command above. Readiness
requires this revision. Migration checks were run only on an isolated test database;
existing application databases are not automatically upgraded by source edits.

Newly indexed imports of the exact same native record share a canonical finding.
Identity binds the assessment, original byte hash, parser version, native rule and
locator, asset/service/request location, recorded observation time and provenance.
Generated IDs, source labels and ingestion times do not change capture identity.
Changing bytes, parser version, time, provenance or assessment creates a separate
finding; similarity of title or CVE is never sufficient. This is exact-capture
duplicate handling, not cross-tool equivalence or general issue deduplication.

Every repeated import still retains its own artifact, native observation and raw
locator. Existing finding memberships gain the new observation, the finding revision
advances, and worker audit records identify the attachment. Original source fields,
analyst disposition, technical validation and reviews are preserved: replaying the
same capture is not new supporting proof. Old snapshots stay frozen. New reports
disclose the limited deduplication policy and retain all source traces.

Any previous `keep_separate` review on the indexed finding vetoes automatic
attachment to that finding. This conservative veto applies even when that review
concerned another observation; use explicit analyst review for further links.
The index remains unchanged and the repeated source gets a separate finding.
Publication is atomic: if a membership/trace bound is exceeded, the import visibly
fails without partial observations, finding changes or duplicate-link audit events;
its original stored bytes remain accessible. No automatic retry occurs.

Existing findings are not backfilled or retroactively merged by this migration.
The first post-upgrade import establishes a new index entry, so older duplicate
finding records may remain. No cross-tool mapping is enabled; Greenbone's current
normalized records do not retain the exact web request location needed to claim
equivalence with a ZAP instance. Native-capture acceptance remains a separate gate.

## Analyst correlation and review priority

`POST /api/v1/assessments/{id}/correlations/review` accepts the existing
`CorrelationReview` contract. Use an authenticated cookie, exact configured Origin,
CSRF token and a fresh idempotency key, as for finding review:

```json
{
  "finding_id": "<finding UUID>",
  "observation_ids": ["<candidate observation UUID>"],
  "decision": "link",
  "expected_revision": 1,
  "rationale": "Explain why the retained source observations describe the same issue."
}
```

Get IDs from the assessment's findings and observations lists; `expected_revision`
is the finding revision. This example's UUID placeholders must be replaced.
Success returns an attributed immutable `ReviewRecord` and advances finding and
assessment revisions. Same-key requests replay the stored success or denial.

Links require same-assessment vulnerability observations with matching canonical
asset, known service endpoint, exact web request location, native tool/rule and
recorded capture time. No timestamp tolerance or hostname/IP alias is inferred.
When capture time is missing, only identical retained capture bytes are compatible.
Different queries, methods, parameters, redacted locations, unknown endpoints,
different rules or incompatible provenance are refused. Titles, CVEs and analyst
rationale alone cannot supply compatibility. Cross-tool linking is refused until
reviewed rule-equivalence mappings exist; no such mapping is enabled in this release.

Use `decision: "keep_separate"` to record a negative review for other owned
observations. It preserves memberships and source fields; it cannot unlink existing
members. A later different decision requires a fresh key and current finding revision.
Newly linked evidence returns disposition to `needs_review` without promoting
technical validation. Original observations, native values, artifacts and other
source findings remain unchanged. Links do not delete or deduplicate source findings;
reports explicitly distinguish canonical finding counts from deduplicated issue counts.

New imports attribute source severity and supported CVSS separately. Linking uses
the highest supported source severity for conservative review ordering, flags
disagreements/unknown severity, and preserves the original primary CVSS, confidence
and remediation. Inspect all source artifacts; an aggregate severity is not technical
confirmation. Existing records are not rewritten in bulk.

The frozen `ordinal-v1` rule assigns `review_first` to high/critical severity,
recorded demonstrated exploitation, or medium severity on a recorded reachable,
high-impact asset. Low/informational severity with all three context inputs known
is `routine`; otherwise it is `review_next`. Confidence never discounts severity.
Exposure, exploitability and asset impact remain unknown unless supported separately.
This is an explainable review queue, not a numeric risk score or probability.
Report snapshots freeze their original memberships, priorities and review history.

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

The adapter sends only generated observation IDs, kinds, source tools and normalized
severity/transport/port/historical facts
from at most 32 observations. It excludes request/message text, target addresses,
raw evidence and artifact download links. Only synthetic-fixture observations are
eligible. The model selects fixed review topics and valid observation IDs; server
templates render the explanation. This is not general natural-language answering,
scanner planning or vulnerability confirmation. Missing evidence/data-use/key or
budget produces a recorded error; no silent local fallback occurs in Groq mode.

Review output v3 applies the `review-coverage-v1` checklist independently of the
provider. Existing observations require source review; vulnerability candidates
require analyst remediation review and a supporting vulnerability citation;
unknown-severity candidates also require uncertainty review and a supporting
unknown-severity citation. Empty context requests evidence and scope clarification.
This is minimum checklist coverage, not autonomous vulnerability reasoning or
technical confirmation. Models may select a supported subset of references; it is
not proof that every imported observation was reviewed. Truncated context remains
explicitly limited to the supplied observations.

Omitted required topics or supporting references fail the analysis. Attempts retain
an application-owned `validation_failure_code`, provider status, output hash and
reported usage; no assistant message or repaired output is substituted. Prompt,
schema and selection-policy versions identify new attempts and evaluation reports.
Historical decisions and same-key replays retain their original output and versions.
The v2 prompt, frozen dataset and original run files are preserved. A new prompt
requires a separately authorized live run before claiming improved Groq results.

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
port and historical status. The first development-only live comparison used v2
review rules; those results do not evaluate the v3 prompt/coverage policy. Native
captures, broader reasoning labels, holdout provider evaluation and authorized
scanner execution retain separate evidence gates.

Compare two compatible run reports without making provider requests:

```bash
backend/.venv/bin/python -m reknyx.security_analysis.compare_evaluations --baseline eval-results/review-local-001.json --candidate eval-results/review-groq-001.json --output eval-results/review-comparison-001.json
```

Use the same split for both runs. The tool rejects mismatched dataset, algorithm,
context, prompt, schema or selection-policy identity, different case selections, duplicate cases and
inconsistent counters. It reports paired improvements/regressions and not-comparable
cases. Comparison exit code 0 means a valid comparison file was written, not that
the candidate passed a quality gate. It does not authenticate how input runs were
executed or infer significance from a small synthetic sample. No provider calls,
retries, report overwrites or changes to the frozen labels are performed.

## CI and disposable container verification

[CI](../.github/workflows/ci.yml) runs contract verification, frontend unit/type/build
and preview browser checks, then a disposable container integration lane. Actions
are pinned by SHA, repository permission is read-only, and dependencies are locked.
The workflow does not publish images, deploy, call providers or execute scanners.
Hosted CI results require an actual GitHub workflow run.

For the same container lane locally, start Docker Engine/Compose and install
`pdftotext` (the `poppler-utils` package on Debian/Ubuntu). From the repository root:

```bash
uv sync --project backend --frozen
npm --prefix frontend ci
cd frontend
npx playwright install chromium
cd ..
bash scripts/ci/compose-check.sh
```

The runner generates a unique project, private temporary credentials and loopback
ports. It builds real images, migrates a fresh PostgreSQL volume, runs backend tests
with the non-owner login, then starts API/worker/frontend. The browser imports
synthetic ZAP/Greenbone evidence, reviews findings and downloads PDFs. A final check
compares downloaded report/source hashes before and after a clean database and
application restart. This does not prove crash recovery, backup/restore, native
captures, real-provider quality or live-scanner acceptance.

Cleanup removes only that invocation's containers/networks/volumes. Generated images
and build cache remain; do not prune unrelated resources. If Docker becomes
unavailable, the private temporary configuration is retained; reconcile the printed
`reknyx-ci-...` project with that env-file after Docker returns, then remove the
temporary directory only after its resources are gone. Browser
traces can contain generated credentials and are not uploaded by the workflow.
Never target an existing user database or persistent staging account with this lane.

## Vultr staging preparation

[`deploy/staging/compose.yml`](../deploy/staging/compose.yml) is an independent,
image-only deployment for the current single-account import/review/draft-PDF flow.
It is separate from the future scanner sandbox. API/worker use deterministic review
on internal networks without provider keys. Only Caddy publishes TCP 80/443; DB/API
have no host ports. Application processes use non-root read-only filesystems, bounded
tmpfs and memory limits. These are initial limits, not measured capacity or proof of
scanner containment.

Prepare a dedicated staging VM with Docker/Compose, a DNS name pointing to it and
private operator access. Firewall/access configuration is an explicit operator task.
Caddy needs working DNS and ACME connectivity to obtain certificates. Build backend
with `backend/Dockerfile` and frontend with `frontend/Dockerfile`, API mode and fixed
backend origin `http://api:8000` at build and startup. Publishing images is a separate
release action: the current CI has no registry write credentials. Promote the tested
images by digest; also pin reviewed PostgreSQL **17** and Caddy **2** images by digest.
Do not change the database major version as an incidental deployment update.

From the repository root on the staging host:

```bash
umask 077
cp deploy/staging/.env.example deploy/staging/.env
chmod 600 deploy/staging/.env
```

Fill every required field privately. DB passwords must be distinct random values
of at least 24 characters and URL-encoded in connection URLs. The initial DB creates
`reknyx_app`; API/worker use that login. Generate the scrypt hash through
`reknyx.infrastructure.auth.hash_password` in a private setup process; single-quote
the whole hash in `.env` to preserve dollar signs. Do not print resolved Compose
configuration or put secrets in shell history. Local `backend/.env` is not staging
configuration. Before starting anything:

```bash
python3 scripts/check_staging.py --env-file deploy/staging/.env
```

The read-only preflight checks resolved digest references, HTTPS origin, credentials,
network/volume boundaries and disabled inference. It prints no resolved secrets and
makes no provider, registry or cloud request. It does not inspect image contents or
verify registry access, image versions, DNS/TLS, host egress, DB privileges or runtime
readiness. Exported shell variables override `.env`; remove stale local overrides
before checking and deploying.

After operator review, use the same project name and env-file for every operation:

```bash
stage() {
  docker compose --project-name reknyx-staging --env-file deploy/staging/.env \
    -f deploy/staging/compose.yml "$@"
}
stage pull
stage up --detach
stage ps --all
```

Confirm migration exit zero, healthy API and working TLS. Sign in and manually import
an explicitly labelled synthetic fixture, review it, download the stored draft PDF,
then compare evidence/PDF hashes after a controlled restart. A health endpoint alone
does not establish workflow acceptance. Do not automatically run the disposable
browser suite against persistent staging data.

For updates, stop admission through proxy/frontend/API, then stop the worker with its
grace period. Inspect durable jobs and publication receipts before changing unresolved
`parsing`/`rendering` state. No automatic drain/recovery endpoint exists; a graceful
stop allowance does not prove completion. Serialize migrations under the owner login
and restart from reviewed digests. Do not blindly rerun uncertain work. Application
rollback requires DB compatibility; do not automatically downgrade Alembic.

DB, evidence and Caddy state persist in named volumes. Never use `down --volumes` on
staging. Initial provisioning applies only to fresh DB volumes; env edits do not
rotate existing DB credentials. Consistent DB/artifact backups, tested restore,
retention/access review, diagnostics and measured load remain separate pilot gates.
Vultr deployment, TLS and registry promotion need actual run evidence; these files
and preflight establish configuration preparation only.
