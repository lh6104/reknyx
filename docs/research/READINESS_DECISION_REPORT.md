# CoreVAPT readiness decision report

Reviewed: 2026-11-02. **Output of the follow-up research requested before platform implementation.** All choices below are design decisions/recommendations; none is a claim that the platform, model or scanner integrations already work. Mandatory baseline: [1.pdf](../../1.pdf), ten pages, SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

## 1. Decision

**Proceed with contract authoring and the bounded module/vertical-slice implementation plan. Keep live scanning and client-ready claims behind their explicit evidence gates.** Further generic market research is not the next critical path. The remaining uncertainties now have named owners, concrete outputs and pass conditions.

The proposed application remains one modular monolith plus a worker, PostgreSQL and immutable private artifacts. The user-appointed frontend team can work against frozen contracts without waiting for a live scanner or model account. The research does not implement or freeze those contracts itself.

## 2. Results against the six open checks

| Open check | Research output / decision | Still needed before claiming success | Owner and dependent gate |
| --- | --- | --- | --- |
| Organizer permission and lab | Local PDF and public listing establish boundaries, but not target credentials/ROE; a public schedule inconsistency was found. An unsent confirmation pack specifies closure evidence. | Official target/profile/traffic authorization; confirmed schedule; §9.5 accepted validation demonstration | Coordinator with organizer; live/submission gates |
| Three integrations | Fixed Nmap/ZAP/native Greenbone format/profile decisions and source-reference inspection. Public sample files are not automatically genuine acceptance captures. | Pinned tool builds, actual native ingestion, authorized Nmap/ZAP receipts, genuine Greenbone export or a reviewed third-adapter fallback | Scanner/QA owners; R05/G4 |
| Contract G0 | Concrete typed input, limits, idempotency, message/planning, hash, lifecycle and risk/report semantics | Executable OpenAPI and schemas/examples, semantic validation, cross-language hash vectors, FE/BE owner review | Contract/foundation owner; G0 |
| Real AI reasoning | Current official-provider shortlist and a conditional first evaluation candidate; strict semantic gate and cost/data-handling protocol | Approved account/data policy, bounded real calls, held-out comparison with deterministic baseline, measured grounding and action validity | Planner/QA owners; LLM acceptance |
| Scope and recovery | Feasible narrow control-plane/data-plane launch design with final authorization fence, actual egress policy and crash/receipt matrix | Host/runtime prerequisites and privileged setup, allow/deny/cancel/crash tests; no exactly-once external-side-effect claim | Integration/worker/policy owners; live enforcement |
| Quality and practical value | Existing 35 acceptance cases/ten manual workflows plus E01–E12 evaluations; pilot release and analyst-time measurement gates | Actual results with denominators, raw provenance/PDF review, operator review, backup/restore evidence for pilot | QA/report/integration owners; release/pilot gates |

“Research decision available” is not “implementation verified.” In particular, G0 is not passed, three integrations are not delivered, and organizer authorization is not supplied by this report.

## 3. Concrete decisions and implementation consequences

| ID | Decision | Why it is appropriate | Implementation consequence |
| --- | --- | --- | --- |
| D01 | Preserve the monolith/worker architecture | No measured scaling/team reason for distributed infrastructure | One state/evidence model and integration owner; no broker or runtime multi-agent system in P0 |
| D02 | First slice is one exact authorized IPv4 lab asset and explicit TCP ports | Narrow enough to enforce and explain while covering network/web | Unsupported ranges/IPv6/UDP rejected; network tests still prove IPv6 cannot escape |
| D03 | ZAP baseline requires origin-wide authorized web scope in v1 | Packaged scan behavior can widen a path target to origin root | Reject path-only authorization; no arbitrary context/auth/hooks or active API/full scan |
| D04 | Native adapter readiness is evidence-based | Public parser fixtures can be malformed, anonymized or inconsistent | Separate format-reference fixtures, native capture provenance and actual app ingestion/live proof |
| D05 | Message append and model planning are separate operations | A retry must not duplicate chat, billing or scans | Explicit idempotent POST messages, explicit idempotent plan request; no inference on page load |
| D06 | Model produces a proposal, never execution authority | Correct JSON is not correct evidence or permission | Validate source ownership/content, revision, catalog, scope/budget and independent grant before dispatch |
| D07 | Use a conditional first model evaluation, not an untested “best model” | Official pricing/capability docs cannot establish local reasoning quality | Measure the declared holdout against deterministic baseline; keep provider fallback labelled |
| D08 | The host launcher is a narrow trusted execution adapter | Giving a planner/worker a raw Docker socket expands authority beyond the fixed catalog | Fixed submit/status/cancel protocol, server-derived profile/network envelope and immutable receipts |
| D09 | Treat uncertain dispatch as unknown until reconciled | DB commit and external scanner start are not one atomic transaction | Attempt fencing, durable launch intent, final start authorization, no blind scanner retry |
| D10 | Use ordinal review priority with sourced context, not invented risk numbers | PDF requires defensible risk and forbids fabricated scores | Preserve CVSS/confidence semantics and unknowns; low confidence does not erase high impact |
| D11 | A ready PDF and a client-ready assessment are different states | A file can render while scope/review/coverage remains incomplete | Immutable snapshots, draft disclosure and attributed release review |
| D12 | Close the competition path before operational expansion | Rubric rewards evidence quality and coherent workflow, not an enterprise feature count | Retest/export/team features follow a verified vertical slice; pilot hardening has separate release gates |

The conditional first model experiment is **`claude-haiku-5-5`** through the direct Claude API; `gpt-6.1-terra` and `gemini-3.8-flash` are alternatives if approved access/data constraints or measured quality justify them. This selects an evaluation starting point, not a quality winner. Exact dated sources, rates and schema/retention qualifications are in the [provider report](MODEL_PROVIDER_DECISIONS.md). The first benign probe has one generation transmission and no automatic retry; the main holdout is 16 decisions or an explicitly budgeted 48 total.

## 4. Research artifacts and how to use them

| Artifact | Use |
| --- | --- |
| [Organizer confirmation pack](ORGANIZER_CONFIRMATION_PACK.md) | Exact unanswered questions, schedule conflict, source authority and unsent message |
| [Scanner readiness decisions](SCANNER_READINESS_DECISIONS.md) | Native format selectors, actual public-reference findings, profiles, exit semantics and third-adapter decision trigger |
| [G0 contract decisions](G0_CONTRACT_DECISIONS.md) | Input types/default limits, retry/revision/hash semantics and schema authoring acceptance |
| [Model/provider decisions](MODEL_PROVIDER_DECISIONS.md) | Verified dated shortlist, conditional candidate, SDK/schema/data-policy constraints and bounded cost/evaluation protocol |
| [Safety/recovery/pilot decisions](SAFETY_RECOVERY_PILOT_DECISIONS.md) | Concrete launch/network trust design, state race/crash handling and minimal operational gates |
| [Competition metrics and real-world validation](COMPETITION_METRICS_AND_REAL_WORLD.md) | E01–E12, metric formulas, held-out sets, pilot personas and manual-versus-assisted experiment |
| [Master plan](../superpowers/plans/2026-11-02-00-master-plan.md) and [parallel dispatch](../superpowers/plans/2026-11-02-06-parallel-dispatch.md) | Dependency/ownership/implementation handoff; frontend remains user-appointed |

The current organizer listing and a specific organizer LinkedIn post disagree in wording about duration. The [confirmation pack](ORGANIZER_CONFIRMATION_PACK.md) records direct URLs and publication evidence. Do not schedule against an assumed six-day or 24-hour build window without clarification. This does not change the PDF's technical rubric.

## 5. Execution sequence after this research

1. **Contract owner:** author and validate G0 schemas/examples, canonical hash vectors and every route-to-view mapping. Frontend can map layouts before G0, then use the frozen contracts.
2. **Foundation + module owners:** implement auth, scope, immutable artifacts and one import-to-observation-to-review-to-PDF slice with explicitly labelled fixtures. This proves integration seams, not live scanner coverage.
3. **Planner owner:** implement schema/semantic validation and failure handling, then run the authorized real-provider holdout once account/data/budget prerequisites exist. Fallback never masquerades as model success.
4. **Worker/integration owners:** implement the narrow launcher and egress/start fence; pass permitted and forbidden destination cases before enabling the Nmap/ZAP lab profiles. Import/renderer/FE work continues independently.
5. **Scanner/QA owners:** complete actual three-source native acceptance. At the acquisition gate defined in the scanner decision report, either accept the genuine Greenbone export or explicitly approve/replan the third-adapter fallback; never substitute generated XML silently.
6. **QA/report owners:** run A01–A35, M01–M10 and applicable E01–E12 with the declared evidence level. Demonstrate PDF-to-raw trace, honest failure handling and the organizer-accepted validation checkpoint.
7. **Coordinator:** assemble submission artifacts with exact limitations; separately complete access/retention/restore/operator gates before a real-client pilot.

No step requires the user to re-explain the project. External credentials, ROE and organizer answers remain factual inputs that public browsing cannot manufacture. Their absence blocks only dependent live/evaluation claims, not safe contract/module development.

## 6. Evidence standard for the next status update

Return task/owner/build/contract revision, exact command, environment, fixture mode, pass/fail/blocked/skipped/not_run counts, and evidence paths with IDs/hashes. Track these outcomes independently: contract validation, mocked UI, native parser, local DB/API integration, real model evaluation, real scanner lab execution, PDF release, and operational pilot readiness.

No score forecast is made. The [PDF rubric](sources/requirements-1-provenance.json) has eight weighted criteria; proposed targets and test pass rates do not convert directly to judge points. Stronger readiness means demonstrable behavior with disclosed limits, not a larger list of planned features.
