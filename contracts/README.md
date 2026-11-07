# Reknyx contract candidate 0.1.0

P1-01 delivers an executable contract with offline G0 verification. Frontend/backend
owner approvals are recorded under `admin` in [review-status.json](review-status.json)
against the exact OpenAPI SHA-256, alongside an exact-input gate attestation and
local evidence path. Foundation services are being implemented;
scanner execution, providers and PDF generation remain in development.

## Authority and files

[openapi.yaml](openapi.yaml) is the HTTP/schema authority: OpenAPI 3.1.2 with JSON
Schema 2020-12, `/api/v1`, 43 operations and strict bounded objects. It preserves
the existing draft inventory and adds these projections for the delivered UI:

- `GET /workspace/summary`, `/workspace/approvals`, `/workspace/findings`,
  `/workspace/reports`, `/workspace/timeline`: complete authorized aggregates or
  bounded lists. Totals never come from a partial client page.
- `GET /assessments/{assessment_id}/reports/{report_id}/snapshot`: the complete
  immutable snapshot used by report preview, independently of PDF readiness.

[route-map.json](route-map.json) maps every operation to current browser views;
browser URLs and API resource URLs are distinct. Existing `/`, `/assessments`,
`/approvals`, `/findings`, `/reports`, `/settings` and assessment child routes stay.
`/dashboard` continues to be the existing frontend redirect. There is no generic
`/jobs` or `/retry` endpoint: asynchronous operations return same-origin import,
execution or report status URLs; explicit plan retry carries a typed prior ID.

[generated/api.d.ts](generated/api.d.ts) is generated from this candidate and is
not a new authority. [tests/type-fixtures.ts](tests/type-fixtures.ts) compiles
synthetic positive fixtures for each component plus negative request/state cases.
No frontend source was changed or wired to these declarations. TypeScript cannot
enforce every JSON Schema bound or conditional: runtime validation remains required.

The examples are intentionally **synthetic contract fixtures**. They are not raw
native captures, parser results, observed vulnerabilities, model evaluation, HTTP
integration or permission to contact the documentation addresses used in them.

| Dataset | Purpose |
| --- | --- |
| [schema-cases.json](examples/schema-cases.json) | Valid example for each schema; invalid bounds, formats, extra fields and state combinations |
| [semantic-cases.json](examples/semantic-cases.json) | Structurally valid requests/records checked against synthetic canonical state: membership, references, revisions, profile/time/budget preconditions, replay and correlation |
| [http-cases.json](examples/http-cases.json) | Request/response examples covering every operation and distinct error outcomes; binary response entries describe media only |
| [priority-cases.json](examples/priority-cases.json) | Twelve labelled ordinal review comparisons |
| [hash-vectors.json](examples/hash-vectors.json) | Independent Python/JavaScript canonical bytes, hashes, normalization, mutations and rejection cases |

Hash vectors establish encoding and structural boundaries; contextual permission,
budget applicability and evidence checks are separately specified by semantic
cases. [HASHING.md](HASHING.md) defines the precise domain encoding and parser
limitations; it is not general RFC 8785/JCS.

## Run offline verification

Tested tooling: Python 3.13.13 and Node.js 22.23.2. Python tooling and its resolved
dependencies are pinned in [requirements.lock.txt](requirements.lock.txt); direct
dependencies are in [requirements.in](requirements.in). Contract-only Node tooling
uses [package.json](package.json) and its npm lockfile. These are not backend
runtime dependencies. Node must meet the package engine and dependency requirements.

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r contracts/requirements.lock.txt
npm --prefix contracts ci --ignore-scripts
.venv/bin/python scripts/validate_contracts.py
.venv/bin/python -m pytest contracts/tests -q
npm --prefix contracts run check:generated
npm --prefix contracts run check:types
npm --prefix contracts run check:hashes
```

To verify the complete offline G0 gate, including recorded owner approvals and all
five commands above, run `.venv/bin/python scripts/verify_g0.py`. Add `--record` to
atomically refresh the successful evidence in `review-status.json`. Any command
failure or changed input prevents recording success. Recorded results describe the
hashed inputs at the recorded time; rerun after changing those inputs. This command
keeps detailed command output under ignored `docs/implementation/evidence/g0/` and
retains only the portable gate attestation in the review ledger. It
does not certify actual HTTP integration or platform readiness. The standalone
validator deliberately reports pending final gate verification because it does not
run the complete gate.

Installation needs package-registry access. After installation, these checks use
local files/processes only, with no service startup, scanner or provider traffic.
The main validator performs full OpenAPI validation, schema validation with format
checks, valid/invalid example checks, semantic acceptance, complete route/HTTP
coverage, twelve priority expectations and both hash implementations. Remote
references and duplicate YAML/JSON members are rejected. Its output identifies the
candidate hash and keeps G0 pending final gate verification. Contract validation alone
does not imply backend, Compose or full-stack acceptance.

To regenerate declarations after a deliberate contract change:

```bash
npm --prefix contracts run generate
```

Update affected examples, type fixtures and route mapping in the same change;
refresh `review-status.json`'s candidate hash and obtain reviews against that hash.
Changing a contract does not update service implementations automatically.

## Session, authorization and errors

- Login is a JSON request with exact allowlisted `Origin`; passwords come from
  backend configuration, never frontend source. Server sessions use an opaque
  `HttpOnly; SameSite=Strict; Path=/api/v1` cookie, `Secure` outside loopback,
  rotation on login and an eight-hour absolute expiry without sliding renewal.
  Backend implementation must bound/rate-limit login attempts.
- All authenticated mutations require `X-CSRF-Token` and exact `Origin`. Session
  reads supply CSRF; responses use `Cache-Control: no-store`. Use one loopback
  hostname consistently. Logout revokes the server session and cookie; it needs
  CSRF but no idempotency key, and a retry after revocation is unauthenticated.
- Actor identity comes from the session. Current membership is checked for every
  read, write, workspace aggregate, snapshot and byte download; a foreign scoped
  resource returns 404 without disclosure. Live authorization references must be
  resolved against trusted registered scope; submitted identifiers are not ROE.
- Keep 401 session loss, 403 denial, 404 isolation, 409 conflicts/in-progress,
  413 size, 415 media, 422 input, 501 unimplemented and 503 dependency/runtime
  failures distinct. Error details are bounded typed fields with request IDs,
  never arbitrary payloads, secrets or stack traces. Capability `planned` displays
  **In development**; a connection failure remains an error.

## Revisions and replay

All authenticated domain mutations require `Idempotency-Key`; login/logout are
the explicit exceptions. The namespace is authenticated actor + assessment +
operation ID + path resource IDs + key. Assessment creation has no assessment ID
yet, so its namespace is actor + operation ID + key. Keys are 1–128 bounded ASCII
characters. Each field is independently bound; no cross-user key lookup.

The digest covers validated request data with exact string values; multipart
digests include the SHA-256 of original bytes, kind, provenance and source
metadata, excluding transport boundary and filename. JSON request serialization
uses sorted keys, compact separators and UTF-8 without Unicode normalization or
number/string coercion; duplicate JSON members and nonfinite numbers are invalid.
Authority fields additionally follow the stricter [hash rules](HASHING.md).

After session/CSRF/membership checks, a same-key/same-body completed request returns
the original status, body and Location **before** testing the original expected
revision again. A different body is 409 `idempotency_conflict`. An in-progress
duplicate is 409 `operation_in_progress` with stable resource/decision ID and
`Retry-After` of 1–60 seconds. Failures are recorded and replayed; reconnect never
silently causes another provider call, import, report or execution. Reservations
without a committed side effect may be reclaimed only after transactional proof
that none occurred. Completed identities remain for the assessment lifetime.

An approval decision binds the existing approval/action hash, scope version,
expiry and budget. Same-key replay returns its decision; a new decision under a
new key conflicts once decided. Review similarly binds expected finding revision,
actor and rationale. A new intent/body gets a new key. Explicit retry planning
references the prior decision/execution; an unknown execution first requires exact
attempt/fence/process/receipt reconciliation and never an automatic scan replay.

Messages are append-only. Each analyst append conservatively increments assessment
state revision and stales old intent; the initial request stays preserved. Appending
does not invoke inference. Explicit synchronous planning reserves identity/budget
before a bounded provider call, holds no DB transaction across it, then compares
state/scope revision before accepting a proposal. Ask/stop/inconclusive/denied/failed
outcomes have no dispatchable proposal. Failed attempts and deterministic source
labels remain visible; there is no silent provider switch.

## Evidence, findings and priorities

Live target scope is one dedicated IPv4 with 1–16 explicit TCP ports and exact
hostname aliases. Exclusions take precedence. ZAP needs origin-wide authorization
at `/` and matching same-assessment HTTP service evidence within the current scope
window; a port number alone is insufficient. Its profile owns AF-only flags and
loopback port 8090. Unsupported options/path scope/legacy fallback remain denied.
The Nmap profile remains bounded discovery; service observations alone do not
create vulnerability findings. Profile deadlines are 120/180 seconds respectively;
an action's reserved runtime matches its requested deadline in semantic cases.

Historical imported IPv6, UDP, hostname or unknown identities are preserved without
becoming live scope. Original bytes are stored before parsing, capped at 20 MiB;
parsers have depth 64, 10,000 records and a 10-second isolated wall budget. Native
parsers allocate no canonical IDs: persistence binds their records to the verified
source manifest/assessment and retains raw locators/hash/parser version/timestamps.

Findings retain observation memberships, compatible asset/service/location/time/rule
meaning and correlation rationale. Same title/CVE does not prove compatibility.
Source CVSS score/vector/version/source and confidence method/raw value remain
distinct from contextual priority. Known exposure/exploitability/impact needs source
observation IDs or attributed analyst rationale; unknown stays unknown. Confirmation
needs an attributed method and evidence, independently of analyst disposition.

`ordinal-v1` assigns `review_first` for high/critical severity, demonstrated
exploitation, or medium severity on a reachable high-impact asset. Low/informational
with all three context inputs known is `routine`; all other cases are `review_next`.
Low confidence never automatically downgrades impact/severity. Stable finding order
is priority (`review_first`, `review_next`, `routine`), severity (`critical`, `high`,
`medium`, `low`, `informational`, `unknown`), then canonical UUID ascending. Conflicting
sources remain attributed; use the highest supported source severity as conservative
review ordering, retain all source values and flag the conflict/unknowns. This is
an ordinal queue, not an invented numerical risk score or calibrated probability.

## Internal transaction seams and reports

Internal data schemas in OpenAPI are not additional HTTP endpoints. Their callers
use trusted actor/worker/launcher context, never an actor field from the browser:

| Interface | Data and responsibility |
| --- | --- |
| `get_session`, `require_analyst` | Infrastructure validates session/expiry; returns trusted Session/Actor |
| `append_event(AuditEventInput)` | Domain transaction includes mutation and attributed TimelineEvent atomically |
| `get_snapshot(assessment_id)` | Assessment service returns consistent authorized AssessmentSnapshot |
| `append_message(assessment_id, expected_revision, input)` | Assessment transaction reserves replay identity, appends once and increments revision |
| `put_bytes(assessment_id, bytes, ArtifactInput)` | Evidence service computes manifest/hash/private locator; filesystem/DB gaps retain reconciliation diagnostics |
| `read_bytes(assessment_id, artifact_id)` | Membership and integrity check before private bytes; no client filesystem paths |
| `parse(bytes, SourceMetadata)` | Pure native parsing to ParsedBatch; no network/DB/authority |
| `ingest_observations(ParsedBatch)` | One persistence owner validates source/assessment and allocates canonical observation IDs |
| `correlate(assessment_id, observation_ids)` | Findings transaction validates references and preserves memberships/review history |
| `authorize_dispatch(action_id, attempt_id)` | Locks assessment → action → approval/grant → budget → attempt; transaction reserves DispatchPermit and audit |
| `authorize_start(StartAuthorizationRequest)` | Trusted launcher rechecks after preparation, same serialization order; consumes exact grant and returns StartAuthorization |
| `create_snapshot(assessment_id, expected_revision)` | Reporting transaction freezes one immutable consistent ReportSnapshot and queues report job |
| `render_pdf(ReportSnapshot)` | Bounded renderer reads frozen data only; no scanner or remote fetch; returns bytes for evidence publication |

Service failures map to the documented typed Error codes. No transaction spans
scanner, parser, renderer or provider IO. Start authorization is a logical fence,
not an atomic DB/process-start or immediate physical revocation guarantee. Runtime
roles, restricted launcher DB functions and egress enforcement still need actual
implementation and separate allow/deny/recovery evidence.

Import/report jobs use the same PostgreSQL worker infrastructure and never consume
scanner grants. Public execution `running` needs a scanner-start receipt; generic
job `running` can include preparation. Import `partial`, report `failed`, approval
`granted`, finding validation and analyst disposition remain independent states.

Reports render an immutable snapshot containing PDF sections 7.1–7.6: executive
scope; methodology/ROE/tool summary; severity/priorities; detailed findings/evidence;
impact/remediation; limitations/assumptions/failures/approvals/timestamps. Snapshot
size is at most 10 MiB; render budget is 30 seconds/512 MiB. Artifact publication
is bounded at 20 MiB. Renderer failure retains the snapshot and never becomes ready.
Old report reads/downloads use stored bytes and retain their hash after later edits.
An attributed client-release review is a separate later capability: ready PDFs stay
draft until that review exists. No release mutation endpoint is enabled in P1-01.

## Review and next gate

The FE/BE review covers G0-W1 workspace projections, W2 snapshot
preview, W3 retry/status URLs, W4 DTO mapping and W5 session/replay semantics against
the delivered UI. Review this candidate hash, strict fields/nullability/limits,
typed errors and independent state machines; record actual reviewer/time/hash.
Generated consumer checks and an independent coding-agent review do not replace
the user-appointed frontend/backend owners' acceptance. Admin has approved both
roles; the complete offline G0 verification is recorded separately from actual frontend HTTP integration, native parsing,
model evaluation, live execution, PDF release and pilot gates remain open.

Requirement review used the ten-page local `1.pdf`, SHA-256
`cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.
The PDF is optional local source material, not a dependency of these checks.

Primary tooling references: [OpenAPI 3.1.2](https://spec.openapis.org/oas/v3.1.2.html),
[JSON Schema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/),
[OpenAPI validator](https://openapi-spec-validator.readthedocs.io/en/latest/) and
[openapi-typescript](https://openapi-ts.dev/cli).
