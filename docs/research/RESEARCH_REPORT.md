# CoreVAPT — research conclusions and preplan assessment

Research snapshot: **2026-11-01**, with upstream additions and an English documentation audit on **2026-11-02**. Original listing and external-document checks were not automatically rerun by translation. Requirements were rechecked against the exact [root PDF](../../1.pdf), 10 pages, SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

## 1. Main conclusion

**CoreVAPT fits Statement 1; a modular monolith with three adapters is a reasonable solo-developer scope.** The hardest work is demonstrating adaptive decisions, correctness, and provenance in a functioning workflow. Additional scanners or elaborate screens do not supply that evidence.

Recommended positioning: **a conversational VAPT assistant that chooses investigations from evidence, normalizes and correlates multi-tool results, and generates traceable reports under analyst control**. This is a product interpretation of PDF §§2–6 and 10–13, not an organizer-prescribed name or architecture.

Retain the balanced strategy. Add conversational requests to acceptance, deliver an early vertical slice, distinguish service observations from vulnerabilities, treat correlation as an identity/evidence problem, and bind approval to the action before implementing scanners.

## 2. Event information checked in the original research

| Item | Recorded information |
| --- | --- |
| Format | Online; Discord |
| Team | 1–4 people; solo permitted |
| Registration | 01 November, 23:59 IST → 02 November, 01:29 UTC+7 |
| Start | 02 November, 14:00 IST → 02 November, 15:30 UTC+7 |
| End | 07 November, 23:59 IST → 08 November, 01:29 UTC+7 |
| Submission | PPT Drive link, demo-video Drive link, and GitHub link |

The listing required accessible links and all three fields for consideration. [Official Unstop API](https://api.unstop.com/hackathons/dataops-innovation-hackathon-hackthecore-1765313). These are the original research's recorded event details; they were not refreshed during translation.

**Calculated from those timestamps:** the event window is approximately **129 hours 59 minutes**. The original Day 1–Day 7 roadmap exceeded that window. Aim to submit during the afternoon/evening of 07 November UTC+7, allowing time to repair link access. Do not treat the India-local end date as a local deadline without conversion.

Unverified: prebuild and AI coding permission, lab credentials, live judging time, PPT/video limits, private repository access, API credits, and cross-border prize/internship eligibility. Broad listing eligibility does not settle payout or internship terms for a participant in Vietnam. The PDF does not resolve these questions.

## 3. What the organizer actually requires

Source: PDF §§3–6, pp2–5.

- Accept a **natural-language assessment request**, target, and authorized scope; produce an auditable plan with rationale.
- Demonstrate at least **three working integrations or supported imports**, spanning network and web. All three need not be live; two live integrations plus one import is a design consistent with this provision.
- Provide a common finding schema, evidence links, duplicate handling, and risk ranking.
- Provide a downloadable professional PDF and an analyst approval gate.
- Disclose all **seven tools** as Live / Import-only / Planned / Unsupported.

Adaptive planning remains a functional requirement (§5.2), while **multi-step adaptive replanning with state/memory** appears as an advanced extension (§6). The MVP needs an observable evidence-dependent branch: observed HTTP leads to a web assessment proposal; absent HTTP leads to a different justified action or stopping; timeout produces limitations rather than a successful-scan claim.

The organizer does not mandate LangGraph, React, PostgreSQL, eight modules, seven tables, cloud deployment, a vector database, or twenty features. These are project choices. §8 frameworks apply where relevant and do not imply comprehensive implementation or formal compliance.

## 4. Strategy against the rubric

Source: §11, p9. Eight criteria, 100 points; source order preserved.

| Criterion | Points | Evidence to prepare |
| --- | ---: | --- |
| End-to-End Coverage | 15 | Request → approved execution/import → analysis → report |
| AI Reasoning & Decisions | 20 | Different evidence produces different next actions; rationale cites observation IDs |
| Technical Accuracy | 15 | Correct parsing; no CVE inferred from a banner alone; observed/suspected/confirmed distinguished |
| Correlation & False Positives | 15 | A correct merge and a similar case kept separate; provenance retained |
| Risk Prioritization | 10 | Versioned rules and explicit inputs; explained severity and business priority |
| Safety & Scope Control | 10 | Backend rejects out-of-scope actions; approval recorded and rechecked at dispatch |
| Report Quality | 10 | Readable PDF with all §7 content, evidence references, and limitations |
| Efficiency & Robustness | 5 | Repetition prevention, bounded steps/time, and transparent timeout/recovery |

**Recommended effort:** focus on decision quality, data/evidence, and one functioning workflow. This is not a score prediction. UI should help the analyst understand evidence, uncertainty, status, and available decisions. Practical value also needs measurement of analyst effort, report correctness, and operating constraints; see [the integrated metrics/application review](COMPETITION_METRICS_AND_REAL_WORLD.md).

## 5. Preplan: retain, revise, add, defer

| Existing decision | Assessment | Recommended adjustment |
| --- | --- | --- |
| Modular monolith and worker | Retain | Shared codebase; separate worker process; durable DB job state |
| Nmap, ZAP, OpenVAS import | Retain conditionally | Verify genuine native XML, authorized export, and assessment identity; do not assume OpenVAS data exists |
| No Redis/Kafka/Kubernetes/Neo4j | Retain | Still implement job lifecycle and durability |
| Local evidence storage | Retain | Immutable raw artifacts, checksums, private access; MinIO later |
| LangGraph | Candidate | Timebox persistence/interrupt work when implementation is authorized; a custom state machine has fewer dependencies |
| Eight P0 modules | Retain responsibilities | Do not turn them into separate services/repositories/workflows |
| Seven initial tables | Revise | Add action/decision trace, observation-to-finding membership, and immutable report snapshot representation |
| `HTTP Service Detected` counted as a finding | Revise | Store a service observation; exclude from vulnerability totals |
| Confidence 0.98/0.75 | Revise | Uncalibrated examples; retain source values and a declared mapping method |
| Merge by CVE/title | Insufficient | Require asset/service/location identity and compatible evidence |
| Approval points to a finding | Insufficient | Actions may precede findings; bind exact action and scope version |
| Risk from CVSS and confidence | Revise | Preserve source severity; low confidence prompts review without concealing high impact |
| Complete modules before integration | Revise | Deliver an early vertical slice and expand it |
| Video/pitch at the end of Day 7 | Revise | Use the actual event window; outline early and record before the deadline |
| Scaffold before kickoff | Rules unverified | Original authorized scope was research/documentation/read-only environment checks; do not infer permission |

## 6. Three implementation options

**A — Balanced, recommended:** live Nmap, a bounded live ZAP profile, and Greenbone native XML import; one planner, independent policy, worker/PostgreSQL, and local evidence. Main risks are lab/scope authorization and genuine correlation across sources.

**B — Import-first fallback:** three native import adapters with the same schema/report/approval flow. This may satisfy §6's integration wording, but offers weaker live execution coverage. It still needs an organizer-authorized sample lab demonstration and honest import-only labels. Do not assume judging equivalence with option A.

**C — More live adapters/agents:** expands implementation, licensing, resource, and failure risks; unsuitable for the proposed solo timebox. Record remaining tools truthfully.

Do not install all of Greenbone merely to count a tool. If no valid export exists by the adapter decision deadline, assess a lighter third integration such as Nikto, supported by genuine authorized output and an updated design. LLM-generated XML is not scanner evidence.

## 7. Technical pitfalls

### Scanning and scope

ZAP passive analysis does not mean its baseline creates no traffic: the baseline includes a crawler. Nmap version detection sends probes. Control actual behavior, ROE, and rate limits rather than trusting profile names. [Scanner research](SCANNER_RESEARCH.md).

A domain string alone cannot enforce scope. Host/IP/port/scheme, exclusions, DNS, redirects, and worker/network enforcement matter. Container networking alone does not restrict scanners to authorized targets. [Technical recommendations](TECHNICAL_RECOMMENDATIONS.md).

### Intelligence and provenance

Preserve original scanner observations and raw sources. Canonical findings are versioned correlation results; do not overwrite source observations. Two tools repeating the same source are not independent evidence and do not automatically confirm a finding.

A finding can be valid without a CVE, such as a misconfiguration. Reported CVEs need sources; CVSS needs version/vector/source when available. OWASP/CWE tags do not establish compliance. [Standards research](STANDARDS_AND_AGENT_RESEARCH.md).

### Agent

Decision trace should contain a concise rationale, evidence IDs, proposed action, policy result, and outcome. It need not store hidden model reasoning. Structured output checks shape; independent policy must still enforce permissions, scope, budgets, and preconditions. Scanner HTML/banners/descriptions are untrusted data.

### Product and report

Reports must retain incomplete coverage, failures, pending approvals, and historical imports that are not contemporaneous with live scans. Offline fallback must be labeled replay/import. Do not animate recorded data as live execution.

## 8. Prior art and differentiation

**Source-verified in the original research:** the USENIX Security 2024 PentestGPT paper describes strong LLM performance on subtasks and difficulty maintaining assessment context. This supports structured evidence/state summaries; paper benchmark results are not CoreVAPT results. [Original paper](https://www.usenix.org/conference/usenixsecurity24/presentation/deng).

PentestGPT's README already describes discovery-to-report tooling; “AI calls tools and produces a report” is not a defensible novelty claim. [Author repository](https://github.com/GreyDGL/PentestGPT). The 02 November source review distinguishes README/legacy behavior from the maintained nested framework; see [upstream comparison](UPSTREAM_ARCHITECTURE_COMPARISON.md). PentAGI describes autonomous pentesting; only its public description/repository was read in the original research, without quality benchmarking. [PentAGI repository](https://github.com/vxcontrol/pentagi).

**Recommended competition emphasis:** source-preserving correlation, explicit uncertainty, approval bound to the exact action, and report-to-raw traceability. These fit the rubric but do not establish exclusive features or market superiority. Check prebuild/license rules and the ability to explain original work before adopting a large upstream system. See [solution landscape](SOLUTION_LANDSCAPE.md) for the updated comparative review.

## 9. Research status and subsequent documentation

The original research supplied inputs to WP-01 Product Specification; it did not itself complete Phase A or demonstrate integrations/E2E. Product, architecture, API/data, and UX documents subsequently authored must be assessed on their own evidence. The current HTML is v6.2 with v6.1 retained; synthetic interactions do not demonstrate scanner, model, or platform execution.

Outstanding organizer questions and the proposed schedule remain in [PREPARATION_AND_EXECUTION.md](PREPARATION_AND_EXECUTION.md). This dossier is not authorization to scan public systems or self-authorize a competition lab.

## Follow-up readiness research — 2026-11-02

The [readiness decision report](READINESS_DECISION_REPORT.md) is the next implementation handoff. New source verification found a duration wording conflict between the listing's 2–7 November timestamps and a specific organizer LinkedIn post's 24-hour description; the [confirmation pack](ORGANIZER_CONFIRMATION_PACK.md) records both without assuming a superseded deadline. It also records unresolved target/ROE and active-validation acceptance. New scanner/provider/network decisions do not establish working integrations, model quality or permission to execute.
