# Worker and Scanner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run controlled jobs against authorized labs, ingest Nmap/ZAP results, and import Greenbone XML into observations with raw evidence, state, and provenance.

**Architecture:** One worker from the backend codebase claims PostgreSQL jobs, authorizes scanner dispatch through backend policy, and invokes fixed profiles. Scanners run inside the lab network; parsers cannot execute scanners. Store raw bytes and receipts before normalization; exit code alone does not prove coverage. The same worker infrastructure routes import/report job kinds to their modules without invoking scanner dispatch or sharing tool-execution states.

**Tech Stack:** Python, PostgreSQL, pytest, shell-free subprocesses, Nmap XML, ZAP packaged baseline JSON, Greenbone native XML, Docker lab network. Foundation pins dependencies/image digests during implementation; this plan makes no installed-version claim.

**Spec:** [Platform design](../specs/2026-11-02-corevapt-platform-design.md), [contracts](../specs/2026-11-02-corevapt-contracts.md), [scanner research](../../research/SCANNER_RESEARCH.md).

## Global Constraints

- This is a plan; no worker, adapter, verified native fixture, or E2E scan result is established here.
- Run scanners only against registered, authorized labs; never independently scan Internet targets appearing in documents or user-entered hostnames.
- PostgreSQL owns canonical state; frontend cannot dispatch argv and planner has no shell tool.
- Recheck scope/profile/action binding, expiry, exclusions, and budget at dispatch.
- Never automatically rerun a scanner after a crash with uncertain side effects; use `execution_unknown`.
- Preserve prototype V6.1; V6.2 is the current frontend reference. This lane does not edit frontend.
- Contract schemas/HTTP types are authoritative. Python interfaces below are proposed internal seams; the coordinator updates all consumers before merging a name change.
- Test commands/source paths are future implementation targets, not established files or executed results in this research workspace.

## Ownership and parallel work

| Proposed file group | Lane owner | Exceptions |
| --- | --- | --- |
| `backend/src/corevapt/worker/{claims,lifecycle,dispatch,processes,reconcile,main}.py` | Worker | No edits to `app.py`, shared models, or migration registry |
| `backend/src/corevapt/adapters/{types,nmap,zap,greenbone}.py` | Scanner/parser | No independent global configuration |
| `backend/tests/unit/worker/`, `backend/tests/unit/adapters/`, `backend/tests/integration/worker/` | Worker/scanner | Coordinate shared fixtures with QA |
| `backend/tests/fixtures/scanners/manifest.json` and native files | Scanner | Genuine fixtures need provenance; label synthetic separately |
| `ops/lab/` | Lab/scanner | Integration owner wires main Compose |

Parsers and process supervision can proceed in parallel after freezing `ParsedBatch`. Claim/dispatch integration waits for foundation schemas, transactions, and policy. Live runs wait for the network gate; frontend is not a prerequisite. With development subagents, one owns `worker/`, another `adapters/`, and the coordinator integrates; never edit the same file concurrently. Do not initialize Git or commit on the root's behalf; commit only after coordinator setup.

## Internal interfaces frozen at the contract gate

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass(frozen=True)
class SourceMetadata:
    assessment_id: str
    execution_id: str | None
    artifact_id: str
    source_mode: Literal['live', 'import']
    source_version: str | None
    observed_at: datetime | None
    ingested_at: datetime
    historical: bool

@dataclass(frozen=True)
class ObservationDraft:
    native_id: str
    kind: Literal['host', 'service', 'vulnerability']
    asset: str
    protocol: str | None
    port: int | None
    location_raw: str | None
    rule_id: str | None
    severity_raw: str | None
    severity: Literal['critical', 'high', 'medium', 'low', 'informational', 'unknown']
    confidence_raw: dict
    raw_locator: str
    fields: dict

@dataclass(frozen=True)
class ParsedBatch:
    observations: tuple[ObservationDraft, ...]
    warnings: tuple[str, ...]
    completeness: Literal['complete', 'partial', 'unknown']
    source_metadata: SourceMetadata

# adapters expose parse(raw_bytes: bytes, source: SourceMetadata) -> ParsedBatch.
# Parser rejection exposes code: malformed | unsupported_format |
# unsafe_xml | resource_limit; raw artifact is retained on failure.
```

The contract owner manages public DTOs in `backend/src/corevapt/contracts.py`; adapter-local types are internal parser types only. Foundation provides `get_session`, `require_analyst`, `append_event`, artifact `put_bytes/read_bytes`, and scope `get_snapshot`. The findings ingestion owner persists `ParsedBatch` through the shared transaction/artifact interfaces with assessment/artifact FKs and parser version; the parser never commits DB state. `confidence_raw` is a source-labeled map (`service_conf`, `zap_confidence`, `qod_value`, `qod_type`), not a common probability. At G0 replace draft unbounded `dict` fields with bounded source-specific schemas; preserve CVSS score/vector/version/source when a native format supplies them.

Policy provides `authorize_dispatch(action_id, attempt_id) -> DispatchPermit`. Worker identity/clock come from trusted dependencies, never client bodies; private transaction helpers may accept explicit worker_id/now for tests. The reservation transaction checks current scope/hash/approval and binds the grant/budget exclusively to the attempt. After preparation, trusted-launcher `authorize_start` rechecks scope/fence/cancel/preparation and atomically consumes the grant. Public execution remains queued until an actual scanner-start receipt; internal preparation and generic job running are distinct. `DispatchPermit` contains only canonical action, executable profile ID/version, normalized target/ports, deadline, budget, artifact prefix, and attempt ID. Workers never create approval; successful API enqueue does not authorize spawn.

`ProcessResult` contains `exit_code`, `started_at`, `finished_at`, `termination_reason`, `stdout_path`, `stderr_path`, `output_paths`, and `process_identity`. `termination_reason`: `completed|timeout|cancelled|output_limit|spawn_failed`. The worker generates every output path inside the attempt directory. Receipts record tool/image version, redacted argv, scope/action hash, and artifact IDs; a receipt is not a vulnerability conclusion.

Generic jobs need `kind=scan|import|report`, resource ID, attempt/lease identity, queued/running/terminal job state, and failure metadata, frozen by the foundation/contract owner. A scan job links a tool execution whose domain states include `partial`, `timed_out`, `cancelled`, and `execution_unknown`; a report job links report state `pending|rendering|ready|failed`. Never mark a report as a successful scan or require a scan approval merely to render a frozen snapshot.

## Task WS-01: Parser contract and fixture provenance

**Files:** Create `backend/src/corevapt/adapters/types.py`, `backend/tests/fixtures/scanners/manifest.json`, `backend/tests/unit/adapters/test_contract.py`.

**Consumes:** Shared enums/IDs and artifact ownership. **Produces:** The types above and a manifest for every raw file.

- [ ] Write the initial contract test and run `cd backend && python -m pytest tests/unit/adapters/test_contract.py -q`; confirm failure because the module does not exist yet.
- [ ] Create immutable types and validate source mode/locators; foundation's persistence seam rejects cross-assessment artifact references.
- [ ] Record file, SHA-256, scanner/version, mode, export command/profile, collection time, lab/authorization reference, filters/pagination, redaction, license/provenance permission, and expected record count. Missing native fixtures block adapter acceptance; never relabel synthetic data as native.
- [ ] Create separately named `synthetic-*` fixtures for errors/edge cases. Use genuine native fixtures for integration acceptance; do not promise native files before obtaining them.
- [ ] Run contract tests, review manifests/raw hashes, and commit only task-owned files after Git setup.

Example contract test without a live scanner:

```python
def test_import_does_not_invent_execution(source_factory):
    source = source_factory(source_mode='import', execution_id=None,
                            observed_at=None, historical=True)
    assert source.execution_id is None
    assert source.observed_at is None
    assert source.historical is True
```

## Task WS-02: Nmap XML parser and fixed profile

**Files:** Create `backend/src/corevapt/adapters/nmap.py`, `backend/tests/unit/adapters/test_nmap.py`, and native/synthetic fixtures under `backend/tests/fixtures/scanners/nmap/`.

**Consumes:** `SourceMetadata`, raw artifact bytes. **Produces:** `parse(raw_bytes, source)->ParsedBatch`; `build_argv(target: str, ports: tuple[int,...], output_file: str, timeout_s: int)->tuple[str,...]`.

- [ ] Write W-N01..W-N06 and confirm import failure before implementation with `cd backend && python -m pytest tests/unit/adapters/test_nmap.py -q`.
- [ ] Parse XML with external entities/network resolution disabled and bounded size/depth/record count. Accept legitimate Nmap DOCTYPE without fetching a DTD; never alter raw bytes merely to make parsing succeed.
- [ ] Map host/address, protocol/port/state/reason, service method/conf, product/version/CPE when present. Missing version remains null; an open port does not become a vulnerability.
- [ ] Catalog profile `nmap_discovery_v1` (display label network-service-discovery): TCP connect, light service detection, numeric lab IP, exact allowed ports, host timeout, low concurrency. No `-A`, arbitrary scripts, or user flags. Proposed argv: `('nmap','-sT','-sV','--version-light','-n','-Pn','-p',ports,'--host-timeout',deadline,'-oX',output,target)`; verify flags against the pinned binary in the lab before acceptance.
- [ ] Determine complete/partial from end-of-scan state, output completeness, and receipt. A valid truncated subset does not establish full-scan success.
- [ ] Run tests, check native manifests, and commit after review.

| Case | Input | Expected |
| --- | --- | --- |
| W-N01 | Native output: TCP 80 open HTTP, service conf 7 | Service observation, raw conf 7, port locator; no vulnerability |
| W-N02 | Open port without version | version=null; no inferred CVE |
| W-N03 | Valid DOCTYPE | Parse without network DTD fetch |
| W-N04 | External entity and nested expansion | Safe rejection; preserve raw; no file/network read |
| W-N05 | Truncated XML or missing runstats | Partial/failed diagnostic; no complete-coverage claim |
| W-N06 | Shell metacharacters or disallowed target/port | No argv/spawn; auditable policy denial |

```python
def test_discovery_is_not_a_vulnerability(native_nmap_bytes, source_factory):
    from corevapt.adapters.nmap import parse
    batch = parse(native_nmap_bytes, source_factory())
    assert any(o.kind == 'service' and o.port == 80 for o in batch.observations)
    assert not any(o.kind == 'vulnerability' for o in batch.observations)
```

## Task WS-03: ZAP packaged baseline parser and result classification

**Files:** Create `backend/src/corevapt/adapters/zap.py`, `backend/tests/unit/adapters/test_zap.py`, `backend/tests/fixtures/scanners/zap/`.

**Consumes:** Full baseline `-J` report JSON, source metadata, receipt. **Produces:** `parse(raw_bytes,source)->ParsedBatch`; fixed `zap_baseline_v1` invocation specification for the lab launcher.

- [ ] Write W-Z01..W-Z06 and run `cd backend && python -m pytest tests/unit/adapters/test_zap.py -q` to observe failure before implementation.
- [ ] Support only the pinned image's full report schema; reject API alerts JSON explicitly instead of guessing a generic parser.
- [ ] Preserve site, plugin ID/alert ref, instance URI/method/parameter/evidence, raw risk/confidence, description/solution/references/CWE; rule ID is not the title. Keep missing/unknown values and warn about missing fields.
- [ ] Use only packaged baseline, with fixed target/port/context/deadline and full JSON in private attempt output. Do not add daemon API orchestration or active scanning here.
- [ ] During implementation, read the pinned version's exit semantics: alert/policy exit differs from runtime failure. Alerts in a complete report do not automatically mean scanner failure; a missing report cannot mean success. Record caps/truncation/phases in receipts.
- [ ] Run tests, review native raw-to-observation mapping, and commit.

| Case | Input | Expected |
| --- | --- | --- |
| W-Z01 | Native full report, two instances of one plugin | Two instance observations preserving rule and URI/method/parameter |
| W-Z02 | API alerts JSON | unsupported_format, raw retained |
| W-Z03 | Empty alert list after completed scan | Complete empty batch; no claim that asset is safe |
| W-Z04 | Missing report and nonzero runtime exit | Failed diagnostic, no fake finding |
| W-Z05 | Alert-driven exit and valid complete report | Pinned exit mapping determines outcome; ingest alerts |
| W-Z06 | HTML/script in evidence fields | Preserve raw; never execute; escape downstream display |

```python
def test_alert_instances_keep_locations(native_zap_bytes, source_factory):
    from corevapt.adapters.zap import parse
    batch = parse(native_zap_bytes, source_factory())
    locations = {(o.fields['uri'], o.fields['method'], o.fields.get('parameter'))
                 for o in batch.observations}
    assert ('http://lab-web:8080/login', 'GET', None) in locations
    assert ('http://lab-web:8080/app', 'GET', None) in locations
```

The fixture task creates exactly these two URIs; this hostname is only a fixture/lab name, not authorization for an external target.

## Task WS-04: Greenbone native XML import

**Files:** Create `backend/src/corevapt/adapters/greenbone.py`, `backend/tests/unit/adapters/test_greenbone.py`, `backend/tests/fixtures/scanners/greenbone/`.

**Consumes:** Size-checked uploaded artifact/source manifest and foundation import ID. **Produces:** `parse(raw_bytes,source)->ParsedBatch`, diagnostics, and raw locators; no live capability.

- [ ] Write W-G01..W-G07 and confirm failure with `cd backend && python -m pytest tests/unit/adapters/test_greenbone.py -q`.
- [ ] Identify supported native report/GMP wrapper using genuine exports. Select the actual nested data report; do not glob every result and mix duplicates/deltas.
- [ ] Map report/task/result UUIDs, host/hostname, original port/location, NVT OID, description, severity/original override, QoD value/type, references/solution. `general/tcp` has port=null with raw location retained; do not split IPv6 blindly on colons.
- [ ] Apply Nmap-equivalent size/depth/entity/record limits. Reject unsupported roots/HTML/PDF/Base64 reports; zero results alone does not establish successful import.
- [ ] Record collection time separately from imported_at; anonymized/historical fixtures do not auto-correlate with live assets. Completeness is unknown without filters/pagination/source counts.
- [ ] Coordinate uniqueness `(assessment_id, artifact_sha256, parser_version)` with foundation. Same-key replay returns the original import without duplicate observations. New parser versions retain separate lineage and controlled active projections.
- [ ] Run tests and native provenance review; commit. Without a native export, status remains “In development”; synthetic tests do not establish working integration.

| Case | Input | Expected |
| --- | --- | --- |
| W-G01 | Native wrapper + nested report | One observation per native result |
| W-G02 | `general/tcp`, IPv6 host | port=null; intact host/location |
| W-G03 | QoD 80, missing severity | Raw QoD=80, severity unknown; no 80% exploitation confidence |
| W-G04 | Severity override | Preserve source/original/displayed values |
| W-G05 | Duplicate bytes in same assessment/parser | No duplicate observations |
| W-G06 | Entity expansion/oversized/unsupported root | Correct rejection code; retain raw after accepted upload |
| W-G07 | Filtered/old/anonymized export | Historical/limitations visible; no full-coverage claim |

```python
def test_general_port_is_not_zero(greenbone_general_bytes, source_factory):
    from corevapt.adapters.greenbone import parse
    batch = parse(greenbone_general_bytes, source_factory(source_mode='import',
                                                        execution_id=None))
    obs = batch.observations[0]
    assert obs.port is None
    assert obs.location_raw == 'general/tcp'
    assert obs.severity == 'unknown'
    assert obs.confidence_raw['qod_value'] == 80
```

## Task WS-05: Claims, leases, and stale-attempt fencing

**Files:** Create `backend/src/corevapt/worker/claims.py`, `backend/src/corevapt/worker/lifecycle.py`, `backend/tests/integration/worker/test_claims.py`.

**Consumes:** Foundation-owned generic-job/tool-execution schemas/repositories and session factory. **Produces:** `claim_next(worker_id,now)->Claim|None`, `heartbeat(execution_id,attempt_id,worker_id,now)->bool`, `complete_attempt(execution_id,attempt_id,outcome,receipt)->bool` for scan attempts. At G0, freeze generic claim methods over job IDs and explicitly map scan jobs to these execution-specific operations; do not use an execution ID to identify import/report jobs.

- [ ] Request worker/attempt identity, claim/lease timestamps, heartbeat, cancellation flag, lifecycle state, kind/resource reference, and immutable attempt receipt reference from foundation; coordinator owns migrations.
- [ ] Write PostgreSQL W-W01..W-W04 integration tests; run `cd backend && python -m pytest tests/integration/worker/test_claims.py -q` and confirm preimplementation failure. SQLite cannot establish PostgreSQL concurrency.
- [ ] Claim with a short row-locking/skip-locked transaction, new attempt ID, and lease; never retain a transaction through a scan. Only eligible queued jobs are claimable; policy separately authorizes scan dispatch.
- [ ] Heartbeat/completion conditionally update the current attempt/worker; stale attempts cannot overwrite newer results. Lease expiry never automatically requeues a running scan.
- [ ] Use barrier-synchronized workers to claim one job: one claim and, after dispatch integration, one spawn. Do not use arbitrary sleeps as concurrency assertions.
- [ ] Run tests, preserve counts/redacted SQL diagnostics, and commit.

| Case | Expected |
| --- | --- |
| W-W01: concurrent claims | One owner; no duplicate run |
| W-W02: wrong-attempt heartbeat | false; unchanged lease |
| W-W03: stale-attempt completion | false; unchanged current outcome |
| W-W04: running lease expires | Reconciliation; no scan replay |

## Task WS-06: Dispatch policy and bounded process supervision

**Files:** Create `backend/src/corevapt/worker/dispatch.py`, `backend/src/corevapt/worker/processes.py`, `backend/tests/unit/worker/test_processes.py`, `backend/tests/integration/worker/test_dispatch.py`.

**Consumes:** Policy `authorize_dispatch`, `DispatchPermit`, approved fixed profiles, artifact writer, claim interfaces. **Produces:** `dispatch(action_id,attempt_id,worker_id)->ExecutionOutcome`, `run_process(argv,deadline,cancel_signal,output_limit_bytes)->ProcessResult`.

- [ ] Write W-D01..W-D09; run `cd backend && python -m pytest tests/unit/worker/test_processes.py tests/integration/worker/test_dispatch.py -q` and confirm failure.
- [ ] Reserve the exact action/attempt/grant/budget in the foundation transaction. After namespace preparation, the trusted launcher calls final `authorize_start`, rechecks current scope/hash/time/exclusions/profile/budget/cancel/fence and consumes the bound grant. Scope updates share the final-start serialization rule. Denied/pending/stale grants never release a scanner; document post-authorization cancellation and the physical start gap.
- [ ] Live scanner execution uses the fixed host-launcher submit/status/cancel protocol from the safety decision report, never worker-supplied argv or a worker Docker socket. Persist intent, preparation/start/final receipts and fences. Local process supervision remains for safe test helpers, import/render jobs and launcher internals. Use a process group, `shell=False`, private temp/output directories, an environment allowlist without API/DB/model secrets, fixed executable, output cap, and hard deadline.
- [ ] On timeout/cancel, terminate the whole group, allow bounded grace, then kill. Drain bounded stdout/stderr without deadlock. Write receipts after stop, including partial output. Never interpret scanner text as shell code.
- [ ] Atomically publish raw output through artifact service; ingest only after manifest/receipt persistence. DB/storage failure retains reconciliation/orphan records and never returns succeeded.
- [ ] Map `succeeded|partial|failed|timed_out|cancelled` using receipts, artifact completeness, and adapter-specific exit semantics; policy denial is a separate decision event.
- [ ] Test with local helper processes that scan no network, then PostgreSQL dispatch tests; commit.

| Case | Expected |
| --- | --- |
| W-D01 pending/rejected/expired grant | Spawn counter=0; audit reason |
| W-D02 changed target/parameters/scope version | Conflict/deny; spawn=0 |
| W-D03 concurrent duplicate dispatch | One consumed grant, one spawned attempt |
| W-D04 timeout helper creates a child process | Entire group stops; timed_out + receipt |
| W-D05 mid-run cancel | cancelled; no false success |
| W-D06 stdout exceeds cap | Stop process; bounded artifact + truncation warning |
| W-D07 missing binary/nonzero runtime | failed + diagnostic; no fake observation |
| W-D08 DB commit fails after output | Raw retained; reconciliation required; no success |
| W-D09 scope revision races dispatch | Deterministic serialized winner; no stale approval dispatch |

```python
def test_pending_approval_never_spawns(dispatch_fixture):
    system = dispatch_fixture(approval_state='pending')
    system.dispatch()
    assert system.processes.spawn_count == 0
    assert system.audit.last_event.reason_code == 'approval_required'
```

This task creates `dispatch_fixture` from real policy/repositories plus a fake ProcessSupervisor. It proves backend enforcement, not live scanner execution or a real active-validation outcome.

## Task WS-07: Crash reconciliation and restart

**Files:** Create `backend/src/corevapt/worker/reconcile.py`, `backend/src/corevapt/worker/main.py`, `backend/tests/integration/worker/test_reconcile.py`.

**Consumes:** Attempt intents, persisted process/job identity, leases, and receipts. **Produces:** `reconcile_expired(now)->ReconcileSummary`, restart entrypoint, controlled inspection/cancellation.

- [ ] Write W-R01..W-R05; confirm failure with `cd backend && python -m pytest tests/integration/worker/test_reconcile.py -q`.
- [ ] Reconcile identity through container/job ID or PID plus start identity/attempt marker. PID existence alone is insufficient; never kill an unrelated process after PID reuse.
- [ ] After dispatch intent but before a persisted receipt, use execution_unknown and pending reconciliation unless no-spawn or actual process outcome can be established. Never blind-retry.
- [ ] Consistent artifacts+receipts permit idempotent reparse without rescanning. Missing/corrupt receipts remain unknown or failed with evidence-backed diagnostics.
- [ ] On worker shutdown, stop claims, reconcile active attempts, and apply bounded termination/cancellation. Restart must not treat old running scans as newly queued work.
- [ ] Route report jobs through the report module using immutable snapshot IDs. A renderer failure may retry the same snapshot under the report retry policy without reissuing scans or creating a new snapshot. Import retries likewise reparse immutable raw inputs idempotently. Freeze separate retry policies at G0.
- [ ] Run tests; manual crash injection belongs only to WS-08's lab; commit.

| Case | Expected |
| --- | --- |
| W-R01 provable pre-spawn crash | Controlled requeue only with auditable no-dispatch proof and explicit grant retry policy |
| W-R02 post-spawn, pre-receipt crash | Reconcile process or execution_unknown; spawn count unchanged |
| W-R03 reused PID | Do not kill unrelated process; unknown |
| W-R04 complete receipt/correct raw hash | Idempotent ingest; no live rescan |
| W-R05 missing receipt/raw or hash mismatch | Diagnostic/integrity failure; no fabricated success |

## Task WS-08: Lab egress gate and manual scanner acceptance

**Files:** Create `ops/lab/README.md`, `ops/lab/targets/`, `ops/lab/egress/`, `backend/tests/integration/worker/test_lab_egress.py`. Coordinator integrates main Compose/image pins; this lane supplies network/profile requirements.

**Consumes:** Authorized lab scope, fixed scanner images/binaries, grant workflow, test-only canary HTTP server. **Produces:** Live capability acceptance evidence or explicit blocked status.

- [ ] Build a disposable lab target with `/login`, `/app`, redirect to an out-of-scope canary, and A/AAAA DNS records. The canary belongs to the test harness but is excluded from assessment scope; do not use external websites for network-blocking tests.
- [ ] Scanner network cannot reach backend/DB/metadata endpoints or Internet; allow only target IPs/ports; v1 uses fixed hostname mappings and blocks DNS. Block unsupported IPv6 and verify actual denial, not configuration alone. Never mount Docker socket into API/planner/worker; Compose's host launcher uses fixed services.
- [ ] Worker submits only attempt/reservation/request IDs to the trusted host launcher. Both Nmap and AF-only ZAP run in attempt-bound namespaces under its fixed catalog; local_internal and remote_routed modes require independent acceptance. If launcher/egress is infeasible, keep ZAP live unavailable; do not bypass with a worker-mounted Docker socket.
- [ ] Write/run `cd backend && python -m pytest tests/integration/worker/test_lab_egress.py -q` in the isolated lab. Capture denied connections/canary request count and IPv4/IPv6/DNS/redirect outcomes.
- [ ] Manual M-W01: create exact host/port assessment + ROE; discovery → approval if required by ROE → Nmap. Preserve action/attempt IDs, raw XML hash, version, receipt, status screenshot, and port/service observation.
- [ ] Manual M-W02: use HTTP evidence to propose ZAP baseline → approve exact action → baseline. Preserve JSON hash, phases/truncation, raw alert source/confidence, and timeline. Baseline approval never enables active scanning.
- [ ] Manual M-W03: change scope after approval, then dispatch; expect deny/conflict and spawn=0. Repeat excluded port, stale hash, expired grant, and unauthorized reviewer with API owner.
- [ ] Manual M-W04: redirect/DNS-rebinding tests point to the harness canary; expect no out-of-scope requests and capture network logs. A canary request fails the release gate and disables the profile.
- [ ] Manual M-W05: kill worker after spawn and restart; expect reconciliation/unknown without rescan. Cancel/timeout a helper scan and inspect terminal states/raw diagnostics.
- [ ] Manual M-W06: import a native Greenbone file with manifest; compare selected native result IDs/locators/QoD/timestamps to API; replay without duplication. Always show imported mode and never create a live receipt.
- [ ] Coordinator runs joint QA E2E; commit docs/tests/evidence manifests after review. Never commit secret/PII raw files; use provenance-recorded redaction in the evidence pack.

## Acceptance gates and handoff evidence

| Gate | PASS condition | Evidence |
| --- | --- | --- |
| Parser | Native Nmap/ZAP/Greenbone mappings and negative cases pass | Test logs, fixture manifests/checksums, record denominator |
| Worker | Claim/grant concurrency, fencing, timeout/cancel/crash tests pass | PostgreSQL logs, receipts, spawn counts |
| Network | IPv4/IPv6/DNS/redirect cannot escape assessment scope | Canary counts, firewall/proxy logs, network/image versions |
| Live Nmap | Actual permitted lab discovery with correct outcome semantics | Action + attempt + receipt + raw artifact + observations |
| Live ZAP | Actual permitted baseline with disclosed phases/limits | Full JSON + receipt + provenance + limitations |
| Greenbone import | Genuine native export with verified source/count/mapping | Import ID + original hash + metadata + sample locators |

Evidence pack: `docs/implementation/evidence/<run-id>/worker-scanners.md` with UTC time, commit when available, image digests, exact commands, pass/fail/skip counts, lab scope ID, native/synthetic/live labels, and limitations. Availability and evidence_level are separate: unimplemented adapters/unaccepted native parsers remain planned (“In development”); implemented modules lacking binaries/egress/runtime prerequisites are unavailable. Callable modules may be available at a lower evidence_level without being live verified. Missing live gates never become live_lab_verified; parser/unit tests never become Live. Hand frontend the execution states, diagnostic reason codes, and capability readiness; do not provide fake success in production mode.

## Self-review before handoff

- [ ] R02/R04/R05/R06/R08/R10/R12/R15 have corresponding tasks/cases.
- [ ] Parsers never commit DB directly; frontend never owns policy. Worker routes report jobs to report-owned rendering and does not own report content or risk calculations.
- [ ] No independent edits to shared schemas/routes/Compose while another owner works there.
- [ ] Synthetic tests never establish completed native fixtures or live capabilities.
- [ ] All live commands require the isolated lab gate; additional targets need explicit scope/authorization.

## Follow-up research decisions

Use [scanner readiness](../../research/SCANNER_READINESS_DECISIONS.md) for exact native versions/selectors, AF-only ZAP/traditional-json/add-on pins and the WS-01 genuine fixture acquisition/fallback decision. Public reference bytes do not pass R05. The [G0 register](../../research/G0_CONTRACT_DECISIONS.md) supplies bounded first-slice types and proposed caps; schemas remain unimplemented.

WS-06/08 consume the [safety/recovery design](../../research/SAFETY_RECOVERY_PILOT_DECISIONS.md): trusted host launcher, wait shim, effective namespace rules, separate local/remote modes, reservation then final `authorize_start`, private immutable receipts and no blind replay. Coordinator owns new `ops/launcher/` integration files, privilege/runbook review and shared migrations; worker owner supplies adapter client and tests, avoiding shared-file writes. Import/report handlers remain outside scanner authorization. All V01–V14 safety cases are proposed extensions, not passing A-cases or live results.
