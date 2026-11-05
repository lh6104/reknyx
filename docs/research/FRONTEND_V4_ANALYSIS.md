# Historical analysis of frontend prototype V4

Original analysis: **2026-11-02**. **Historical record:** `corevapt_frontend_v4.html` has been removed from the current checkout. Its old line references, dimensions, and browser results describe that former artifact and were **not rerun** during this English documentation audit. Current prototype documentation: [v6.2 requirements](FRONTEND_V6_2_REQUIREMENTS.md).

Original comparison sources: [requirements matrix](REQUIREMENTS_MATRIX.md), [technical recommendations](TECHNICAL_RECOMMENDATIONS.md), [UX/solo plan](PREPARATION_AND_EXECUTION.md), and [PentestGPT/Fennec research](UPSTREAM_ARCHITECTURE_COMPARISON.md). The original session analyzed source and browser interactions without modifying HTML, running scanners/models, or implementing a backend. It applied `codebase-design` to distinguish necessary responsibilities from the number of user interfaces.

## 1. Historical conclusion

**V4 represented the right responsibilities but fragmented the solo MVP experience.** Scope, observations, findings, evidence, correlation, approval, and reporting are justified by the problem statement. Making nearly all of them top-level navigation items complicated one continuous assessment.

The artifact used standalone HTML/CSS/vanilla JavaScript, without graph frameworks, state libraries, brokers, or multiple services. There was no evidence of infrastructure overengineering. The implementation risk was building eleven screens and separate endpoints before one request → evidence → report workflow.

The original recommendation was Assessments, Assessment workspace, and Integration status, with Plan & activity, Findings, and Report inside the workspace. Scope/approval/evidence/audit would open contextually. This changed information organization, not organizer acceptance. The later six-step v6.2 UX is documented separately.

## 2. How V4 worked

### Data

`assessments`, `observations`, `artifacts`, `findings`, `approvals`, and `jobs` were hard-coded fixtures. State `S` held page, selected assessment, filters, modal/drawer, audit, and snapshots. Historical HTML lines 398–415.

The inspected seed contained three assessments, six observations, five artifact-metadata records, four finding candidates, and three proposals. The default assessment contained four observations and two candidates. These were fixture sizes, not security results.

### Rendering and interaction

```text
Click/input
  → JavaScript handler
  → mutate S or referenced objects
  → render() / renderOverlay() / findings rendering
  → replace DOM with innerHTML
```

`navigate()` changed pages/closed overlays/rendered; `current()` selected assessment; `scoped()` filtered by `assessmentId`. Views returned HTML strings. There was no URL router, API fetching, localStorage/DB persistence. Reload restored seeds. Historical lines 415–425, 452–470.

`esc()` escaped displayed data; search applied to current-assessment findings. Ctrl/Cmd+K focused search; Escape closed overlays/sidebar. Browser Blob/download links generated CSV/JSON. These were real frontend interactions over fictional data.

### Three capability levels

| Level | Examples |
| --- | --- |
| Implemented frontend interaction | Navigation, filtering, rationale, local decisions, observation linking, snapshots, CSV/JSON |
| Implemented simulation | Fixed ZAP proposal from a `:443` service observation, one correlation pair, local policy |
| Missing platform | LLM, genuine scan/import parsers, raw evidence/hash, risk engine, authenticated approval, worker, durable DB/audit, server PDF |

## 3. Screen responsibilities and historical behavior

| Screen / historical lines | Analyst purpose | V4 implementation | Original MVP assessment |
| --- | --- | --- | --- |
| Assessment overview — 427–428 | Request/scope, findings, pending decisions, failures | Counts from assessment records; seeded timeline | Keep concise summary; avoid duplicate finding tables |
| Assessments — 429–431, 461–462 | Create/select assessment | Name, hostname, IPv4 `/32`, ROE reference, request; empty draft opens planner | Needed; avoid a third redundant detail/overview page |
| Scope & services — 432–433 | Targets/exclusions/profiles/budget/services | Scope display and `kind==='Service'` filtering; revision button only increments version | Keep in assessment scope; simulation controls belong in demo/test |
| Request & plan — 438–439 | Express goal and understand next step | Stores request; matches `kind==='Service' && location===':443'`; fixed proposal | Central workflow, but no AI/request interpretation |
| Findings & triage — 434–437, 457–460 | Search, inspect, review with reasons | Table/drawer, rationale, local status, whole assessment register export | Keep evidence/correlation/risk in context |
| Correlation review — 440–441 | Decide whether observations represent the same issue | Only links `OBS-203` to `FND-42` or keeps separate | Basic correlation P0; one-pair page could be a detail panel |
| Action approvals — 411–413, 442–445 | Approve/deny exact actions and see outcomes | Rules/rationale/JSON payload equality; no dispatch | P0, surfaced near pending timeline actions |
| Evidence lineage — 446, 459–461 | Observation → artifact/locator/time | Metadata only; no raw, null checksum, disabled upload | Trace P0; contextual drawer before standalone explorer |
| Integration status — 398, 447 | Understand live/import/planned/unsupported tools | Static seven-tool limitation matrix | Secondary page; no connector/key administration needed |
| Report snapshot — 448–450, 469 | Freeze and inspect a report | `structuredClone()`, §§7.1–7.6, browser print/JSON | Keep; one snapshot can suffice initially |
| Decision audit — 418, 451, 468 | Actor/action/time/assessment | In-memory array, fixed actor, JSON export | Audit P0, presented in activity rather than a separate application |

### Shared elements

- **Assessment selector:** contextual filtering, not backend authorization/tenant isolation.
- **Finding drawer:** severity, status, CVSS/CVE/CWE, confidence, priority, exposure, exploitability, impact, evidence, remediation. Separate Description/Evidence/Review for readability.
- **Artifact modal:** object metadata, not raw evidence viewing.
- **Toast:** interaction/missing-rationale feedback, not backend notifications.
- **Topbar activity:** opens audit, not real-time alerts. Avatar supplied no authentication.
- **Global search:** despite its variable name, searched only current-assessment findings; UI wording disclosed this.
- **CSV/manifest/audit/snapshot exports:** useful for review/debugging; PDF/evidence trace mattered more than every export format.

## 4. Interpreting the historical demo

### Seeded assessment

AST-021 → Nmap service observation → fixed ZAP proposal → exact-action review → approve/deny with rationale → no execution → seeded findings/correlation → snapshot → print/export.

This communicated the intended flow, not a working scanner pipeline. Jobs/observations/findings existed before approval. Audit recorded only interactions since page load, not the collection/model history of seeds.

### New assessment

Draft → request/scope → no observations → planner reports no HTTP evidence → no new action/scan/finding. This was an honest empty state, but platform implementation needed to connect authorized requests to discovery rather than depend on seed data.

### Backend handoff

Frontend should submit intent/decisions and render server state/receipts. Worker owns execution, dispatch policy, parsing, and artifacts. Editing `S.approvals` cannot grant actual authority. Presentation may be reused; the simulation engine must not become backend policy.

## 5. Useful ideas to retain

1. Service observations separate from vulnerabilities; open ports do not inflate finding counts.
2. Request/scope/evidence/report share assessment identity.
3. Honest unknowns/limitations; historical imports differ from present collection; source severity differs from priority.
4. Approval shows action details/rationale for meaningful human control.
5. Correlation/review retains source observations.
6. Frozen snapshots do not silently change after triage.
7. Standalone implementation supports UX learning without unnecessary infrastructure.

Evidence, approval, and correlation remain central acceptance requirements. Reduce cognitive load through contextual detail rather than removing them.

## 6. Complexity and cognitive load

### 6.1. Fragmented navigation

Eleven sidebar items, selector, and detail view made one workflow resemble separate applications. Overview/detail/timeline duplicated request/job summaries. Switching pages for evidence/correlation/audit broke finding/action context.

Original proposed navigation:

```text
Assessments
Assessment workspace
  ├─ Plan & activity [request + scope + jobs + approvals + audit]
  ├─ Findings        [detail + evidence + correlation + review]
  └─ Report
Integration status  [secondary]
```

A multi-conversation chatbot, attack-tree canvas, and SaaS administration dashboard were unnecessary. A natural-language request and evidence-linked plan could support P0 if backed by real interpretation.

### 6.2. Implementation detail in the analyst flow

Worker internals, cryptographic binding, missing parsers, and canonical JSON were useful research notes but occupied decision space. Keep Demo/Live/Import disclosure prominent; place technical detail behind expansion/demo notes. Fictional data must remain disclosed.

At the historical 1440 px overview, auto-fit placed four panels in one row, leaving a narrow findings table requiring internal horizontal reading. No page overflow did not establish usable panels. This was a layout/hierarchy issue, not a reason for another dashboard framework.

### 6.3. Scenario controls

`Simulate scope revision`, `Simulate expiry`, and exposed payloads helped demonstrate invalidation. Keep these in demo/debug controls. A real product needs purposeful scope edits, visible expiration, and replanning rather than artificial expiry buttons in normal operations.

### 6.4. CSS layering and compressed code

Historical size: approximately **97.8 KB** total, **56.0 KB** CSS, **40.0 KB** JavaScript. Size alone did not establish overengineering. Multiple original/V3 contrast/V4 override layers and unused chart/hero styles complicated review; one-line view functions obscured business changes.

For the proposed React implementation, split by real features and shared table/drawer/status primitives; avoid copying global `S`/inline handlers into numerous shallow components or building a generic design system. Scope decisions should precede prototype refactoring.

## 7. Historical gaps demonstrated

### Request interpretation

Changing the request to “Only assess TLS certificates; do not propose web crawling” still yielded bounded ZAP baseline. The request was stored but not used by the selection rule, which only recognized `:443`, not HTTP on `:80/:8080` after location-only changes. Lines 438–439.

This disclosed simulation did not demonstrate AI reasoning. Real planning needs normalized protocols, objectives, and allowed capabilities; chat UI alone cannot supply it.

### Correlation was one scenario

Linking changed membership from `['OBS-202']` to `['OBS-202','OBS-203']`. There was no arbitrary-input matcher/upload; candidate source was not a separate finding, so count did not decrease. This demonstrated membership review, not N-to-M deduplication. Lines 440–441.

### Incomplete local scope checks

Target/exclusion/profile/version/payload/expiry/ownership checks existed. A newly bound action using port 8443 with scope limited to 80/443 still returned `Requires approval`, showing incomplete ports/budget validation. This was not a backend bypass; no backend existed. Lines 411–412, 442.

JSON payload comparison demonstrated exact local binding, not cryptographic integrity/authentication. `authorized=true`, ROE strings, and checkboxes were inputs/fixtures, not independently verified authorization.

### Risk fields without ranking

`priority='Review required'`, confidence, and several context fields were common defaults. Severity filtering was not risk ranking. Keeping Unknown was correct, but a real versioned input/reason policy remained necessary. Lines 409, 435–436, 450.

### Triage/report inclusion

After FND-42 became False positive, a new snapshot still counted two candidates and Medium=2. Provenance remained, but users could mistake candidate severity totals for actionable vulnerabilities. This was semantic ambiguity given the candidates label, not necessarily a calculation defect.

Separate candidate, actionable, and rejected/false-positive totals; retain rejected evidence in an appendix or clear breakdown. Never delete sources simply to reduce counts. Lines 437, 448–450. See the [current metrics review](COMPETITION_METRICS_AND_REAL_WORLD.md).

### Snapshot versus archive

Historical browser checks confirmed deep-copy immutability after triage. `S.snapshots[assessmentId]` kept one replaceable snapshot and reload lost everything. Backend persistence was needed for later report traceability. `window.print()` was browser printing, not a server downloadable-PDF artifact. Lines 448–450.

## 8. Historical verification — 2026-11-02, not rerun

- Inline JavaScript parsed with `node --check`.
- Headless Chromium opened all eleven views with no page errors/external requests in the tested sequence.
- Request-save behavior did not interpret request semantics.
- Correlation updated the two seeded observation IDs.
- Snapshot JSON remained unchanged after later triage; replacement retained False positive status while candidate totals still counted it.
- The port-policy case above used browser-memory edits only, without scanner/network requests.
- Reload restored seeds and cleared audit/snapshots.
- At 390 px, document scrollWidth was 390 and closed sidebar x=-240; no page-wide overflow. Desktop/mobile screenshots were inspected, not a complete accessibility/responsive audit.

Original temporary artifacts were recorded under `/tmp/corevapt-frontend-analysis/`; their continued availability is unverified. The original analysis did not rerun PDF print, native parsers, models, backend, or platform E2E. PDF statements in [V4 review](FRONTEND_V4_REVIEW.md) came from a different historical check.

## 9. Original recommended sequence

1. Consolidate assessment workflow and secondary integration matrix.
2. Connect empty draft → authorized discovery → actual artifact → observation → adaptive next step → finding → report.
3. Implement worker/backend scope, approval, durable state, evidence, and risk; frontend renders the outcome.
4. Place correlation/evidence/approval in context while preserving deep trace.
5. Refine CSS/mobile and optionally SSE/extra exports after the main path.

These are historical recommendations, not current v6.2 verification or evidence that platform requirements have been completed.
