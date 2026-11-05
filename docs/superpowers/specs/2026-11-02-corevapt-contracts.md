# CoreVAPT — contract v0 for parallel work

Status: **design contract**, not executable OpenAPI. At G0, the contract owner must produce `contracts/openapi.yaml`, fixtures, and shared DTOs, and verify mappings before marking the contract frozen. Later changes require a version, FE/BE impact notes, and fixture updates in the same change.

## 1. Conventions

Base `/api/v1`; UTF-8 JSON; UUID string IDs; UTC ISO-8601 timestamps; monotonically increasing integer revisions; lowercase hexadecimal SHA-256 hashes. Lists return `{items: [], next_cursor: null}` with bounded pagination. Errors return `{error: {code, message, details, request_id}}`, without stack traces/secrets. Status codes: `401` unauthenticated; `403` unauthorized or policy denied; `404` missing or outside the assessment; `409` stale revision/hash or idempotency conflict; `413` oversized; `415` unsupported format; `422` invalid data; `503` temporarily unavailable dependency/capability. A directly called planned endpoint returns `501 capability_not_implemented`; an unsupported profile returns `422 unsupported_profile`, never silent success.

Local authentication: HttpOnly SameSite=Strict session cookie, credentials from backend configuration, CSRF token for mutations, origin allowlist, and HTTPS when exposed beyond localhost. Health/login are public; capabilities and domain endpoints require a session. Derive the actor from that session. Never embed a password/key in the frontend. Every query checks assessment membership, including artifact downloads, conversations, and report snapshots.

Asynchronous import/execution/report creation returns `202 {job_id, resource_id, status_url}`. `Idempotency-Key` is required for all three groups: the same actor+assessment+operation+key+body returns the same job; a different body returns 409. Request idempotency differs from job claims/leases. Approval is an action-bound decision and does not create an execution directly. Report jobs use the existing PostgreSQL-backed worker queue; no report-specific scanner process, broker, or second orchestration runtime is required.

## 2. Minimum UI DTOs

| DTO | Required fields |
| --- | --- |
| Assessment | id, name, request, scope_version, state_revision, status, created_at |
| Scope | assessment_id, version, authorization_ref, allowed_hosts, allowed_ips, allowed_ports, exclusions, allowed_profiles, valid_from, valid_until, budget, hash |
| ConversationMessage | id, assessment_id, role, content, created_at, actor_id nullable for assistant/system, state_revision, basis_observation_ids, proposal_ids, source, limitations |
| DecisionRecord | id, assessment_id, state_revision, scope_version, created_at, source, candidate_profile nullable, basis_observation_ids, proposal_id nullable, rationale, policy_result nullable, budget_remaining, outcome |
| Job | id, assessment_id, kind, resource_id, state, attempt_id nullable, created_at, started_at nullable, finished_at nullable, failure_code nullable |
| ActionProposal | id, assessment_id, state_revision, scope_version, profile, targets, parameters, basis_observation_ids, rationale, expected_evidence, done_when, action_hash, policy_result, expires_at |
| Approval | id, action_id, action_hash, scope_version, status, actor_id nullable before decision, rationale nullable, decided_at nullable, expires_at |
| Execution | id, assessment_id, action_id, attempt_id, state, started_at nullable, finished_at nullable, receipt_id nullable, artifact_ids, failure_code nullable |
| Artifact | id, assessment_id, source, sha256, size_bytes, content_type, observed_at nullable, ingested_at, parser_version nullable, historical, download_url |
| Observation | id, assessment_id, execution_id nullable for import, artifact_id, raw_locator, kind, source_tool, native_id, asset, service nullable, location nullable, raw_severity nullable, raw_confidence nullable, observed_at nullable, ingested_at |
| Finding | id, assessment_id, revision, title, asset, location nullable, severity, cvss nullable, cvss_vector nullable, cvss_version nullable, cvss_source nullable, cve_ids, cwe_ids, confidence_method, confidence_value nullable, validation_status, analyst_disposition, observation_ids, correlation_reason, exposure, exploitability, asset_impact, risk_input_sources, priority, priority_reasons, risk_rule_version, unknowns, remediation |
| Report | id, assessment_id, snapshot_id, created_at, state, artifact_id nullable, failure_code nullable |
| TimelineEvent | id, assessment_id, at, actor_type, actor_id nullable, kind, resource_id, reason, outcome |

Enums: `policy_result=permit|require_approval|deny`; execution `queued|running|succeeded|partial|failed|timed_out|cancelled|execution_unknown`; validation `observed|suspected|confirmed|rejected|needs_review`; analyst_disposition `needs_review|accepted|rejected`; severity `critical|high|medium|low|informational|unknown`. Validation status does not indicate execution success. Scope budget contains `max_actions`, `max_runtime_seconds`, `max_model_calls`, `max_input_tokens`, and `max_output_tokens`; enforce monetary limits only when provider pricing is verified/configured.

At G0, define typed schemas for `targets`, `parameters`, `asset`, `service`, and `priority`; arbitrary JSON must not remain scanner input. Catalog profiles are only `nmap_discovery_v1` and `zap_baseline_v1`; import kinds are `nmap_xml|zap_json|greenbone_xml`. ZAP evidence requires an HTTP service basis; Nmap discovery may have no basis if policy permits. The server computes the canonical action hash from tool/profile version, normalized target/parameters, scope hash/version, basis IDs, expiry, and budget. The client does not choose the hash.

Risk fields `exposure`, `exploitability`, and `asset_impact` use typed known/unknown values with source observation IDs or an attributed analyst rationale. Preserve source CVSS score, vector, version, and source independently of contextual priority. `risk_input_sources` records provenance for severity/CVSS and every non-unknown input; `risk_rule_version` identifies the deterministic ranking rule. A missing input remains unknown. No model-generated CVE, proof, or unsupported numeric score is accepted. Define concrete enum values and ranking/nullability behavior in G0 fixtures before implementing the rule.

Generic job kinds are `scan|import|report`. Freeze generic job lifecycle separately from execution/report lifecycles at G0; each job links its domain resource and never substitutes its state for that resource's outcome. `DecisionRecord` preserves proposed, denied, stopped, inconclusive, and failed next-step reasoning independently of displayed chat; evidence and proposal links must belong to its assessment.

Conversation roles are `analyst|assistant|system`; source is `analyst|llm|deterministic|system`. Persist messages and proposal references per assessment. Bound message length, history page size, and model context independently. The initial `Assessment.request` remains the initiating request; later messages are append-only and any change to assessment intent increments `state_revision`, invalidating stale proposals. Conversation text is never an authorization source.

## 3. Routes and ownership

| Owner | Route | Main request / response |
| --- | --- | --- |
| Foundation | GET /health/live; GET /health/ready | Separate liveness and DB/migration readiness; neither proves the pipeline |
| Foundation | POST /auth/login; POST /auth/logout; GET /auth/me | Session and CSRF; never return credentials |
| Contract/foundation | GET /capabilities | Manifest from section 4 |
| Assessment | POST /assessments; GET /assessments; GET /assessments/{id} | Create name/request/scope; list/detail DTOs |
| Assessment | PUT /assessments/{id}/scope | expected_version + scope; 409 when stale |
| Assessment | PATCH /assessments/{id}/request | expected_revision + request; invalidate stale proposals |
| Conversation | POST /assessments/{id}/messages; GET /assessments/{id}/messages | Append analyst content with expected_revision; paginated persisted history and basis/proposal references |
| Planner | POST /assessments/{id}/plans | expected_revision; return proposal IDs, source=llm or deterministic, limitations |
| Planner | GET /assessments/{id}/decisions | Paginated persisted evidence-linked decision records, including stop/deny/inconclusive outcomes |
| Policy | GET /assessments/{id}/actions; GET /assessments/{id}/approvals | Assessment filters; pending/denied decisions remain traceable |
| Policy | POST /assessments/{id}/approvals/{approval_id}/decision | decision=grant/reject, action_hash, expected_scope_version, rationale |
| Worker | POST /assessments/{id}/actions/{action_id}/executions | Idempotency-Key; expected_action_hash; 202 job |
| Worker | GET /assessments/{id}/executions; GET /assessments/{id}/executions/{execution_id} | States + receipt metadata |
| Worker | POST /assessments/{id}/executions/{execution_id}/cancel | Request bounded cancellation; do not assume the process has stopped |
| Import | POST /assessments/{id}/imports | Multipart file + kind + source timestamps; Idempotency-Key; 202 |
| Import | GET /assessments/{id}/imports/{import_id} | Job state, parse warnings, artifact/observation IDs |
| Findings | GET /assessments/{id}/observations; GET /assessments/{id}/findings; GET /assessments/{id}/findings/{finding_id} | Severity/review/search filters; bounded pagination |
| Findings | POST /assessments/{id}/findings/{finding_id}/review | expected_revision, disposition, rationale, evidence_ids |
| Findings | POST /assessments/{id}/correlations/review | finding_id, observation_ids, decision=link/keep_separate, expected_revision, rationale |
| Artifact | GET /assessments/{id}/artifacts; GET /assessments/{id}/artifacts/{artifact_id}; GET /assessments/{id}/artifacts/{artifact_id}/download | Private safe download; never recompute source sha256 from rendered text |
| Report | POST /assessments/{id}/reports; GET /assessments/{id}/reports; GET /assessments/{id}/reports/{report_id} | expected_revision + Idempotency-Key; snapshot metadata |
| Report | GET /assessments/{id}/reports/{report_id}/download | 409 until ready; never rerender from live state |
| Audit | GET /assessments/{id}/timeline | Stable event ordering/cursor, including denials/failures |

This minimum route inventory lets the frontend map views. G0 must define complete request/response JSON Schemas, examples, nullability, limits, and HTTP statuses for every route before domain implementation begins. Freeze message mutation idempotency/retry behavior together with the message schema; a browser retry must not silently duplicate analyst messages or invoke the model twice.

## 4. Capability manifest and UI

```json
{
  "contract_version": "0.1.0",
  "capabilities": [
    {
      "id": "reports.pdf",
      "availability": "planned",
      "reason_code": "module_in_progress",
      "message": "In development",
      "mode": "server_pdf",
      "evidence_level": "none"
    }
  ]
}
```

Availability: `planned|available|unavailable|unsupported`. Evidence level: `none|unit_verified|local_integration_verified|live_lab_verified`. `available` means callable in the current environment; it does not imply live acceptance. Frontend preview has a separate fixture manifest and an always-visible banner. Network errors/401/500/contract mismatches must not become planned. An implemented route with a missing scanner binary is `unavailable` with a reason, not `available`.

## 5. Internal interfaces frozen at G0

The following names are design targets, not existing functions:

```python
# foundation: service object receives injected session + trusted actor/clock
get_session() -> Session
require_analyst() -> Analyst
append_event(event: AuditEventInput) -> TimelineEvent
# assessments / conversation / artifacts
get_snapshot(assessment_id: UUID) -> AssessmentSnapshot
append_message(assessment_id: UUID, expected_revision: int, message: ConversationMessageInput) -> ConversationMessage
put_bytes(assessment_id: UUID, content: bytes, metadata: ArtifactInput) -> Artifact
read_bytes(assessment_id: UUID, artifact_id: UUID) -> bytes
# policy: actor/worker identity and clock are injected, never client-supplied
# atomically validate/bind grant and budget to one attempt reservation
# DispatchPermit is a reservation, not permission for an unbounded delayed start
# returns deny/conflict exceptions without starting a process
authorize_dispatch(action_id: UUID, attempt_id: UUID) -> DispatchPermit
# trusted launcher only: recheck current scope/preparation/fence and consume grant
authorize_start(attempt_id: UUID, attempt_fence: int, descriptor_hash: str, prepared_receipt_hash: str) -> StartAuthorization
# parsing takes raw bytes only, with no network/DB access
parse(raw_bytes: bytes, source_metadata: SourceMetadata) -> ParsedBatch
# findings / reporting
# only the normalization persistence owner creates observation IDs
# and validates assessment ownership before linking them
ingest_observations(batch: ParsedBatch) -> list[Observation]
correlate(assessment_id: UUID, observation_ids: list[UUID]) -> list[Finding]
create_snapshot(assessment_id: UUID, expected_revision: int) -> ReportSnapshot
render_pdf(snapshot: ReportSnapshot) -> bytes
```

The assessment module owns conversation persistence through `assessments/conversation.py`; this is an internal responsibility, not a new process or separately staffed lane. Persist planner decision records with evidence/action links independently of chat display.

G0 defines every type, exception, transaction owner, maximum size, and caller authorization rule. Scanner owners consume shared DTO/service contracts. Every adapter has the same parse interface; only live adapters expose execution capability. Reports never call scanners; the planner never calls the worker directly. The worker adds no independent migration to the shared migration chain. Report job handling calls `render_pdf` with a frozen snapshot and persists the resulting artifact through the shared artifact service; it does not require a scan action or consume a scanner approval grant.

## 6. Follow-up research decisions — 2026-11-02

The [G0 decision register](../../research/G0_CONTRACT_DECISIONS.md) supplies candidate field bounds, typed scope/profile/risk semantics, message/plan idempotency, hash normalization and separate lifecycles. It remains a design: executable OpenAPI/examples and G0 validation have not run. The [scanner decisions](../../research/SCANNER_READINESS_DECISIONS.md) specify selected native versions and origin-wide AF-only ZAP. The [provider decision](../../research/MODEL_PROVIDER_DECISIONS.md) is conditional evaluation, not an enabled model.

`DispatchPermit` now explicitly denotes a grant/budget reservation bound to an attempt. The host launcher uses `authorize_start` after network preparation, rechecks the same serialized scope/action/grant records, and atomically consumes the bound grant. Scope changes after this logical dispatch point request cancellation; no atomic DB/process-start or immediate physical revocation guarantee is made. Public execution stays queued through preparation, then running requires an observed scanner-start receipt; job running is scheduler activity. Freeze internal phases, fences and generation types at G0 according to the [safety/recovery decisions](../../research/SAFETY_RECOVERY_PILOT_DECISIONS.md).
