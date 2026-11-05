# CoreVAPT frontend 6.2 — requirements and assessment experience

Date: **2026-11-02**. Authorized scope for this frontend revision: read project context/PDF, update documentation, and revise the HTML prototype. No backend implementation, model calls, or scanner execution. User-provided V6.1 review notes informed the UX; the next version is **6.2**, not V7. This document specifies intended prototype behavior; observed checks belong in the separate verification record.

## 1. Direct source basis

The complete [root PDF](../../1.pdf) was read and compared with the [page-based extraction](sources/statement-1-extracted.txt). Root `1.pdf` and the [research copy](sources/statement-1.pdf) share SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

- §§1–3, pp1–2: reduce manual output combination/interpretation; select next steps from context/evidence and explain decisions. Request → planning → approved orchestration → ingestion → analysis → risk → human review → report.
- §5, pp3–4: scope, adaptive planning, execution/error handling, normalization/correlation, evidence/confidence, risk, approval, and reporting.
- §6, p5: at least three working integrations/imports spanning network and web; disclose all seven tool statuses. All seven live adapters are advanced scope, not the minimum.
- §7, pp5–6: downloadable PDF containing all six sections, 7.1–7.6.
- §§10–11, pp8–9: show decisions, outputs, and provenance. AI Reasoning & Decisions receives 20/100 points. UI quality alone does not demonstrate runtime capabilities.
- §13, p10: authorized labs only, no fabricated evidence, protected sensitive data, and auditable actions.

The original frontend research checked official documentation on **2026-11-02**: [ZAP baseline](https://www.zaproxy.org/docs/docker/baseline-scan/) spiders before passive analysis and supports JSON; [Nmap version detection](https://nmap.org/book/man-version-detection.html) sends probes. UI must disclose traffic instead of describing these profiles as impact-free. This is source verification, not runtime verification; translation did not rerun those external checks.

## 2. V6.1 issues and 6.2 decisions

| Issue from code/context | 6.2 decision | Acceptance condition |
| --- | --- | --- |
| Three tabs hide assessment stages | Six status-bearing steps: Scope, Plan, Run, Analyze, Review, Report | Same six steps available on desktop/mobile |
| `nextStep()` and focus dropdown inadequately express an agent | Conversation and structured decision: context, basis IDs, selected/excluded tools, expected evidence, completion condition | Requests receive responses explicitly labeled deterministic demo |
| ZAP timeout/pending approval lack execution identity | Separate action, approval, execution attempt; initial ZAP not executed | No output before execution; retry preserves prior run |
| Approval lacks a subsequent action | Separate simulate-run control after approval; live execution disabled | Approval alone cannot imply scan success; queued/running/terminal states shown |
| Artifact contains metadata only | Raw fixture text, locator, checksum over exact fixture bytes | Synthetic disclosure in evidence/exports; no claim of genuine native scanner output |
| Correlation difficult to find | Analyze compare panel; reasoned link/keep separate | Preserve observations; distinct assets/locations stay separate |
| Priority fields do not rank work | `review-order-v1` queue using source severity, analyst context, explicit unknowns | No invented CVSS/CVE/EPSS; confidence is not exploitability |
| Report creation hides incomplete work | Readiness checklist, pending/failed/unknown disclosure, reasoned draft snapshot | Frozen snapshot; backend PDF Planned; browser print is a sample |
| Documents link removed V3/V4 files | README/spec/handoff use 6.2; retain V6.1 | Check local links and predecessor hash |

## 3. Information architecture and PDF mapping

| Step | Analyst question | Content/actions | Requirements |
| --- | --- | --- | --- |
| 01 Scope | What am I authorized to assess? | Target/IP, ports, exclusions, ROE, validity, rate/deadline, versioned edits | R01/R02/R15 |
| 02 Plan | What will the agent do, and why? | Natural-language conversation, structured plan, evidence rationale, allowlisted actions, approve/deny | R01/R03/R10/R13 |
| 03 Run | What happened in this attempt? | Run/attempt/action/approval IDs, source times, logs/output, timeout/cancel/unknown; retry as new proposal | R04/R05/R12 |
| 04 Analyze | Which sources describe the same issue? | Common observations/findings, correlation, raw evidence/provenance; services excluded from vulnerability counts | R06/R07/R08/R13 |
| 05 Review | What should I address first, and how certain is it? | Ranked queue, factors/unknowns, rationale, false positives, validation gate, audit | R09/R10/R12 |
| 06 Report | What can this report say, with which limitations? | Checklist, executive/technical preview, six PDF sections, frozen snapshot, print/JSON sample | R11/R08/R15 |

Assessments/Integrations are system-level navigation; Integrations is not an assessment step. Evidence opens directly from Plan, Run, Analyze, and Report. Mobile uses a step selector and vertically arranged panels without changing state meanings.

## 4. Prototype interaction contract

**State:** tab-local RAM; reload resets it. Each assessment independently owns scope, request revision, conversation, actions, runs, observations, findings, audit, and snapshots. New assessments start empty. Do not store user scan data/secrets in localStorage.

**Agent:** scenario/rule responses labeled `Demo agent · deterministic`. Supports rationale questions, discovery-only, web assessment, progress/failure, and reporting. Other requests receive an explicit limitation rather than false comprehension/execution. Proposals come only from a fixed profile catalog; no arbitrary CLI. Evidence references open source drawers. This simulates conversation UX, not a functioning conversational model.

**Causal scenario:** initial Nmap scenario is complete with a service fixture; Greenbone is a historical-import fixture; ZAP is proposed without output. Approval does not run tools. Analyst explicitly selects success/timeout/failed/partial/unknown and starts an attempt. Timers simulate queued → running → terminal without target requests. Only success/partial add output. Unknown does not auto-retry. Cancellation remains requested until the simulator confirms it. Retry creates a new proposal, reason, and approval; it never rewrites a previous run. Completed profiles cannot repeat without a separate retest reason.

**Approval:** exact local payload includes target/profile/ports/rate/deadline, scope/request revision, basis IDs, and expiry. Local policy checks exclusions, profile, evidence ownership, and HTTP basis; approval/rejection requires rationale. Scope/request changes stale old proposals. These are UX guards, not cryptographic authorization or actual enforcement. Offensive validation requires approval but execution remains unsupported; do not fabricate Metasploit execution.

**Evidence/correlation:** fixtures are authored for the prototype, not scanner output. Separate raw text/metadata, compute SHA-256 over exact fixture bytes, and distinguish `observed_at` from `ingested_at` for historical data. Link/keep separate requires reason; cross-time linking does not confirm exploitation. Fixture/manifest downloads carry synthetic notices. Real imports remain Planned; file selection is not an operational adapter.

**Risk/review:** transparent `review-order-v1`: Critical/High, or high impact with reachable lab exposure → Review first; missing severity/exposure/exploitability/impact → Resolve context; Medium or observed preconditions → Review next; otherwise Routine review. Break ties by source severity then finding ID. Analyst context edits require rationale and preserve source severity/confidence/validation. Do not generate numeric risk scores. Uncalibrated confidence remains an explicit unknown. Analyst disposition is separate from validation; false positives retain evidence/appendix entries. Review requires rationale and does not establish confirmed exploitation.

**Report:** incomplete review/coverage permits an acknowledged draft with reason, freezing all disclosures. Do not call demo/incomplete output client-ready. Snapshot includes findings, memberships, actions, attempts, evidence, audit, and limitations at creation; later review cannot change it. Backend `pending/rendering/failed/ready` belongs to live handoff; prototype provides preview/browser print only. Server PDF download is disabled with a reason.

## 5. Truthful capability level

| Capability | 6.2 level | Platform work still needed |
| --- | --- | --- |
| Six steps, conversation, structured plan | UI scenario | Model, structured output, semantic validation |
| Run lifecycle, policy, approval/audit | Local simulation | Authentication, DB, worker, dispatch recheck, receipts/network enforcement |
| Nmap/ZAP/Greenbone | Synthetic fixtures; adapters Planned | Two live adapters, native Greenbone parser, genuine sourced outputs |
| Normalize/correlate/rank/review | In-memory interaction | Native ingestion, durable memberships, tested ranking |
| Raw evidence/hash | Exact synthetic fixture bytes | Private immutable actual execution/import artifacts |
| Report | Frozen local sample/browser print | Authenticated server snapshot/render/download and PDF acceptance |

Do not count this prototype toward the three working integrations or treat browser checks as scanner/model E2E. Advanced remediation tracking, full retest comparison, team RBAC, and all-seven-live coverage remain outside the HTML scope.

## 6. Frontend acceptance

Run the [browser checks](../../tests/prototype-v6.2.spec.cjs) using the [handoff](../superpowers/plans/2026-11-02-01-frontend-handoff.md). Check all six steps, causality, approval without dispatch, timeout/retry/unknown/cancel, assessment isolation, stale approvals, exact evidence hashes, correlation/false positives, draft disclosure, and snapshot immutability. Check 1440/820/390 px, keyboard focus/Escape, escaping, zero external requests, and printed sections 7.1–7.6. Record observed results only after execution in the [verification record](FRONTEND_V6_2_VERIFICATION.md); proposed checks alone are not evidence of passing.
