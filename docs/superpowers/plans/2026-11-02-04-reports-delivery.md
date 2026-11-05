# CoreVAPT Reports & Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement each task. Check a box only after collecting evidence.

**Goal:** Generate PDFs from immutable snapshots with traceable evidence and deliver a local stack with reproducible setup, execution, and reconciliation.

**Architecture:** The report module reads assessment state at one revision in a short transaction, persists an immutable JSON snapshot, and queues rendering on the existing worker. The renderer reads only that snapshot and packaged template resources; authenticated API routes serve artifact downloads. Integration owner assembles modules in Docker Compose and CI after contract-compliant handoff. Report/import jobs have their own domain states, separate from tool executions; no extra broker or worker system is required.

**Tech Stack:** Foundation's Python/FastAPI/PostgreSQL; HTML/Jinja2 autoescape + WeasyPrint is the proposed renderer and requires dependency smoke testing; pytest, a PDF text extractor, Docker Compose.

**Spec:** [Platform design](../specs/2026-11-02-corevapt-platform-design.md), [shared contracts](../specs/2026-11-02-corevapt-contracts.md).

## Global Constraints

- Preserve `corevapt_frontend_v6.1.html`; reference `corevapt_frontend_v6.2.html`. The user's appointed agent owns frontend.
- PostgreSQL owns canonical state; raw artifacts and report snapshots are immutable, with checksums over bytes.
- Distinguish fixtures, local verification, and live scanner evidence; unexecuted does not mean passed.
- Foundation/integration ownership of `backend/src/corevapt/app.py`, configuration, shared contracts, migrations, dependency lockfiles, and Compose/CI wiring must name one writer per shared file. Other lanes submit patch requests through the coordinator.
- Scanner execution requires an isolated lab with ROE and egress enforcement; report work does not authorize external scans.
- Module/test paths and commands below are future implementation targets. The initial plan did not establish backend, Compose, or an application test runner. Recheck actual files before execution.

## Ownership and prerequisites

| Lane | Can start after contract freeze | Required before integration |
| --- | --- | --- |
| Reports | Templates, snapshot-schema tests, renderer with labeled fixtures | DB repository, artifact storage, report jobs, auth dependency |
| Integration/Delivery | Runbook and CI skeleton review | Runnable foundation, module routers, worker handlers |
| Appointed frontend | Prototype-based report UI and labeled contract mocks | Ready reports/capabilities API and authenticated downloads |

Report owner edits only `backend/src/corevapt/reports/`, `backend/tests/unit/reports/`, `backend/tests/integration/test_reports.py`, and report documentation. Integration owner updates `compose.yaml`, `backend/Dockerfile`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`, `scripts/check_stack.py`, `README.md`, and `docs/runbooks/local-platform.md`; coordinate with foundation so each shared file has one writer at a time.

### Task RP1: Immutable snapshot at a consistent revision

**Proposed files:** `backend/src/corevapt/reports/snapshot.py`, `backend/src/corevapt/reports/service.py`, `backend/tests/unit/reports/test_snapshot.py`, `backend/tests/integration/test_reports.py`.

**Interface:** `create_snapshot(assessment_id: UUID, expected_revision: int) -> ReportSnapshot`. `ReportSnapshot` contains `id`, `assessment_id`, `state_revision`, `scope_version`, `created_at`, `assessment`, `executions`, `findings`, `observations`, `artifacts`, `approvals`, `decisions`, `limitations`, and `provenance_versions`; include evidence-linked planner decisions and frozen risk-input provenance. Inject actor/session/clock from trusted context, never the request actor. Export concrete schema from shared contracts; domain repositories provide projections. Report service reads only the requested assessment. Return 409 for revision changes and 403 for unauthorized actors.

- [ ] RP1.1 Write an independent mutation test without relying on JSON key order:

```python
def test_snapshot_keeps_original_review(report_service, assessed_fixture):
    snapshot = report_service.create_snapshot(
        assessed_fixture.id, assessed_fixture.revision
    )
    assessed_fixture.review_first_finding("rejected", reason="Independent follow-up")
    stored = report_service.get_snapshot(snapshot.id, assessed_fixture.actor_id)
    assert stored.findings[0].validation_status == "needs_review"
    assert stored.state_revision == snapshot.state_revision
```

`report_service` uses isolated PostgreSQL; `assessed_fixture` creates a needs_review finding with source observation and artifact bytes/hash. SQLite cannot establish transaction-snapshot correctness.

- [ ] RP1.2 From `backend/`, run `python -m pytest tests/unit/reports/test_snapshot.py tests/integration/test_reports.py -q`; confirm missing-service failure and preserve RED logs.
- [ ] RP1.3 Implement repeatable-read or revision-bound projection with optimistic checks; deep-copy/freeze JSON and persist through artifact storage. If DB commit fails after artifact creation, record store reconciliation instead of reporting ready.
- [ ] RP1.4 Reject findings/observations/artifacts from another assessment. Memberships, severity counts, and raw hashes come from the frozen projection. Same idempotency key/body returns the same report ID; changed body returns 409.
- [ ] RP1.5 Rerun to GREEN, review migration requests with foundation, and preserve snapshot JSON/hash in run evidence. Commit task only after coordinator repository setup; the report lane does not initialize Git.

**Manual:** Create snapshot A → change review → download A again → same content/hash; create B → new revision/content/ID. Record report IDs, revisions, and hashes, not merely a success-button screenshot.

### Task RP2: Six-section PDF renderer with isolation and resource limits

**Proposed files:** `backend/src/corevapt/reports/render.py`, `backend/src/corevapt/reports/templates/report.html`, `backend/src/corevapt/reports/templates/report.css`, `backend/tests/unit/reports/test_render.py`, `backend/tests/fixtures/reports/manifest.json`.

**Interface:** `render_pdf(snapshot: ReportSnapshot) -> bytes`. Inject `PackagedResources` when constructing the renderer; it maps packaged font/CSS names only. Reject evidence-supplied `http:`, `https:`, `file:`, and paths. Proposed defaults: 30-second deadline, 512 MiB memory ceiling, 10 MiB snapshot limit in the rendering container. Integration owner must verify these against large fixtures; render_failed preserves the snapshot and never marks ready.

- [ ] RP2.1 Write tests with a Unicode fixture containing one service-discovery observation, two findings, one Unknown severity, one historical import, and one failed execution:

```python
def test_pdf_has_required_sections_and_unknown(renderer, snapshot, pdf_text):
    document = renderer.render_pdf(snapshot)
    assert document.startswith(b"%PDF-")
    text = pdf_text(document)
    for heading in ("7.1", "7.2", "7.3", "7.4", "7.5", "7.6"):
        assert heading in text
    assert "Unknown" in text
    assert snapshot.findings[0].id in text
```

`pdf_text` uses a pinned PDF parser; this synthetic fixture never calls scanners and is labeled accordingly. Add a resource-fetch callback test that raises for external/file URLs; hostile `<script>` and `<img src=file:///etc/passwd>` remain escaped description text, never resources.

- [ ] RP2.2 From `backend/`, run `python -m pytest tests/unit/reports/test_render.py -q`; preserve RED.
- [ ] RP2.3 Implement sections 7.1 Executive Summary, 7.2 Assessment Methodology, 7.3 Severity Distribution, 7.4 Detailed Vulnerability Findings, 7.5 Impact and Remediation, 7.6 Assessment Limitations. Include scope/ROE, tool/profile/exit outcomes, source confidence scales, finding evidence IDs/locators/hashes, risk reasons and source inputs, approvals, timestamps, unsupported coverage, and model/fallback labels.
- [ ] RP2.4 Render in a bounded process without target/scanner/model credentials, using packaged Unicode fonts. Count canonical findings separately from service observations. CVSS/CVE/CWE without source support displays Unknown/Not established, never default numbers. Preserve CVSS vector/version/source when available. Store PDF checksum/template version in its artifact manifest.
- [ ] RP2.5 Run GREEN; confirm malicious fixtures cannot trigger network/file reads, exercise deadline/memory limits, and preserve failures in job/timeline.

**Manual:** Open PDF on desktop; inspect multilingual Unicode text, headings, page breaks, long tables/URLs, and hash appendix. A zero-finding report still includes methodology/limitations. Compare severity totals to the snapshot, not subsequently changed UI state. Project-authored copy remains English; Unicode fixtures test font behavior without changing product language.

### Task RP3: Authenticated report creation/download and evidence access

**Proposed files:** `backend/src/corevapt/reports/router.py`, `backend/tests/integration/test_reports.py`, `backend/tests/integration/test_artifact_download.py`. Foundation/artifact owner owns artifact download routes; report owner supplies tests/review without concurrent edits. Use `router.py` consistently with the other plans; the earlier `routes.py` spelling is superseded before implementation.

**HTTP interface:** Base `/api/v1`. `POST /assessments/{assessment_id}/reports` accepts `expected_revision` and `Idempotency-Key`, returns 202 `{job_id, resource_id, status_url}` where resource_id is the report ID. `GET /assessments/{assessment_id}/reports/{report_id}` returns state/snapshot/artifact metadata. `GET /assessments/{assessment_id}/reports/{report_id}/download` returns `application/pdf` only when ready. Freeze names against contracts before code; coordinator owns changes. `GET /assessments/{assessment_id}/artifacts/{artifact_id}/download` uses the same ownership check. Auth supplies actors; never trust a body `reviewer`.

- [ ] RP3.1 Write integration tests: absent authentication→401; cross-assessment URL→404; insufficient actor→403; stale revision/idempotency conflict→409; running/failed report download→409. Assert no duplicate report/job rows.
- [ ] RP3.2 From `backend/`, run `python -m pytest tests/integration/test_reports.py tests/integration/test_artifact_download.py -q`; observe RED.
- [ ] RP3.3 Implement services/routers and submit job registration patch requests. Register `kind=report` on the existing worker; call the report renderer with frozen snapshot ID, never the scanner adapter. Server generates paths and sanitizes download filenames. Return `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`; no local filesystem paths/credentials in DTOs.
- [ ] RP3.4 On an isolated test volume, changing one PDF/raw byte causes integrity mismatch and audit; never serve corrupted bytes as verified evidence. Do not modify raw demo files already used for acceptance.
- [ ] RP3.5 Run GREEN. Report capability becomes `available` only with integration evidence and runtime dependency checks; local integration earns `local_integration_verified`, never readiness merely because code merged.

**Manual:** Authorized analyst downloads PDF; copied URL fails anonymously; assessment B cannot access A's evidence. Stopping API produces a connection error, never a blank report or “In development”.

### Task DL1: Assemble local stack/CI and deliver repeatable execution

**Owner:** Integration owner; master plan explicitly assigns shared-file writers with foundation.

**Proposed files:** `compose.yaml`, `backend/Dockerfile`, `.env.example`, `.gitignore`, `.github/workflows/ci.yml`, `scripts/check_stack.py`, `docs/runbooks/local-platform.md`, `README.md`.

**Interface:** Compose services `db`, `migrate`, `api`, `worker`; appointed frontend owner hands build/start contracts to integration. Scanner/lab profiles are separate and off by default. Secrets remain backend/worker-only; do not publish private raw volume statically. `GET /api/v1/health/ready` reports dependency health; `GET /api/v1/health/live` reports process liveness; authenticated `/api/v1/capabilities` reports per-feature `availability`/`evidence_level`. None replaces pipeline evidence.

- [ ] DL1.1 Create a smoke test for health, authenticated assessment create/read, fixture-backed report queued→ready, PDF download `%PDF-`, and hash. It must refuse scanner-working claims based only on fixtures.
- [ ] DL1.2 Once foundation packages/dependencies exist, agree on target commands:

```bash
docker compose -p corevapt-test config --quiet
docker compose -p corevapt-test up -d --build db api worker
python scripts/check_stack.py --base-url http://127.0.0.1:8000 --evidence-dir docs/implementation/evidence/local-smoke
```

`migrate` is a one-shot dependency before api/worker. Script reads test credentials from environment without exposing secrets. The proposed port must be confirmed free; use isolated project/volumes.

- [ ] DL1.3 CI runs foundation-selected lint/type checks, contract-schema validation, unit tests, PostgreSQL integration, renderer smoke, frontend contract/component tests, and labeled mocked browser E2E. Live lab tests are separate opt-in jobs with ROE; CI never independently scans external targets or calls paid models.
- [ ] DL1.4 Lock versions/digests after upstream verification during implementation; record image/scanner/font/license sources, never guessed versions. Migrate an empty DB and a previous-revision test DB; migration failure keeps the stack unready.
- [ ] DL1.5 Document setup/env/private data, start/stop/logs, backup/restore, lab-enablement gate, test-only reset, and evidence paths. Stop with `docker compose -p corevapt-test stop`; do not `down -v` user volumes. Separate pass/fail/blocked/skipped by test layer.

**Exit gate:** Build/start/migration logs, smoke JSON, sample snapshot/PDF/hash, explicitly identified CI or local equivalent, limitations, and evidence-backed seven-tool matrix. Missing fresh-stack E2E/live scans remain blocked/not_run with reasons; never call the platform complete from this plan.

## Follow-up pilot and delivery research

DL1 consumes the [safety/recovery/pilot decisions](../../research/SAFETY_RECOVERY_PILOT_DECISIONS.md): coordinator-owned host launcher/runbook, separate local/remote network acceptance, resource/lease/orphan diagnostics and a quiesced DB+artifact+journal backup bundle. A restore increments host generation and cannot revive a consumed grant. These are unrun pilot gates; retain immutable-snapshot/download checks. The [organizer confirmation pack](../../research/ORGANIZER_CONFIRMATION_PACK.md) contains an unresolved duration conflict relevant to submission scheduling.
