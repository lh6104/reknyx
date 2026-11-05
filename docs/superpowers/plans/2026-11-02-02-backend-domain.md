# Backend Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement each task. The checklists track future work, not achieved results.

**Goal:** Build a durable backend for assessments, execution authorization, provenance, conversations, findings, and planning so frontend/scanner/report modules share one contract.

**Architecture:** FastAPI modular monolith and separate worker using PostgreSQL as canonical state. Each module owns its implementation; shared contracts, composition root, and migration graph have one owner. Artifacts are immutable bytes in private local storage; the DB owns manifests and lineage.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, pytest. Select and lock versions during foundation implementation; this document does not claim dependencies are installed.

**Spec:** [Platform design](../specs/2026-11-02-corevapt-platform-design.md), [shared contracts](../specs/2026-11-02-corevapt-contracts.md); also read [requirements matrix](../../research/REQUIREMENTS_MATRIX.md), [technical recommendations](../../research/TECHNICAL_RECOMMENDATIONS.md), and [upstream comparison](../../research/UPSTREAM_ARCHITECTURE_COMPARISON.md).

## Global Constraints

- The user's appointed agent owns frontend; backend agents do not edit prototypes or frontend files.
- Implement only after the master plan freezes design/contracts. If contract names differ, update this plan first; do not silently introduce aliases.
- API prefix `/api/v1`; the server authenticates the actor; the client cannot choose the reviewer.
- PostgreSQL owns canonical state; prompts and UI do not own execution state.
- Never generate shell commands from the model; approval cannot exceed scope or enable unimplemented capability.
- Frontend displays “In development” for planned capability; a runtime failure of available capability remains an error.
- A fake or synthetic fixture does not turn Planned into Working.
- Do not add a broker, vector database, graph database, or second workflow engine to the MVP.
- At initial drafting, the workspace had no backend, migrations, or Git repository. Recheck before implementation. Code paths and test commands below are proposed targets, not installed/executed results. Commit only after the coordinator establishes Git.

## Ownership, order, and parallel work

| Lane | Owner | Owned edits | Required input | Independent work |
| --- | --- | --- | --- | --- |
| BE-01 Foundation | Foundation/integrator | `backend/pyproject.toml`, lockfile, `app.py`, `config.py`, `contracts.py`, `foundation/`, Alembic, model registry | Contract freeze | Frontend contract fixtures; pure scanner parsers; QA cases |
| BE-02 Scope/conversation | Assessment agent | `assessments/`, scope/conversation tests | BE-01 session/auth/DTO | BE-03 storage |
| BE-03 Artifact | Storage agent | `artifacts/`, artifact tests | BE-01 session/auth/DTO | BE-02 scope |
| BE-04 Policy | Policy agent | `policy/`, policy tests | BE-02 scope snapshot; BE-01 transactions/events | Pure scanner adapters; pure report renderer |
| BE-05 Observations/findings | Findings agent | `findings/`, finding tests | BE-03 manifest; frozen observation DTO | BE-04 policy |
| BE-06 Planner | Planner agent | `planner/`, planner tests | BE-02/04/05 contracts | Scanner and PDF integration |
| BE-07 Integration | Foundation/integrator | Composition root, migration graph, contract tests | BE-01…06 | QA manual preparation |

Each agent exports `models.py`, `router.py`, and public services inside owned directories. Send model/router/migration requirements to the integrator; do not independently edit `app.py`, `foundation/model_registry.py`, `alembic/env.py`, shared DTOs, or dependency lockfiles. A directory has one active writer. Never run concurrent migrations against the same database; parallel tests require separate databases/schemas named by run ID.

## File map and internal interfaces frozen at BE-01

| Module | Main files | Proposed public interface |
| --- | --- | --- |
| Foundation | `backend/src/corevapt/foundation/db.py`, `auth.py`, `events.py`, `idempotency.py` | `get_session() -> Session`; `require_analyst() -> Analyst`; `append_event(event: AuditEventInput) -> TimelineEvent` |
| Assessment | `assessments/service.py`, `scope.py`, `models.py`, `router.py` | `get_snapshot(assessment_id: UUID) -> AssessmentSnapshot`; `revise_scope(assessment_id: UUID, expected_version: int, scope: ScopeInput) -> AssessmentSnapshot` |
| Conversation (assessment-owned) | `assessments/conversation.py`, `assessments/models.py`, `assessments/router.py` | `append_message(assessment_id: UUID, expected_revision: int, message: ConversationMessageInput) -> ConversationMessage` |
| Artifact | `artifacts/service.py`, `storage.py`, `models.py`, `router.py` | `put_bytes(assessment_id: UUID, content: bytes, metadata: ArtifactInput) -> Artifact`; `read_bytes(assessment_id: UUID, artifact_id: UUID) -> bytes` |
| Policy | `policy/service.py`, `binding.py`, `models.py`, `router.py` | `evaluate(action: ActionProposal, snapshot: AssessmentSnapshot) -> PolicyDecision`; `authorize_dispatch(action_id: UUID, attempt_id: UUID) -> DispatchPermit` |
| Findings | `findings/ingest.py`, `correlation.py`, `risk.py`, `service.py`, `models.py`, `router.py` | `ingest_observations(batch: ParsedBatch) -> list[Observation]`; `correlate(assessment_id: UUID, observation_ids: list[UUID]) -> list[Finding]` |
| Planner | `planner/service.py`, `context.py`, `validation.py`, `provider.py`, `router.py` | `propose_next(snapshot: AssessmentSnapshot, provider: PlannerProvider) -> PlanResult`; `validate_proposal(proposal: ActionProposal, snapshot: AssessmentSnapshot) -> ValidatedProposal` |

Service objects receive injected sessions, trusted actors, and clocks; public service methods never take a client-supplied actor. A FastAPI dependency may use a generator internally to close sessions, while the public contract returns Session. `UUID` and `Session` come from base libraries. The contract owner defines `Analyst`, `AuditEventInput`, `TimelineEvent`, `AssessmentSnapshot`, `ScopeInput`, `ConversationMessageInput`, `ConversationMessage`, `ArtifactInput`, `Artifact`, `ActionProposal`, `PolicyDecision`, `DispatchPermit`, `ObservationInput`, `Observation`, `Finding`, `ParsedBatch`, `PlanResult`, and `ValidatedProposal` in `contracts.py`. `PlannerProvider` is an internal `generate(context: PlannerContext) -> ProviderResult` protocol in `planner/provider.py`; define `PlannerContext` and `ProviderResult` there too. Scanner/report/frontend modules must not introduce competing DTOs.

## BE-01 — Foundation with authenticated requests, persistence, and audit

**Create:** `backend/pyproject.toml`, `backend/src/corevapt/{__init__,app,config,contracts}.py`, `backend/src/corevapt/foundation/{db,auth,events,idempotency,model_registry}.py`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_foundation.py`, `backend/tests/conftest.py`, `backend/tests/integration/test_foundation.py`.

**Consumes:** Shared contract. **Produces:** Per-request/task sessions, authenticated analyst, audit append in the same transaction, one migration graph, and application assembly.

- [ ] Freeze local analyst authentication in the shared contract. Configure username/password hash through backend secrets; use bounded HttpOnly/SameSite sessions and CSRF/origin checks for cookie-authenticated mutations. No secrets in frontend/query strings. Test fixtures log in through the real contract endpoint instead of supplying actors in request bodies.
- [ ] Write failing unauthenticated mutation, forged reviewer, and restart-persistence tests. Proposed HTTP test seam (`client` is TestClient using an isolated PostgreSQL database):

```python
def test_unauthenticated_assessment_is_rejected(client):
    response = client.post('/api/v1/assessments', json={})
    assert response.status_code == 401

def test_missing_database_is_not_ready(client_without_database):
    response = client_without_database.get('/api/v1/health/ready')
    assert response.status_code == 503
```

- [ ] Run `cd backend && python -m pytest tests/integration/test_foundation.py -q`; record the actual failing result, then implement minimal configuration/session/auth/audit/migrations. The application DB role cannot edit/delete audit records; migrations use another role. Separate liveness/readiness; health does not demonstrate scanner operation.
- [ ] Add unique idempotency constraint `(actor_id, assessment_id, operation, key)` plus request digest. Same key/payload returns the original resource; same key/different payload returns `409`. Bound transactions; never keep one open across scanner/model calls.
- [ ] Test wrong/correct login/logout, cookie flags, CSRF mutations, server-side actors, DB unavailable, rollback without false successful audit, and concurrent idempotent requests. Migrate an empty DB, verify one Alembic head, and confirm repeated `upgrade head` leaves data unchanged.
- [ ] Manual: create an assessment through authenticated HTTP, restart API, reread the same ID; confirm logs omit passwords/cookies. Preserve commands, timestamps, schema revision, and redacted responses in run evidence.
- [ ] Integrator reviews/commits once Git exists and publishes the foundation interface to other owners.

## BE-02 — Assessments, versioned scope, and persisted conversation

**Create:** `backend/src/corevapt/assessments/{models,scope,conversation,service,router}.py`, `backend/tests/unit/test_scope.py`, `backend/tests/integration/test_assessments.py`, `backend/tests/integration/test_conversation.py`. Integrator creates migrations from model diffs, with `0002_assessments.py` expected after BE-01; integrator chooses the final sequence.

**Consumes:** BE-01 auth/session/audit. **Produces:** Assessment create/list/detail, scope revisions, initiating request, persisted messages, and canonical snapshot. Scope includes lab authorization reference, allowed hosts/IPs/ports/profiles, exclusions, validity, and contract budgets.

- [ ] Write failing exact-hostname and stale-revision tests. Scope fixture: `web.lab.example`, IPv4 `192.0.2.20/32`, port 8080, excluded port 8081. Documentation IP ranges are unit fixtures, not live scan targets.

```python
def test_hostname_suffix_does_not_authorize(scope_fixture):
    from corevapt.assessments.scope import allows_destination
    assert not allows_destination(scope_fixture, 'web.lab.example.attacker.test', 8080)

def test_excluded_port_is_denied(scope_fixture):
    from corevapt.assessments.scope import allows_destination
    assert not allows_destination(scope_fixture, 'web.lab.example', 8081)
```

- [ ] Run `cd backend && python -m pytest tests/unit/test_scope.py -q`; implement `allows_destination(scope: ScopeInput, host: str, port: int) -> bool` with IP/hostname canonicalization, exact allowlist, and deny-precedence exclusions. Check validity through an injected clock; scanner plan owns DNS/runtime destination enforcement.
- [ ] Implement contract routes, immutable scope history, and CAS on expected scope version. Request edits use expected state revision; audit denied/stale requests. Request text never adds a target to scope. Creating a draft with an authorization reference does not verify lab permission.
- [ ] Persist append-only analyst/assistant messages with assessment, actor/source, timestamps, state revision, evidence basis IDs, and proposal IDs. Enforce bounded size/pagination, replay-safe message mutation, and cross-assessment reference checks. A changed analyst request increments canonical state revision and invalidates stale proposals; chat text never changes scope/approval implicitly.
- [ ] Test restart/reload conversation persistence, A/B isolation, duplicate browser retry, stale revision, nonexistent/foreign evidence references, and bounded history retrieval. Retain the initiating request and proposal decision records independently of displayed chat history.
- [ ] Test IPv4/IPv6 canonical forms, invalid ports, URL credentials, hostname suffix tricks, expired scope, exclusions, invalid CIDRs, revision conflicts, and assessment isolation. Reject extra JSON fields rather than accepting arbitrary reviewers/commands.
- [ ] Run `cd backend && python -m pytest tests/unit/test_scope.py tests/integration/test_assessments.py tests/integration/test_conversation.py -q`.
- [ ] Manual: create a finding-free draft, revise scope v1→v2 and confirm v1 remains; inspect actor/time/reason in timeline. Append a message, restart, and confirm the history and evidence/proposal links persist. An HTTP client can provide evidence before frontend integration.
- [ ] Review/commit and send an actual snapshot example to policy/planner/scanner owners.

## BE-03 — Immutable artifacts and provenance manifests

**Create:** `backend/src/corevapt/artifacts/{models,storage,service,router}.py`, `backend/tests/unit/test_artifact_storage.py`, `backend/tests/integration/test_artifacts.py`. Integrator owns manifest migration; never edit another owner's migration.

**Consumes:** BE-01 transactions/auth; BE-02 assessment ownership. **Produces:** Immutable artifacts for scanner/import/report and private authorized downloads.

- [ ] Write failing byte-hash and path-traversal tests. Internal storage interface: `LocalArtifactStore.put(content: bytes) -> StoredBlob`, `.get(storage_key: str) -> bytes`; `StoredBlob` contains key/sha256/size in `storage.py`. Clients cannot choose storage paths.

```python
def test_storage_preserves_exact_bytes(tmp_path):
    import hashlib
    from corevapt.artifacts.storage import LocalArtifactStore
    raw = b'<report>\r\nraw &amp; bytes</report>'
    store = LocalArtifactStore(tmp_path)
    blob = store.put(raw)
    assert store.get(blob.storage_key) == raw
    assert blob.sha256 == hashlib.sha256(raw).hexdigest()
    assert blob.size == len(raw)
```

- [ ] Run `cd backend && python -m pytest tests/unit/test_artifact_storage.py -q`; implement temporary write → flush → atomic rename, private root, generated key, original checksum, and manifest. Block symlink/path escapes; expose no raw-overwrite endpoint.
- [ ] If DB commit fails after a file write, preserve an orphan receipt for reconciliation. Reconciliation deletes only blobs unreferenced by any manifest after a configured retention window, with dry-run support. Never claim filesystem/DB atomicity.
- [ ] Test empty/oversized content, exact readback, duplicate content across assessments without metadata leakage, DB rollback/orphans, missing blob integrity errors, checksum mismatch, unauthorized download, malicious filenames, and scanner-text XSS in preview. Import routes enforce MIME/size limits; storage also has a hard limit.
- [ ] Run `cd backend && python -m pytest tests/unit/test_artifact_storage.py tests/integration/test_artifacts.py -q`.
- [ ] Manual: upload a valid lab output when a provenance-recorded fixture is available; download and compare `sha256sum`; change one byte in a copy and check integrity failure while preserving original raw bytes. Label synthetic fixtures as tests.
- [ ] Review/commit and publish manifest DTOs without exposing filesystem paths to frontend.

## BE-04 — Policy, exact approvals, and single-use dispatch permits

**Create:** `backend/src/corevapt/policy/{models,binding,service,router}.py`, `backend/tests/unit/test_policy.py`, `backend/tests/integration/test_approval_dispatch.py`.

**Consumes:** BE-02 scope snapshots, authenticated actor, shared action/profile DTOs, and capabilities published by the integration owner. **Produces:** `permit/require_approval/deny`, approvals bound to action hash/scope version/expiry, and one-attempt dispatch reservations. The worker reserves; the trusted host launcher crosses the final `authorize_start` seam before releasing its fixed scanner.

- [ ] Write failing stable-hash and changed-parameter invalidation tests. Canonical envelopes contain normalized JSON types, sorted keys, fixed separators, contract-defined target/evidence ordering, one UTC timestamp format, and versioned profiles.

```python
def test_binding_changes_with_port(action_envelope):
    from corevapt.policy.binding import action_digest
    changed = {**action_envelope, 'parameters': {'ports': [8081]}}
    assert action_digest(action_envelope) != action_digest(changed)
```

- [ ] Run `cd backend && python -m pytest tests/unit/test_policy.py -q`; implement `action_digest(envelope: dict) -> str`, policy evaluation, and decision storage. Denied actions remain auditable but create no runnable execution. Frontend cannot submit argv or override permits.
- [ ] In the short `authorize_dispatch` transaction, lock action/grant and check current scope/revision, implemented capability, evidence ownership, expiry, budgets, and action hash. Atomically reserve attempt/grant and commit before scanner invocation; worker receipts/recovery address the gap after reservation. Lease expiry never automatically grants a new permit.
- [ ] Implement launcher-only `authorize_start` after preparation: use the same assessment-first lock order, recheck current scope/grant/cancel/deadline/fence/preparation, and consume the bound grant once. The reservation itself never starts a scanner. Test both orders of scope revision versus final authorization and record the unavoidable physical-start gap.
- [ ] Test pending/rejected cannot dispatch; a valid grant reserves once; expired/stale scope/changed parameters are blocked; foreign evidence is rejected; unsupported tools remain denied despite a grant; concurrent workers receive one permit; forged reviewers never alter the actor. Grant consumption is not execution success.
- [ ] Deny offensive validation while no supported active-validation adapter/profile exists. A granted UI record must not bypass backend capability or worker validation. Record the PDF section 9.5 demonstration gap separately: gate tests/fake runners cannot establish a real approved validation outcome.
- [ ] Run `cd backend && python -m pytest tests/unit/test_policy.py tests/integration/test_approval_dispatch.py -q` against real PostgreSQL; SQLite does not establish locking correctness.
- [ ] Manual: approve an exact action, change scope before dispatch, and observe contract `409`/denial with zero external calls from an explicitly labeled runner spy. Live demonstrations require an authorized lab and separate outcome evidence.
- [ ] Review/commit and publish DispatchPermit to the worker owner.

## BE-05 — Observations, correlation, risk, and analyst review

**Create:** `backend/src/corevapt/findings/{models,ingest,correlation,risk,service,router}.py`, `backend/tests/unit/test_correlation.py`, `backend/tests/unit/test_risk.py`, `backend/tests/integration/test_findings_lineage.py`.

**Consumes:** BE-03 artifact manifests and scanner-parser `ObservationInput`. **Produces:** Idempotent observations, canonical memberships preserving raw locators, priority reason codes, and analyst dispositions with rationales.

- [ ] Freeze observation identity `(assessment_id, artifact_id, parser_version, native_record_key)`. Service-discovery observations do not increase vulnerability counts. Reparse with the same parser version is idempotent; a new parser version creates versioned results without overwriting history.
- [ ] Write failing tests through pure correlation seam `classify_pair(left: ObservationInput, right: ObservationInput) -> CorrelationDecision` in `correlation.py`; `CorrelationDecision` contains `relation`, `reason_codes`, and `rule_version`.

```python
def test_same_cve_different_assets_stay_separate(observation_factory):
    from corevapt.findings.correlation import classify_pair
    left = observation_factory(asset='192.0.2.20', cve='CVE-2024-0001')
    right = observation_factory(asset='192.0.2.21', cve='CVE-2024-0001')
    assert classify_pair(left, right).relation == 'unmatched'
```

- [ ] Run `cd backend && python -m pytest tests/unit/test_correlation.py tests/unit/test_risk.py -q`; implement exact duplicates first, then mapped cross-tool rules over asset/service/location/weakness. Title/CVE equality alone is insufficient. Historical/host-wide observations lacking endpoints become related/needs_review; preserve memberships after analyst overrides.
- [ ] Implement a versioned risk rule with selected severity source and explicit unknowns. Persist CVSS score, vector, version, source, and supporting observation reference when supplied; missing CVSS never becomes zero. Persist exposure, exploitability, and asset impact as evidence-supported or attributed analyst inputs, with unknown values and source/rationale. Keep source severity distinct from contextual priority and store all priority reasons/rule versions. Reject invented CVEs or numeric scores unsupported by the declared rule.
- [ ] Preserve Nmap service confidence, ZAP confidence, and Greenbone QoD semantics; do not add them into a calibrated probability. Review requires reason/evidence/actor; model text alone cannot promote a finding to confirmed.
- [ ] Test mapped positive duplicates, equal titles on different assets, same CVE on different endpoints, different path/method/parameter, absent CVE, historical uncertainty, severity conflicts, service-only observations, unknown risk inputs, and risk provenance. Block FK/cross-assessment artifact mismatches. Analyst rejection preserves raw/member records and auditable rationale; assessment filters never mix records.
- [ ] Run `cd backend && python -m pytest tests/unit/test_correlation.py tests/unit/test_risk.py tests/integration/test_findings_lineage.py -q`.
- [ ] Manual: import two provenance-backed native outputs → open finding → observation ID → raw locator → download/checksum. Compare severity/counts before and after correlation. Report the inspected pair count without inferring system-wide accuracy.
- [ ] Review/commit and publish finding projections/report-ready snapshots to the report owner.

## BE-06 — Typed planner, adaptive branches, and budget finalization

**Create:** `backend/src/corevapt/planner/{context,provider,validation,service,router}.py`, `backend/tests/unit/test_planner_validation.py`, `backend/tests/integration/test_planner_state.py`.

**Consumes:** Assessment snapshots, persisted conversation, observations, prior attempts/decisions, remaining budget, and static supported action catalog. **Produces:** Proposal or finalization/inconclusive result; never dispatches. Coordinator selects the provider/model when access is available. Fake-provider tests remain fixture-labeled and never display as live AI.

- [ ] Write failing fabricated-evidence tests for `validate_proposal`; `proposal_factory` creates ActionProposal and `snapshot_fixture` contains canonical IDs.

```python
def test_unknown_evidence_is_rejected(proposal_factory, snapshot_fixture):
    import pytest
    from corevapt.planner.validation import validate_proposal, ProposalRejected
    proposal = proposal_factory(basis_observation_ids=['00000000-0000-0000-0000-000000000099'])
    with pytest.raises(ProposalRejected, match='unknown_evidence'):
        validate_proposal(proposal, snapshot_fixture)
```

- [ ] Run `cd backend && python -m pytest tests/unit/test_planner_validation.py -q`; define `ProposalRejected` in `validation.py`, typed proposals, and semantic validation: schema → assessment/evidence → revision/dependencies → capability/scope → repetition/budget. Model output cannot add profiles to the catalog.
- [ ] Build bounded, versioned, redacted context with source IDs; no credentials, arbitrary artifact paths, or unlimited raw content. Provider adapter records model/prompt version, elapsed time, usage, and errors without secrets.
- [ ] Persist a decision record for every proposed/denied/stopped/failed next step: assessment/state/scope revision, candidate profile, rationale, source evidence IDs, policy result, remaining budget, and outcome. Link assistant messages to these records/proposals; conversation text never replaces canonical decision or execution state.
- [ ] Implement deterministic orchestration `running → finalizing → partial/completed`; stop new scans near limits and reserve summary budget. Unavailable provider/invalid schema returns an error or explicit deterministic fallback, never fabricated findings or an apparent live-AI summary.
- [ ] Test HTTP evidence → permitted web proposal; absent HTTP → no ZAP proposal; no unnecessary repeated completed profile; stale revision, foreign observation, shell field, unsupported profile, malformed JSON, timeout, usage limit, and inconsistent expected output never create executions. `done_when` depends on real coverage/artifacts, never model claims.
- [ ] Run `cd backend && python -m pytest tests/unit/test_planner_validation.py tests/integration/test_planner_state.py -q`.
- [ ] Manual: compare proposals/rationales/basis IDs from two evidence sets for the same assessment scenario. A real provider call records request metadata and cost when available; without a provider, model-live acceptance is “unverified”, never replaced by a fake-provider test.
- [ ] Review/commit and expose planner capability only after integration checks pass.

## BE-07 — Assembly, contract verification, and E2E handoff

**Integrator edits:** `backend/src/corevapt/app.py`, `foundation/model_registry.py`, `contracts.py`, `backend/alembic/versions/`, `backend/tests/integration/test_domain_contract.py`; setup-document ownership is assigned by the coordinator.

**Consumes:** BE-01…06 plus reviewed scanner/report routers. **Produces:** One app/migration graph, contract-aligned OpenAPI, and implementation-grounded capabilities.

- [ ] Integrator creates migrations in dependency order; model owners review FKs/uniques/checks. Upgrade empty and populated databases, comparing counts/hashes before/after. Never manually edit `alembic_version`.
- [ ] Freeze the error envelope; test `401/403/409/413/415/422` and reason codes. Lists/details/timeline/conversation/artifacts enforce authenticated assessment context. Submit B's record IDs through A's requests.
- [ ] Test OpenAPI routes/contract fixtures: queued operations return job IDs, idempotency replay returns the same resource, unsupported capability never yields fake success. Auth/error/pagination schemas match frontend fixtures.
- [ ] Run `cd backend && python -m pytest tests/unit tests/integration -q`; export JUnit/OpenAPI comparison to CI/run evidence under the QA plan. Run only after files exist; this plan records no test results.
- [ ] Coordinator manual flow: assessment → evidence → conversation/proposal → approve/reject → actual execution or blocked outcome → finding review → report snapshot. Run restart recovery separately under the scanner plan; show “In development” for missing capability without hiding actual failures.
- [ ] Handoff includes changed files, actual commands/exit codes, schema revision, limitations, evidence paths, and capabilities eligible to become ready. Review spec conformance and code quality before merge.

## Acceptance conditions and test evidence

| Gate | Required evidence | Insufficient evidence |
| --- | --- | --- |
| Foundation | Fresh migration, restart persistence, PostgreSQL auth/CSRF tests | Health 200 |
| Scope/policy | Negative cases, atomic single-permit dispatch, actor audit | Disabled Approve button |
| Conversation/decisions | Restart/isolation/retry tests and evidence-linked persisted history/decisions | Browser-only chat |
| Artifact/lineage | Exact bytes/hash round trip and finding/member/locator trace | Checksum copied from seed metadata |
| Correlation/risk | Named positive/negative pairs, rules/versions, preserved unknowns and risk provenance | Title similarity or LLM verdict |
| Planner | Typed/semantic validation, adaptive branch, quota errors; separate live-model evidence | Fake-provider tests |
| Integrated backend | Clean contract comparison, suite logs, manual run IDs | Independently passing modules |

Each case records ID, commit or source hash before Git, UTC time, redacted configuration/versions, fixture/lab provenance, command/steps, expected/actual, exit code, artifact IDs, and `pass/fail/blocked/not_run`. Unexecuted gates remain `not_run`; expectations are not passes. QA consolidates automated/manual results under the shared QA plan.

## Self-review before execution

- [ ] Compare final shared contract: route names, DTO fields, status/error enums, and authentication.
- [ ] R01/R02/R08/R10/R12/R13/R15 map to BE-01/02/03/04/06; R06/R07/R09 to BE-05; R03 to BE-06. R04/R05 belong to scanner plan, R11 to report plan, R14 to capability integration; BE-07 verifies the seams.
- [ ] No two owners edit migration graph/composition root/shared contracts simultaneously.
- [ ] Every task has a failing test, bounded implementation, targeted run, manual case, and review. Sample code specifies future tests, not existing results.
- [ ] Worker execution requires DispatchPermit and the scanner plan's network scope gate; backend prechecks alone do not establish full network enforcement.

## Follow-up research handoff

Read the [G0 contract decisions](../../research/G0_CONTRACT_DECISIONS.md) before BE-01/02/04/06. Apply separate idempotent message append and planning, provider-independent schemas and typed known/unknown risk data. The [provider decision](../../research/MODEL_PROVIDER_DECISIONS.md) names a conditional first experiment and hard call budgets; there is no live-model result. For BE-04, `authorize_dispatch` reserves while launcher-only `authorize_start` consumes after preparation; freeze fences/generation and restricted DB functions with the foundation owner under the [safety decisions](../../research/SAFETY_RECOVERY_PILOT_DECISIONS.md). None of these additions marks a task complete.
