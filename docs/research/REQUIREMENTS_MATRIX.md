# Statement 1 — requirements → design → evidence

The sole source for the requirement column is the user-supplied [organizer PDF at the repository root](../../1.pdf), **10 physical pages**, SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`. It was reread with `pdftotext` during the **2026-11-02** documentation audit. Proposed solutions and acceptance checks are CoreVAPT design recommendations; the frontend prototype does not establish their platform implementation.

## 1. Functional and MVP requirements

| ID | Requirement / source | Proposed solution | Proposed acceptance evidence |
| --- | --- | --- | --- |
| R01 | Conversational request, target, and scope — §3 p2; §6 p5 | Request/chat panel and scope form; the agent cannot expand scope itself | A natural-language request produces a plan; backend scope is read from the correct assessment |
| R02 | Register approved lab targets, exclusions, and permissions — §5.1 p3 | Versioned authorized scope and ROE | Valid in-scope action accepted; excluded host/port rejected with an audit reason |
| R03 | Choose tools from discovered services/results and explain the next step — §5.2 p4 | Planner uses observation IDs and a fixed action catalog | HTTP evidence leads to web assessment; absent HTTP evidence does not; both use the same policy |
| R04 | Execute approved scans; monitor jobs and handle timeouts/errors — §5.3 p4 | Worker with genuine execution state and artifacts | Running/success/timeout states, exit codes, and raw references are observable |
| R05 | At least three working integrations/imports spanning network and web — §6 p5 | Nmap, ZAP, and Greenbone import | Each adapter processes actual native output; live versus import mode disclosed |
| R06 | Common data model — §5.4 p4 | Separate scanner observations from canonical findings | Three formats map to a versioned contract |
| R07 | Merge genuine duplicates without hiding assets or evidence — §5.4 p4 | Correlation rules and membership links | Positive pair merged; different assets/paths remain separate; all raw references retained |
| R08 | Source, asset, timestamps, raw references, evidence, confidence, and status — §5.5 p4 | Artifact, observation, and validation records | UI/PDF trace to observation and raw locator; artifact hash matches |
| R09 | Severity/CVSS, exposure, exploitability, impact, and confidence — §5.6 p4 | Rule-based priority with sourced inputs and explicit unknowns | Two explainable cases; no invented CVSS; missing data does not become zero |
| R10 | Explicit approval before active exploitation/offensive validation, with recorded outcome — §5.7 p4; security boundary p2 | Approval bound to action hash and scope; policy check before dispatch | Pending/rejected actions do not dispatch; only the approved action executes; stale approval blocked |
| R11 | Client-ready report — §5.8 p4; §7 p5–6 | Snapshot → renderer → downloadable PDF | Readable PDF with headings/navigation, all §7 content, and evidence traceability |
| R12 | Show progress, decisions, and failures; avoid repetition — §3 p2 | Timeline, action fingerprint, and budgets | Repeated request does not create a duplicate scan; displayed failures are genuine |
| R13 | Distinguish observed evidence from inference — §3 p2 | Fact/inference labels and source references | AI summary is never represented as raw scanner evidence |
| R14 | Truthful status matrix for all seven tools — §6 p5; §9.6 p7–8 | Capability/mode/limitation matrix | Planned work is not counted as live/working; a video does not substitute for execution |
| R15 | Lab-only testing, integrity, and secure scan-data handling — §13 p10 | Policy, private storage, redaction, and audit | Out-of-scope actions blocked; sensitive content absent from public repository |

## 2. Required report: preserve §7 structure

The preplan's nine report parts can be used, but the source PDF numbers **six subsections**. Additional subheadings are acceptable if all content remains present.

| PDF section | Page | Required content |
| --- | --- | --- |
| 7.1 Executive Summary | 5 | Executive summary and overall assessment scope |
| 7.2 Assessment Methodology | 5–6 | Methodology, rules of engagement, tested assets, and tool execution summary |
| 7.3 Severity Distribution | 6 | Severity distribution and prioritized findings |
| 7.4 Detailed Vulnerability Findings | 6 | Identifier, affected asset, description, supported severity/CVSS, applicable CVE/CWE, supporting evidence, confidence, and validation status |
| 7.5 Impact and Remediation | 6 | Business/technical impact, actionable remediation, and references |
| 7.6 Assessment Limitations | 6 | Limitations, assumptions, scan failures, human approvals, and timestamps |

Recommended additions, not organizer requirements: report ID, generation timestamp, snapshot version, evidence manifest/checksum appendix, observations separated from vulnerability counts, historical-import labels, and model/prompt/parser versions.

## 3. Deliverables and live demonstration

| Requirement — §9 p7–8 | Proposed artifact |
| --- | --- |
| 9.1 Working prototype on an organizer-authorized sample lab | Assessment with execution/import trace |
| 9.2 Architecture: models, orchestration, adapters, flow, state/memory, and security boundaries | Architecture diagram and ownership table |
| 9.3 Sample evidence-backed AI-generated VAPT PDF | Content-reviewed PDF snapshot |
| 9.4 Source: setup, dependencies, licensing assumptions, and execution | README, lockfiles, and tool/license matrix |
| 9.5 Approval demonstration and decision/audit trace | Request/reject/approve demonstration with execution outcome |
| 9.6 Integration matrix with limitations, assumptions, and unsupported scenarios | Seven-tool table with actual modes and evidence |

The seven capabilities in the live checklist (§10 p8) are: target/request and scope; plan and tool rationale; multi-tool execution/import and trace; normalization/correlation/false positives/uncertainty; priority and approval; PDF and original evidence; failure handling and honest disclosure. Map each to a step supported by actual data; slides alone do not demonstrate execution.

PPT, video, and GitHub are separate listing submission fields, recorded historically in the [research report](RESEARCH_REPORT.md). They do not replace the PDF's deliverables.

## 4. Integration matrix before platform implementation

This records **workspace platform readiness**, not the desired final state. No working scanner adapter has been demonstrated by the research or synthetic frontend scenarios.

| Tool | Current status | Proposed MVP target | Required disclosure |
| --- | --- | --- | --- |
| Nmap | Planned | Live discovery and native XML parsing | Fixed scope/profile; service detection does not prove a vulnerability |
| Nessus | Unsupported | Unsupported | No verified licensed installation/export in the workspace |
| OpenVAS / Greenbone | Planned | Import-only native XML | No Greenbone execution; valid export, timestamps, and provenance needed |
| Nikto | Unsupported | Unsupported / fallback third integration | Switch only after assessment and receipt of genuine output |
| OWASP ZAP | Planned | Live web profile and JSON parsing | Bounded profile; no claim of full authenticated/API coverage |
| Burp Suite | Unsupported | Unsupported | Do not assume licensed scanner/API functionality in Community |
| Metasploit | Unsupported | Unsupported | An approval gate is not an exploitation integration |

Change Planned to Live/Import-only only after implementation, with execution/artifact/version evidence. Unsupported describes CoreVAPT's supported scope, not the underlying tool's capabilities. Frontend fixtures and file selection do not change adapter status.

## 5. Proposed minimum acceptance cases

1. **Happy path:** request → plan → scan/import → normalized data → correlation → review → PDF, under one assessment ID.
2. **Adaptive branch:** two different evidence inputs lead to different next actions; each decision includes source IDs.
3. **Scope:** excluded target/port, out-of-scope redirects, and scope changes after approval are blocked at the execution seam.
4. **Approval:** unauthorized callers cannot approve; changed parameters cannot reuse approval; denial is audited.
5. **Import:** genuine native fixture, unsupported format, oversized XML, malformed XML, and duplicate import; an empty parse is not silently successful.
6. **Correlation:** true duplicate; same title/different asset; same CVE/different endpoint; missing CVE; contradictory evidence; no blind merge.
7. **Risk:** missing CVSS/exposure/EPSS; low confidence with high impact; differing vectors/versions; source severity preserved.
8. **Worker:** timeout, nonzero exit, partial artifact, and process crash; scans with side effects are not retried unconditionally.
9. **LLM:** invalid schema, unsupported action, nonexistent evidence ID, exhausted budget, and unavailable API; no invented results.
10. **Report:** finding traceability, Unicode/fonts, page breaks, consistent severity totals, pending approvals, and failures retained in the snapshot.

These are proposed checks of real failure modes, not test results. Record denominators, versions, lab, and profile when testing. A few fixtures cannot establish a system-wide low false-positive rate.

## 6. Defensible measurement

Compare manual ingestion/correlation/report preparation with assisted work on the same lab and evidence set; record conditions and repetitions. Without a baseline, report only observed workflow/scan/report duration and interaction counts.

Useful metrics include artifact-to-report trace coverage, merge precision/recall on labeled pairs, scope rejection across negative cases, repeated-action counts, timeout-recovery outcomes, and model latency/cost. Do not present proposed targets such as “95% accuracy” or “80% less work” as achieved results. See [competition metrics and practical applications](COMPETITION_METRICS_AND_REAL_WORLD.md) for the integrated evaluation plan.

## 7. Exact judging rubric — §11 p9

| Criterion, in source order | Points |
| --- | ---: |
| End-to-End Coverage | 15 |
| AI Reasoning & Decisions | 20 |
| Technical Accuracy | 15 |
| Correlation & False Positives | 15 |
| Risk Prioritization | 10 |
| Safety & Scope Control | 10 |
| Report Quality | 10 |
| Efficiency & Robustness | 5 |
| **Total** | **100** |

## 8. Frontend 6.2: UI-level requirement coverage

Sources: [PDF/UX requirements](FRONTEND_V6_2_REQUIREMENTS.md), [HTML](../../corevapt_frontend_v6.2.html), and the [separate frontend verification record](FRONTEND_V6_2_VERIFICATION.md). UI coverage does not establish runtime acceptance.

| ID | 6.2 surface | Remaining platform requirement |
| --- | --- | --- |
| R01 | Request creation/editing and deterministic conversation | Model inference and authenticated request persistence |
| R02 | Scope/version/exclusions/ports/budget; stale/out-of-scope UX guards | Server policy and DNS/redirect/IPv6 egress enforcement |
| R03 | Structured plan, tool rationale, HTTP/non-HTTP basis, decisions after failure | Model planning and semantic validation over real observations |
| R04 | Run/attempt/action/approval references; queued/running/success/partial/failure/timeout/cancel/unknown | Worker/process telemetry, receipts, durable cancellation/reconciliation |
| R05 | Synthetic Nmap/ZAP/Greenbone flows and Planned import UI | Three working integrations/imports remain unproven |
| R06 | Common in-memory observation/finding fields | Native parsers and versioned persisted schema |
| R07 | Reasoned compare/link/keep separate; distinct endpoint/service ports preserved | Validated persisted matching policy and labeled evaluation |
| R08 | Synthetic raw bytes, locator, observed/ingested time, SHA-256, frozen source | Genuine scanner/import artifacts and private immutable storage |
| R09 | Review ordering, analyst exposure/exploitability/impact, explicit unknowns | Evidence-backed inputs and tested/persisted policy |
| R10 | Exact local payload review, approve/deny, invalidation, blocked offensive checkpoint | Authenticated actor, canonical server hash, bound grant, dispatch recheck |
| R11 | Sections 7.1–7.6, executive/technical views, draft readiness, frozen preview/print | Backend jobs/render/download authorization and client-ready PDF acceptance |
| R12 | Per-attempt logs/audit, duplicate guard, new retry, unknown reconciliation | Durable audit/idempotency/receipt recovery after actual crashes |
| R13 | Sources separate from demo inference; basis links and unknown labels | Grounding evaluation against actual model/tool output |
| R14 | Seven tools with current Planned/Unsupported, intended mode, limitations | Live/Import-only labels require actual integration evidence |
| R15 | Synthetic lab-only UI, escaped text, no target requests | Private storage/auth/network controls and integrity acceptance |

Prototype interactions alone do not pass platform gates G0–G4. The HTML supports UX review and frontend/backend handoff; it is not a working AI-agent submission. For candidate/actionable/rejected count semantics and limited evaluation denominators, see [competition metrics and practical applications](COMPETITION_METRICS_AND_REAL_WORLD.md).

## 8. V6.3 page consolidation and dashboard

The [V6.3 UX specification](UX_STANDARDS_AND_PAGE_MAP.md) supersedes the V6.2 page map, preserving R01–R15 and its runtime boundaries. The new dashboard does not add mandatory scanner/provider scope.

| Surface | Requirement responsibility | Contextual details |
| --- | --- | --- |
| Dashboard / Assessments | R12 progress and decisions; R01 assessment entry | Assessment-bound attention links, latest run issues, candidate-review counts and draft state |
| Agent & runs | R01–R05, R10, R12, R13 | Scope/ROE, exact-action approval, attempts/logs, native import status, conversation and evidence basis |
| Findings | R06–R10, R13 | Correlation, raw provenance, uncertainty, priority factors and analyst review |
| Report | R08, R11–R13, R15 | Six required sections, readiness/limitations, frozen evidence and decisions |
| Tools/defaults drawer | R14 and clear configuration boundaries | Seven-tool matrix; defaults for new drafts only, with no authorization side effect |

[Browser evidence](FRONTEND_V6_3_VERIFICATION.md) verifies the local page/interaction model. All three scanner integrations/imports, actual model planning and server PDF remain unproven; no conformance or improved human usability is inferred.

## 9. V6.4 approved merge — frontend mapping

The approved [merge](FRONTEND_V6_2_V6_3_MERGE_RESEARCH.md) and [current page map](UX_STANDARDS_AND_PAGE_MAP.md) replace the V6.3 navigation above without changing R01–R15 or integration requirements. Workflow takes the Agent & runs responsibilities with an always-visible six-phase lifecycle and task/why/basis/decision/result. Agents exposes the one assistant's role, mode, disconnected model, capability readiness, authority limits and assessment activity; it adds no scanner/provider requirement or runtime agent resource. Dashboard, Findings, Report and Settings retain the mapped responsibilities.

[Fresh V6.4 browser evidence](FRONTEND_V6_4_VERIFICATION.md) is local UI evidence only. Clarifications preserve request/grants; Edit request, Generate plan, approval and run start stay separate. No browser count is a passed platform requirement, model evaluation or working integration.
