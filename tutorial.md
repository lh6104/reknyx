# Reknyx API tutorial

This guide describes the current local Phase 1 API. It uses synthetic evidence and a disposable test database. The API is an import and review workflow; it does not run scanners. Explicit evidence review supports local rules and an optional Groq adapter. A recorded scope or a sample IP address does not grant permission to scan.

## Start and inspect the API

For the already-prepared disposable setup, start PostgreSQL, the API, and the worker as described in [backend setup](backend/README.md). The local API used in this guide is `http://127.0.0.1:18080`; replace the port if your setup differs. The frontend runs at `http://localhost:3100`.

To enable the API reference, set `REKNYX_ENABLE_API_DOCS=true` in the API process environment before starting it. Open [Swagger UI](http://127.0.0.1:18080/docs). It loads JavaScript and CSS from a CDN. The complete reviewed contract is [contracts/openapi.yaml](contracts/openapi.yaml). The contract includes planned endpoints: the presence of an operation in Swagger does not mean it is implemented. Check `/api/v1/capabilities` after logging in.

```bash
curl -sS http://127.0.0.1:18080/api/v1/health/live
curl -sS http://127.0.0.1:18080/api/v1/health/ready
```

Liveness checks the process. Readiness checks the database and migrations; neither proves that a scanner or model is available.

## Sign in and make requests

Use the configured local account (username `admin` in the disposable setup). Enter its current password when prompted; passwords are not stored in this tutorial. The following Bash commands store the session cookie in a private temporary directory. Run them in the same terminal; `python3` and `curl` are required.

```bash
umask 077
REKNYX_TEST_DIR=$(mktemp -d)
REKNYX_API=http://127.0.0.1:18080/api/v1
REKNYX_ORIGIN=http://localhost:3100
python3 -c 'import getpass,json; print(json.dumps({"username":"admin","password":getpass.getpass("Password: ")}))' | \
curl -sS -c "$REKNYX_TEST_DIR/cookies" \
  -H "Origin: $REKNYX_ORIGIN" -H 'Content-Type: application/json' \
  --data-binary @- \
  "$REKNYX_API/auth/login" > "$REKNYX_TEST_DIR/session.json"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("Signed in:", d["actor"]["display_name"])' "$REKNYX_TEST_DIR/session.json"
REKNYX_CSRF=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["csrf_token"])' "$REKNYX_TEST_DIR/session.json")
curl -sS -b "$REKNYX_TEST_DIR/cookies" "$REKNYX_API/auth/me"
curl -sS -b "$REKNYX_TEST_DIR/cookies" "$REKNYX_API/capabilities"
```

The configured origin must match **exactly**, including hostname and port; `127.0.0.1:3100` and `localhost:3100` are different origins. All mutations require the `Origin` header; after login they also require the session's `X-CSRF-Token`. Most domain mutations require a unique `Idempotency-Key`: use a fresh key for each new operation, and reuse it with the exact same request when intentionally retrying that operation. The session expires after eight hours. Swagger opened on the API origin cannot bypass origin or CSRF checks, so use the commands below or the frontend for mutations.

## API endpoint map

All paths below are relative to `/api/v1`. The schema and exact fields are in the contract and Swagger page.

| Purpose | Method and path | What it does |
| --- | --- | --- |
| Health | `GET /health/live`, `GET /health/ready` | Check process and database/migrations. |
| Session | `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` | Start, inspect, and revoke the cookie session. |
| Capabilities | `GET /capabilities` | Report available versus planned functions. |
| Workspace | `GET /workspace/summary`, `/workspace/findings`, `/workspace/reports`, `/workspace/timeline`, `/workspace/approvals` | Read authorized cross-assessment projections. Approval lists are empty in this phase. |
| Assessments | `POST /assessments`, `GET /assessments`, `GET /assessments/{id}` | Create and retrieve persisted assessment records. |
| Scope and request | `PUT /assessments/{id}/scope`, `PUT /assessments/{id}/request` | Update using the expected version/revision. |
| Conversation | `GET` and `POST /assessments/{id}/messages` | Read or append messages. Appending does not invoke a model. |
| Imports | `POST /assessments/{id}/imports`, `GET /assessments/{id}/imports/{import_id}` | Upload original Nmap XML, traditional ZAP JSON or Greenbone XML and poll the worker. |
| Evidence | `GET /assessments/{id}/observations`, `/artifacts`, `/artifacts/{artifact_id}`, `/artifacts/{artifact_id}/download` | Inspect observations, metadata, hashes and original bytes. |
| Findings | `GET /assessments/{id}/findings`, `/findings/{finding_id}`; `POST /findings/{finding_id}/review` | Read and review findings; disposition is separate from technical validation. |
| Reports | `POST` and `GET /assessments/{id}/reports`; `GET /reports/{report_id}`, `/reports/{report_id}/snapshot`, `/reports/{report_id}/download` | Freeze a snapshot, poll rendering, inspect it and download the ready PDF. |
| Audit | `GET /assessments/{id}/timeline` | Read the assessment's recorded events. |

For the shortened evidence, finding, and report paths in the table, retain the `/assessments/{id}` prefix. Lists return `items` and `next_cursor`; use `limit` and `cursor` to read subsequent pages. Reads and downloads enforce assessment ownership.

Explicit evidence review is available. Live provider evaluation, executable scan planning, scanner execution, and approval decisions remain in development. Planned calls may return HTTP 501. A draft PDF is not automatically a client-ready assessment.

## Try the full synthetic workflow

1. Sign in to `http://localhost:3100` with the disposable account. Create an assessment with a synthetic IPv4 `192.0.2.10`, TCP ports `80,443`, authorization reference `00000000-0000-4000-8000-000000000012`, and a valid time window. This records scope only and authorizes no traffic.
2. Append a message. It is persisted without invoking AI.
3. In the assessment, upload `/tmp/reknyx-phase1-synthetic-zap.json` as `zap_json`, with provenance `synthetic_fixture` and a source label. Wait for `succeeded`; the separately running worker must process the job.
4. Open Findings. Inspect the evidence and original download, then save an analyst disposition with a rationale. A suspected finding remains technically suspected after acceptance.
5. Open Report, include suspected findings, create the report, wait for `ready`, inspect the frozen snapshot, and download the PDF. Reload to confirm persistence.

For direct calls, start with the assessment list:

```bash
curl -sS -b "$REKNYX_TEST_DIR/cookies" "$REKNYX_API/assessments?limit=20"
```

Replace `ASSESSMENT_ID` below with an ID from the response. Fetch the current `state_revision` from `assessment`, then use it as `expected_revision`; create a new idempotency key for each new message.

```bash
REKNYX_ASSESSMENT_ID=ASSESSMENT_ID
curl -sS -b "$REKNYX_TEST_DIR/cookies" "$REKNYX_API/assessments/$REKNYX_ASSESSMENT_ID"
REKNYX_KEY=$(python3 -c 'import uuid; print(uuid.uuid4())')
curl -sS -b "$REKNYX_TEST_DIR/cookies" \
  -H "Origin: $REKNYX_ORIGIN" -H "X-CSRF-Token: $REKNYX_CSRF" \
  -H "Idempotency-Key: $REKNYX_KEY" -H 'Content-Type: application/json' \
  -d '{"expected_revision":1,"content":"Synthetic API tutorial message"}' \
  "$REKNYX_API/assessments/$REKNYX_ASSESSMENT_ID/messages"
```

Change `expected_revision` to the actual current value. A stale revision produces a conflict. For upload/review/report request fields and HTTP status responses, expand the corresponding operation in Swagger or consult the contract. An accepted import or report returns `status_url`: poll it until it reaches a terminal state instead of assuming the result is ready.

To end the session:

```bash
curl -sS -b "$REKNYX_TEST_DIR/cookies" -X POST \
  -H "Origin: $REKNYX_ORIGIN" -H "X-CSRF-Token: $REKNYX_CSRF" \
  "$REKNYX_API/auth/logout"
```

The cookie and session response in `$REKNYX_TEST_DIR` are sensitive; delete that temporary directory when you no longer need it.

## Troubleshooting

- **404 on `/docs`**: enable `REKNYX_ENABLE_API_DOCS=true` in the API process and restart it. Confirm the API port.
- **403 exact configured Origin**: use the exact origin configured in `REKNYX_ALLOWED_ORIGINS`; check the CSRF header for authenticated mutations.
- **401**: check the credentials or sign in again if the session expired.
- **409**: refresh the current revision or inspect the idempotency/retry response before retrying.
- **422**: compare the body and headers with the contract, including UUID format and UTC timestamps.
- **501**: the requested capability is still in development.
- **Import/report stays queued**: verify the worker is running against the same database and artifact root; do not blindly replay work whose outcome is uncertain.
- **503 readiness**: inspect the local PostgreSQL connection and migration state; do not reset the database or its volume.

## Test Greenbone import

Use `backend/tests/fixtures/greenbone/synthetic-report.xml` in the import form,
select **Greenbone XML**, and declare `synthetic_fixture` provenance. This file is
project-authored synthetic evidence, not a scanner capture. Follow the same
import → review → report steps above. The synthetic result retains its OID,
QoD and source CVSS fields, and stays suspected after analyst acceptance.
Only one completed report is supported per upload. Live Greenbone scanning is
not implemented; this operation imports previously recorded bytes only.

## Settings in API mode

Settings follows the prototype's Analyst and report, Assessment defaults, Safety,
and Tool integrations sections. Nmap, OWASP ZAP and Greenbone show **Import-only**
when the server reports their import capabilities available. Disabled checkboxes
are status indicators; they do not enable scans or grant authorization. Refresh
Settings to fetch current server capabilities.

You can save the default TCP ports, whether to include suspected findings in new
report forms, and the display theme. These non-sensitive preferences are saved in
this browser under `reknyx.api.preferences.v1`. Existing scope and report snapshots
are unaffected. Analyst identity is supplied by the authenticated server session.
Rate limits, execution deadlines, audit customization and approval configuration
remain in development. Reset preferences restores browser defaults only.

## Ask Agents and evidence review

Open an assessment and click **Ask Agents → Review evidence**, or use the
**Review evidence** button in Conversation. Local mode returns a decision and
assistant message labelled `deterministic`; it performs no model call. The source,
limitations and decision revision remain visible. Appending a message only saves it.

For direct API use, `POST /assessments/{id}/plans` requires the same cookie, Origin,
CSRF and idempotency headers as other mutations, with body
`{"expected_revision":CURRENT_REVISION,"retry":null}`. Success returns a
`PlanResult` containing `decision` and `proposal:null`. Read the current revision
before a new request. Read history through `GET /assessments/{id}/decisions`.
Same-key replay returns the stored result; it does not call the provider again.

For Groq, follow [backend provider setup](backend/README.md#explicit-evidence-review-and-groq-setup).
Use your free-plan account and keep the API key in private server configuration.
Only synthetic structural evidence is eligible for this first adapter. Model
budget defaults to zero; choose an explicit allowance on new assessment creation
before requesting Groq review. Provider failures are errors, not successful local
fallbacks. The adapter does not accept arbitrary tools or executable proposals.

Settings → **Evidence analysis** displays the configured review mode and any missing
Groq setup requirement. The operator can also run
`python -m reknyx.security_analysis.check_setup` in the configured backend environment.
This offline command never sends a request or prints the API key. A configured
status does not mean the key or live provider has been verified.

Groq model selection is configured in `backend/.env` using `REKNYX_GROQ_MODEL`
(default `openai/gpt-oss-120b`). Set it explicitly to `openai/gpt-oss-20b` for a
light-model run. Temperature, reasoning effort and output-token limit use
`REKNYX_GROQ_TEMPERATURE`, `REKNYX_GROQ_REASONING_EFFORT` and
`REKNYX_GROQ_MAX_OUTPUT_TOKENS`. Restart after edits. Strict schemas, evidence
references and disabled direct execution remain enforced; retries and model
switching never occur automatically.

## Benchmark the review algorithm

Use the [backend benchmark instructions](backend/README.md#review-selection-benchmark).
Start with the deterministic run; it makes zero provider requests. Compare Groq on
the same frozen dataset and split only after authorizing a live run and its call
budget. Inspect per-case failures, coverage and validation results, not only the
pass fraction. Synthetic review-selection scores do not measure pentest success.
