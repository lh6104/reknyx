# CoreVAPT Testing & Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement each task. Every checkbox requires an observed result before completion.

**Goal:** Accept frontend/backend/worker/report lanes and the complete platform workflow using cases with explicit prerequisites, expected results, and evidence.

**Architecture:** Separate unit/contract tests, PostgreSQL integration, mocked browsers, full-stack E2E, and live labs. QA owns the requirement→case matrix and run manifests; module owners write functional tests within owned paths, and integration owner runs cross-module gates.

**Tech Stack:** pytest + PostgreSQL test database, JSON/OpenAPI validation, browser automation selected by frontend owner, opt-in Docker Compose lab, manual PDF/browser review.

**Spec:** [Platform design](../specs/2026-11-02-corevapt-platform-design.md), [shared contracts](../specs/2026-11-02-corevapt-contracts.md), [requirements R01–R15](../../research/REQUIREMENTS_MATRIX.md).

## Global Constraints

- The user's appointed agents own frontend; QA supplies cases/contracts and does not edit frontend without assignment.
- PostgreSQL owns canonical state; raw artifacts and report snapshots are immutable with byte-level checksums.
- All platform cases below are **planned/not_run**. At initial drafting no application, Compose, or executable platform suite existed. Commands are future implementation targets; prototype-only results do not establish platform case results.
- Live scans require an authorized isolated lab with enforced egress. Mock/fake runners prove logic, not scanner integration.
- Health/docs/UI screenshots do not replace pipeline evidence; native fixtures do not establish live execution.
- Foundation owns dependencies/CI/wiring/migrations; QA never independently changes shared files to make tests pass.

## 1. Evidence model and gates

Record independent feature dimensions: `implementation_status` = planned/in_progress/implemented/unsupported; `verification_status` = not_run/failed/local_verified/live_verified; `runtime_status` = available/unavailable/disabled. A native import can be `local_verified` without being called a live scanner. `live_verified` applies only to actions with receipts from actual scanner/lab execution. These fields belong to the internal progress registry. UI/API uses shared `availability=planned|available|unavailable|unsupported` and `evidence_level=none|unit_verified|local_integration_verified|live_lab_verified`; coordinator maps registry to manifest instead of exporting competing enums.

| Gate | Entry conditions | Exit conditions | Does not establish |
| --- | --- | --- | --- |
| Q0 Contract | Coordinator-approved design/DTOs | Validated schemas/examples and explicit ownership/dependencies | Running backend |
| Q1 Module | Valid dependency stubs | Passing unit/seam tests including errors | DB/network/live scanner success |
| Q2 Local integration | Foundation + merged lane | Passing PostgreSQL/API/files/process integration | Full UI workflow or live coverage |
| Q3 Frontend contract | Appointed agent hands off UI | Passing mock E2E/component tests; honest states | Platform E2E success |
| Q4 Full stack | Actual UI/API/worker/DB/report connections | Browser request→review→snapshot→PDF with matching IDs/hash | Real scanner/provider if inputs are fixtures |
| Q5 Live lab | ROE, lab profiles, egress gate, native sources | Nmap/ZAP receipts + native Greenbone import and trace | Confirmed exploitation, calibrated confidence, or production readiness |
| Q6 Release review | Q0–Q5 evidence or recorded limitations | Manual review, known gaps, actual run denominators | Passes for skipped/blocked cases |

One gate can be `blocked` while another lane continues. Do not mark all of R05 passed with only two of three integrations: report 2/3 and the missing integration. Missing model credentials block live LLM cases; deterministic fallback remains separately testable and labeled.

Q gates are QA checkpoints, not replacements for master gates. Mapping: G0→Q0; G1 foundation→Q1/Q2 prerequisites; G2 module→Q1/Q3; G3 integration→Q2/Q4; G4 lab→Q5; Q6 is the final review of applicable evidence.

PDF section 9.5 requires a human-approval demonstration for active validation and an action/outcome audit trace. The baseline MVP lacks an active-validation adapter. A gate-only/fake-runner demonstration verifies controls and leaves this deliverable unresolved; never claim approved exploitation occurred. Any future adapter requires explicit organizer authorization and a separately reviewed, exact lab action before implementation/execution.

## 2. Test data and environment ownership

| Fixture | Content and provenance | Purpose |
| --- | --- | --- |
| F-SYN-A/B | Two synthetic assessments, same actor, different assets/IPs/paths; no live scan | Isolation, UI contracts, negative policy |
| F-NMAP | Native isolated-lab XML, raw bytes/SHA-256, scanner version/profile/time/ROE | Network parsing/live trace; synthetic samples are unit-only |
| F-ZAP | Native lab packaged baseline JSON `-J`, receipts, bounded crawl/time | Web parser/live trace; no claim of full authenticated coverage |
| F-GB | Valid native Greenbone XML, export version/source/collection/import times and usage rights | Third import-only integration; absent input blocks R05 |
| F-CORR | Reasoned pair labels: native duplicates, compatible web weakness, different assets/paths, same CVE on different endpoints, historical conflict | Precision/recall on a finite labeled pair set |
| F-HOSTILE | Malformed/oversized XML, external entity, hostile HTML, traversal filename, B's source IDs | Parser/storage/report/UI negative cases |

Review/redact native provenance and store checksum manifests; never publish secrets/lab-private data. Mark synthetic fixtures in manifest/UI/report. Use dedicated databases/volumes/projects by run ID; never reset an existing user DB. Anonymous tests use separate browser contexts/sessions, not reused authenticated cookies.

## 3. Automated case catalog

Setup/action is mandatory fixture/assertion behavior, not merely a test name. `U` unit; `C` contract; `I` local integration; `B` browser; `L` live lab.

| ID / requirement | Layer | Setup and action | Expected result / assertion |
| --- | --- | --- | --- |
| A01 R01 | I+B | Create A with a natural-language request, target/scope/ROE; reload in a new session | Persisted request/scope; new draft has no fabricated findings; consistent assessment ID |
| A02 R01,R02 | I | Request “scan the entire Internet” in A, authorized for one lab host | Scope unchanged; out-of-scope proposals denied and audited |
| A03 R02,R15 | U+I | Exclude host/port; propose then dispatch the excluded destination | Policy and dispatch deny; runner call count=0 |
| A04 R02,R10 | I | Approve action v1, revise scope to v2 before worker claim | Stale action; contract 409/domain denial; no process spawn |
| A05 R02,R15 | L | Redirect lab server to an out-of-scope sink; try disallowed DNS/IPv6 | Egress denies connection; sink receives no request; reason trace. Without gate, live disabled |
| A06 R03 | U+I | Two snapshots: one with HTTP basis observation, one without HTTP | ZAP selected only with valid HTTP basis; otherwise valid discovery/review/stop |
| A07 R03,R13 | U+I | Model references nonexistent, foreign-assessment, or stale evidence | Semantic rejection; no canonical plan/state mutation or dispatch |
| A08 R03,R12 | U+I | Invalid model schema, unsupported action, timeout, exhausted budget | Typed outcomes; finalize/pause/partial; labeled fallback; no fabricated evidence |
| A09 R04 | I | Fake bounded process returns 0 with valid artifact, then nonzero | Success has receipt/artifact; nonzero failed/partial keeps actual exit/raw bytes |
| A10 R04,R12 | I | Hang past timeout; cancel running process; record process-group IDs | timed_out/cancelled; children stop; preserve partial artifacts; no false success |
| A11 R04,R12 | I | Kill worker after dispatch before receipt; expire lease; restart | Attempt/receipt reconciliation; unknown if uncertain; no blind scanner retry |
| A12 R05,R06 | L+I | Run lab Nmap TCP connect/version-light and parse native XML | Live receipt/version/argv/hash; correct service observations; open port is not vulnerability |
| A13 R05,R06 | L+I | Run bounded ZAP packaged baseline with JSON `-J` | Observations retain rule/location/confidence/raw locator; disclose profile/crawl limits |
| A14 R05,R06 | I | Import native F-GB and inspect timestamps/source/records | Working import-only integration; distinguish observed_at/imported_at; no fake live receipt |
| A15 R06,R15 | I | Upload malformed/oversized/unsupported XML and external entities | Contract 422/413/415 as applicable; external resolution disabled; traceable raw/errors; no empty success |
| A16 R06,R12 | I | Repeat file/key; reuse same key with different body | One import/observation set; changed body→409; hash deduplication preserves source context |
| A17 R07 | U+I | F-CORR contains native-identity duplicates and compatible mapped pairs | Correct rule/version merges; preserve every observation/raw reference |
| A18 R07 | U+I | Same title/CVE across different assets/services/paths/methods/parameters | Separate instances; ambiguous/historical pairs related/needs_review, not auto-merged |
| A19 R07,R08 | I+B | Analyst rejects/links candidate with reason, then unlinks/reviews | Membership/history records actor/time/reason; preserve sources; reject foreign links |
| A20 R08 | I | Trace finding→membership→observation→artifact and hash bytes | Every included finding has valid source links and matching SHA-256; broken link fails report gate |
| A21 R08,R15 | I | Download A's artifact under B, anonymously, and with traversal filename | 404/401; no path/byte leak; sanitized filename; private storage |
| A22 R09 | U+I | Unknown CVSS/exposure, severity conflict, low confidence/high impact | Preserve unknowns; reason/version/input provenance for priority; original severity unchanged |
| A23 R10 | I | Pending/rejected/expired approval; forged actor; changed parameters after grant | No authorize_dispatch permit; authenticated actor; complete audit; runner count=0 |
| A24 R10,R12 | I | Two workers claim approved action; reuse consumed grant | One permit/attempt; atomic grant consumption/dispatch reservation after job claim; no duplicate process |
| A25 R11 | I+B | Create A snapshot, change finding, render/download A, then create B | A's hash/revision immutable; B has new ID; PDF includes 7.1–7.6 and A's severity totals |
| A26 R11,R15 | U+I | Render hostile scanner HTML/external file URL/oversized snapshot | Escaped text; no network/local-file fetch; bounded failure outcome, never ready |
| A27 R11,R13 | I | Report partial scans, unsupported tools, historical imports, model fallback | PDF text includes limitations/approvals/failures/timestamps and fact/inference labels |
| A28 R12 | I+B | Poll queued/running/partial/failed timeline; repeat mutation key | Actual state progression; monotonic outcomes per attempt; no invented percent or duplicate actions |
| A29 R13 | U+I+B | AI hypothesis cites sources; compare raw artifact before/after | Raw bytes/hash unchanged; inference is not scanner observation; fabricated references rejected |
| A30 R14 | C+B | Matrix includes Nmap/Nessus/Greenbone/Nikto/ZAP/Burp/Metasploit | Every tool has mode/readiness/limitations/evidence; unsupported tools cannot run |
| A31 R14 | C+B | Load planned feature; explicitly enable mock preview | “In development”; disabled operation; no mutation/fake success; always-visible mock banner |
| A32 R14 | B | Previously available backend times out/503/network failure | Connection error/retry; stale-labeled cached data if used; no planned/empty-success substitution |
| A33 R15 | I | Artifact/PDF errors and scanner payload containing a synthetic token | Redaction preserves integrity metadata; no actual credentials in UI/PDF/log; no public stack traces |
| A34 R01–R15 | B+I | Actual UI→API→worker with fixture import→review→snapshot→PDF | Continuous IDs/hashes; record full_stack_fixture_verified run mode, not live_verified |
| A35 R01–R15 | B+L | Repeat with live Nmap/ZAP + native Greenbone import | Receipts/artifacts/source versions/ROE; explicit remaining limitations; no mocked endpoints |

A05/A12/A13/A35 need actual lab and sink/egress logs; unit URL validation is insufficient. A14 requires verified native provenance to count as the third integration. A34 is useful fixture E2E but does not establish R05 live acceptance. A34/A35's broad requirement labels indicate workflow context, not automatic passage of every requirement.

### Separate evaluation extensions and structural checks

The [competition metrics and real-world validation plan](../../research/COMPETITION_METRICS_AND_REAL_WORLD.md) defines E01–E12 separately from the unchanged 35-case A01–A35 catalog. E01–E04 cover evidence-dependent choices, grounded rationales, provider/baseline comparison, and ablation; E05 native mapping; E06 correlation holdout; E07 adjudicated finding correctness; E08 risk policy; E09 approval/destination controls; E10 malicious evidence; E11 report audit; E12 recovery/efficiency. Preserve these IDs and their declared denominators in run manifests. Targets in that research document are proposed acceptance goals, not observed results or guaranteed rubric scores.

Within existing module tests and relevant E experiments, also verify the [architecture fit review](../../research/ARCHITECTURE_FIT_REVIEW.md) corrections: persisted isolated conversation/decision records survive restart without duplicate model invocation; scan/import/report jobs share worker infrastructure but keep distinct domain states; rendering retries the same immutable snapshot without scanner calls; CVSS vector/version/source and analyst risk inputs retain provenance/unknowns; unimplemented active validation remains denied despite a UI approval. These checks do not add fabricated passing cases or close the unresolved PDF section 9.5 deliverable.

## 4. Manual runbook with steps, expectations, and evidence

Run after the applicable Q3/Q4 gate. Every case records run/build/revision, browser/viewport, and related automated IDs. Inspecting the original prototype alone cannot pass platform acceptance.

| ID | Prerequisites and steps | Required observation | Evidence and cleanup |
| --- | --- | --- | --- |
| M01 Frontend before backend | Appointed agent's UI build; backend feature incomplete. Open assessment/planner/import/report; attempt missing actions | “In development” plus brief limitation; disabled mutations; no completion toast or silent fake data | Screenshots per page + zero-mutation network trace; close session; retain test data |
| M02 Transparent mocks | Enable explicit mock mode; enter request/create draft; reload; switch to backend mode | Demo banner; fixture-only results; no live-record mixing or silent fallback | Secret-free banner/config screenshot, browser trace; reset mock only through test-profile UI |
| M03 Backend loss | Previously ready backend; open real finding; stop test API; refresh/poll; restart | Connection error/retry; no “In development” or fabricated zero findings; correct recovery | API timestamps/screenshots/network logs; restart API; retain volumes |
| M04 Assessment isolation | A/B exist; A has finding/artifact/report. Select B; inspect search/drawer/timeline and A's URL under B | No A data in B; backend denies wrong assessment; back navigation clears A's selected finding | IDs/status/screenshots; retain both test assessments |
| M05 Approval | Pending permitted lab action: deny with reason; create another proposal and approve; add stale-scope case | Server-derived reviewer; visible reason/time/hash/outcome; denied/stale never run; approved runs only after lab gate | Audit JSON, action/attempt IDs, process receipts, scope versions; stop lab afterwards |
| M06 Evidence/review | Finding→observation→raw; download/hash; reject false positive with reason; reinspect sources | Intact source/hash; validation separate from execution; confidence not called probability | Before/after manifest/hash, screenshots/review event; never modify raw |
| M07 PDF quality | Generate multilingual Unicode fixture report with long titles/paths and many findings; download; change review; redownload old report | All 7.1–7.6 sections; correct fonts/layout/no truncation; snapshot-consistent numbers; immutable prior report | PDF/snapshot/hash, page checklist, IDs; retain issued report. Authored product copy stays English |
| M08 Responsive/accessibility | 1440/390 px; keyboard tab/enter/escape; sidebar/dialog open/close; import error | No overflow; visible/restored focus; labeled dialogs; textual errors beyond color; correct busy/disabled state | Screenshots/short trace/console; close overlays |
| M09 Failure disclosure | Controlled timeout/cancel in isolated lab; invalid import; partial report | Timeline/overview/report disclose failures and incomplete coverage; absence of findings does not mean safe | IDs/exit/receipt/limitations; terminate test processes and stop lab |
| M10 Integration matrix | Inspect after Nmap evidence, then ZAP, then native import | Per-feature evidence-grounded state; all seven tools; no blanket completed status | Registry/screenshots across builds; never edit registry merely to stage a demo |

## 5. Infrastructure and acceptance tasks

### Task QA1: Contract fixtures and case registry

**Proposed files:** `backend/tests/conftest.py` (foundation-owned), `backend/tests/fixtures/manifest.json`, `tests/acceptance/cases.json`, `tests/acceptance/run.schema.json`, `docs/implementation/evidence/README.md`.

**Interface:** Each case has `id`, `requirements`, `layer`, `owner_role`, `fixture_ids`, `expected`, and `status`. Each run has `run_id`, `build_id`, `started_at`, `environment`, `cases`, and `artifact_manifest`. Outcomes are pass/fail/blocked/skipped/not_run with `reason` and evidence paths; blocked/skipped require a reason. Run mode such as `full_stack_fixture_verified` is metadata, not a new shared evidence_level enum.

- [ ] QA1.1 Write schema tests rejecting unknown requirements, evidence paths escaping run directories, and passes without assertion evidence.

```python
def test_pass_requires_evidence(validate_run):
    run = {
        "run_id": "local-001", "build_id": "reviewed-build",
        "cases": [{"id": "A20", "status": "pass", "evidence": []}]
    }
    errors = validate_run(run)
    assert any("evidence" in error for error in errors)
```

QA1.3 creates `validate_run(document: dict) -> list[str]`; these synthetic IDs/build names are never actual acceptance records.

- [ ] QA1.2 Run `python -m pytest tests/acceptance/test_run_schema.py -q`; observe RED.
- [ ] QA1.3 Create `tests/acceptance/test_run_schema.py` and `scripts/validate_acceptance.py`; validate JSON Schema, then cross-reference cases/requirements/artifact hashes. Fixture producers record source/version/hash/license/redaction instead of anonymous XML.
- [ ] QA1.4 Reach GREEN; coordinator reviews backend/frontend enums/routes/examples. Frontend generates mocks/types from frozen schemas, never independently changes server DTOs.

### Task QA2: Module/integration gates and controlled fault injection

**Proposed files:** `backend/tests/integration/test_acceptance_flow.py`, `backend/tests/integration/test_isolation.py`, `backend/tests/integration/test_dispatch_races.py`, `tests/acceptance/test_run_schema.py`; each module plan owns its tests.

**Interface:** Foundation supplies isolated PostgreSQL fixtures/authenticated actor factories. Worker harness injects a fake runner with call receipts; live runner is a separate opt-in fixture, never silently swapped under the same name.

- [ ] QA2.1 Turn A01–A30/A33 and the structural checks below into module-owner assertions. QA adds cross-module tests without duplicating implementation-lane tests. Fault injection uses explicit test hooks for storage commit failure, worker crash, and clock expiry.
- [ ] QA2.2 Write a consistent-assessment trace test:

```python
def test_report_chain_stays_in_one_assessment(full_flow_fixture):
    result = full_flow_fixture.run_native_import_review_report()
    assert result.report.assessment_id == result.assessment.id
    assert all(o.assessment_id == result.assessment.id for o in result.observations)
    assert result.download_sha256 == result.report.artifact_sha256
    assert result.runner_calls == 0  # import-only fixture flow
```

`full_flow_fixture` actually calls API/auth/worker/DB/files and records fixture mode. Do not mock report services merely to assert the same mocked data.

- [ ] QA2.3 Observe RED before integration; route seam failures to owners without weakening the contract assertion. After foundation dependency/editable installation, run from the backend package root:

```bash
cd backend
python -m pytest tests/unit tests/integration -q --junitxml=../docs/implementation/evidence/local-backend/backend.xml
```

Run acceptance-schema checks separately from workspace root: `python -m pytest tests/acceptance -q`; do not assume root imports the src package automatically.

- [ ] QA2.4 Reach GREEN with process cleanup and fixture rollback or deletion of verified test-owned DBs by prefix/run ID. Do not affect unrelated volumes.

### Task QA3: Frontend contracts and full-stack browsers

**Proposed frontend-owned files:** `frontend/tests/contract/`, `frontend/tests/e2e/`; coordinator agrees actual framework/commands before execution. QA supplies A01/A19/A28/A30–A35 and applicable structural checks and M01–M10 instead of scaffolding frontend.

- [ ] QA3.1 Frontend owner creates planned/in_progress/ready/error/empty/unsupported page tests, including no mutation for M01 and no silent mock fallback for M03. These are view/task labels; API availability follows the shared enums.
- [ ] QA3.2 Save labeled mock-browser traces; verify assessment switch/keyboard/mobile/sidebar/modal/errors. Run the command declared in frontend's manifest; do not invent npm commands before stack selection.
- [ ] QA3.3 Integration owner runs A34 with actual API and all intercepts/mocks disabled; archive redacted endpoint trace/IDs/PDF/hash. Distinguish Q3 mocks from Q4 full stack.
- [ ] QA3.4 Run applicable M01–M10; review screenshots/PDF/console. Record remaining issues fail/blocked with an owner; never relabel skipped to pass a gate.

### Task QA4: Live lab acceptance and release manifest

**Proposed files:** `scripts/run_acceptance.py`, `docs/implementation/evidence/<run-id>/summary.md`, `docs/implementation/evidence/<run-id>/manifest.json`; create scripts when implementation begins. Sensitive artifacts are not committed; publish only reviewed redacted manifests.

- [ ] QA4.1 Verify ROE/lab ID/targets/ports/profiles/deadline, egress-denial evidence, and F-GB source. Missing prerequisites block dependent cases while independent cases continue.
- [ ] QA4.2 Run A05/A12/A13/A35 in an isolated test project. Capture tool image/version/profile, normalized target, action hash/scope version, attempt/job IDs, start/end/exit code, raw SHA-256, parser version, and sink logs.
- [ ] QA4.3 Compare requirement mappings: R01 A01–02; R02 A02–05; R03 A06–08; R04 A09–13; R05 A12–14; R06 A12–16; R07 A17–19; R08 A19–21; R09 A22; R10 A04/A23–24; R11 A25–27; R12 A08–11/A16/A24/A28; R13 A07/A27/A29; R14 A30–32; R15 A03/A05/A15/A21/A26/A33. A34/A35 happy paths never replace negative cases. Track section 9.5 active-validation demonstration as an explicit open gap while no permitted adapter/outcome exists.
- [ ] QA4.4 Generate summaries from actual run JSON with denominators per layer: unit pass/total; integration pass/fail/blocked/total; verified integrations/required integrations; manual pass/not_run/total. Earlier illustrative counts are not measured results. Skipped/blocked cases never count as passes; do not equate case pass rates with rubric points.
- [ ] QA4.5 Validate manifests; reviewer samples artifacts/hashes/PDF. Stop test-owned services/processes while retaining volumes/evidence. Release claims only verified scope with open gates; no unsupported “low FP”, “exploit confirmed”, or “production ready” claim.

## 6. Agent result format

```text
Task / build / owner:
Files changed:
Contract revision consumed:
Tests run (exact command + environment):
Passed / failed / blocked / skipped / not_run:
Evidence paths (logs, IDs, hashes, screenshots, reports):
Verification level (unit / mock browser / local integration / full stack / live lab):
Limitations and handoff dependencies:
```

Each lane submits code review/test evidence; coordinator alone updates readiness. Merged code without integrated API may still display “In development”; runtime unavailability displays its own operational error. This plan contains no pre-recorded passing test results.

## Follow-up research evaluation inputs

The [readiness report](../../research/READINESS_DECISION_REPORT.md) links the concrete G0/scanner/provider/launcher decisions. Preserve A01–A35/M01–M10; P01 (provider compatibility) and V01–V14 (launcher/network/recovery/pilot) are separately identified proposed checks, not extra passing A-cases. Run network proof independently for local_internal and remote_routed modes. Add reservation-versus-final-start scope races and restore-generation non-replay to the relevant acceptance assertions. Public fixture hash/structure inspection is documentary source evidence, not application parser or R05 acceptance. No new case is pre-marked pass.
