# CoreVAPT documentation audit

Audit date: 2026-11-02. Scope: root README and all project-authored Markdown under `docs/`, plus PDF provenance, source text/JSON and the existence of linked local artifacts. Copied `.agents/skills/` instructions are development assets and were screened for language; they are not product architecture or newly authored research. HTML prototypes, tests and screenshots are inspected as context and are not modified by this research pass.

## 1. Main findings and actions

| Finding | Consequence | Action in this pass |
| --- | --- | --- |
| Most project documents mixed Vietnamese and English | Inconsistent handoff and competition presentation | Translate research, plans, specs and README into English; translate example labels/comments as well as prose |
| Root README and some historical reviews referenced removed V3/V4 HTML | Broken navigation and ambiguity about current frontend | Point current work to V6.2/V6.1; keep V4 analyses explicitly historical without pretending their source still exists |
| Research, design, prototype and runtime evidence were easy to conflate | Unsupported claims of working tools/model/PDF | State the evidence level at each entry point and retain original verification dates; do not rerun/relabel old results as current |
| Contracts were a written inventory rather than executable schemas | Parallel agents could independently invent incompatible DTOs | Keep G0 as an explicit unpassed gate; specify full OpenAPI/profile/snapshot/parser contracts before domain integration |
| PDF and rubric were already studied but not tied to an operational evaluation protocol | Tests might pass while judging claims remain unsubstantiated | Re-read mandatory `1.pdf`, retain hash/visual rubric proof, add criterion-to-measure mapping and bounded holdouts |
| Prior-art coverage focused on two agent frameworks | Risk of rebuilding mature imports/reporting without a clear product reason | Add current findings/workflow/reporting/orchestration solution comparison, including edition/license boundaries |
| Plans lacked some conversation/risk/job distinctions | UI concepts might not survive persistence or share lifecycle semantics safely | Amend design/contracts/plans with persisted conversations/decisions, contextual risk fields and non-scanner job kinds |
| Gate-only approval demonstration could be mistaken for completed active validation | Unresolved PDF §9.5 acceptance hidden by a mock demo | Keep the permitted-validation question explicit and label fake-runner evidence correctly |

English documentation does not require silently changing independently authored frontend assets. The implementation handoff uses the English label **“In development”** for planned capabilities. Preview, runtime error, unsupported integration and live verification remain separate concepts.

## 2. Useful content retained from every existing document

All paths below are project-relative. This table is an audit disposition, not proof that the planned software exists.

| Document | Useful content retained | Review disposition |
| --- | --- | --- |
| `README.md` | Research-first entry, prototype and plan navigation | English; current prototype links and evidence boundaries |
| `docs/research/README.md` | Source authority, research reading order, unresolved organizer questions | English index; new review/landscape/metrics links |
| `RESEARCH_REPORT.md` | Balanced three-integration strategy, rubric, no arbitrary compliance/accuracy claims | Retain as research baseline; distinguish old snapshots from current findings |
| `REQUIREMENTS_MATRIX.md` | R01–R15, six report sections, mandatory/bonus distinction, negative cases | Keep IDs and source traceability; add latest review pointers |
| `SCANNER_RESEARCH.md` | Live versus native-import modes, traffic semantics, output/license constraints | Preserve native fixture and licensing gates; no working adapter assumed |
| `STANDARDS_AND_AGENT_RESEARCH.md` | Separate CVSS/CVE/CWE/confidence/risk, untrusted target data | Keep source semantics and no formal-compliance claim |
| `TECHNICAL_RECOMMENDATIONS.md` | Worker durability, artifact lineage, exact-action approval, versioned correlation/risk | Keep deep interfaces and concrete failure modes; current spec is normative for implementation |
| `PREPARATION_AND_EXECUTION.md` | Organizer questions, evidence gates, realistic submission buffer | Label preparation/environment/event snapshots by date; not a current environment benchmark |
| `PENTESTGPT_ARCHITECTURE.md` | Typed plan validation, state revision, bounded evidence, execution receipts | Static pinned-commit analysis; no runtime reproduction claimed |
| `FENNEC_ARCHITECTURE.md` | Deterministic router, hypothesis outcomes and summary budget | Transfer principles without adding a large runtime multi-agent system |
| `UPSTREAM_ARCHITECTURE_COMPARISON.md` | Proposal versus command, canonical state, expected evidence and stopping conditions | Retain five focused improvements and defer speculative features |
| `FRONTEND_V4_ANALYSIS.md` | Detailed analyst views, provenance and simulation boundaries | Historical analysis; V4 source absent from current checkout |
| `FRONTEND_V4_REVIEW.md` | Earlier scope corrections, honest integration states and report snapshot UX | Historical verification report; not fresh platform evidence |
| `FRONTEND_V6_2_REQUIREMENTS.md` | Six-stage workflow, causal action/run identity, raw fixtures, draft report disclosure | Current UX context; synthetic fixtures and local simulation clearly labelled |
| `FRONTEND_V6_2_VERIFICATION.md` | Frontend owner’s recorded 17 browser-check groups, environment, screenshots, sample PDF and artifact hashes | English translation preserves the original run; this research audit did not rerun browser checks |
| `specs/2026-11-02-corevapt-platform-design.md` | Ownership, scope, state invariants and frontend-first parallel work | English and corrected conversation/risk/job contracts |
| `specs/2026-11-02-corevapt-contracts.md` | HTTP routes, error/enum/idempotency/auth semantics and service seams | Design v0; full executable schemas remain G0 work |
| `plans/2026-11-02-00-master-plan.md` | Prerequisites, G0–G4 and source/evidence ownership | Retain coherent vertical slice and independent frontend assignment |
| `plans/2026-11-02-01-frontend-handoff.md` | Capability states, API error behavior, isolation and browser tests | Align with V6.2 six-step UX; no silent mock fallback |
| `plans/2026-11-02-02-backend-domain.md` | Scope history, immutable artifacts, policy locking, correlation and planner validation | Keep narrow responsibilities and trusted dependency injection |
| `plans/2026-11-02-03-worker-scanners.md` | Native parsers, bounded profiles, leases, fencing and crash reconciliation | No blind live retry; adapter-specific exits and actual destination checks |
| `plans/2026-11-02-04-reports-delivery.md` | Immutable snapshot, isolated renderer, authenticated downloads and delivery | Generic report jobs distinct from scan authorization; operational evidence explicit |
| `plans/2026-11-02-05-testing-acceptance.md` | 35 automated cases, ten manual workflows, Q0–Q6 and denominator discipline | Preserve all cases; map extensions E01–E12 without counting planned cases as passes |
| `plans/2026-11-02-06-parallel-dispatch.md` | Role/file ownership, independent waves and handoff packet | User retains frontend agent assignment; common files have one writer |
| `plans/2026-11-02-frontend-v6-2.md` | Prototype-only implementation sequence and verification boundary | Preserve checklist truth; no fresh frontend test execution in this review |

Research table entries without a prefix are under `docs/research/`; `specs/` and `plans/` entries are under `docs/superpowers/`. The V6.2 verification record was added by the frontend owner while the initial audit was in progress. Its recorded V6.1/V6.2 hashes match the reviewed files; the sample PDF has four A4 pages. Those artifact checks do not independently reproduce its 17 browser-check groups.

## 3. New synthesis produced by this pass

| Artifact | Purpose |
| --- | --- |
| [Architecture fit review](ARCHITECTURE_FIT_REVIEW.md) | Actual versus proposed tree, requirements fit, data/control flow, structural corrections and pilot boundaries |
| [Current solution landscape](SOLUTION_LANDSCAPE.md) | Primary-source comparison, version/edition/license caveats and reuse decisions |
| [Competition metrics and real-world validation](COMPETITION_METRICS_AND_REAL_WORLD.md) | Eight weighted criteria, formulas, proposed targets, held-out evaluations, manual evidence and analyst-time experiment |
| [PDF provenance manifest](sources/requirements-1-provenance.json) | Hash, pages, matching copy, exact criterion weights and local-source authority limit |
| [Rubric page image](sources/requirements-1-rubric-page-9.png) | Visual evidence for the rubric weights and total |

## 4. Document authority and consistency rules

1. Mandatory local PDF defines competition requirements; official listing adds submission logistics. If organizer updates are discovered, record source/date and diff instead of silently changing the baseline.
2. Current platform spec and contract define proposed implementation semantics. Earlier technical research supplies rationale; example endpoints are not independently authoritative APIs.
3. Master/parallel plans assign files and gates. Module plans consume those contracts. A contract change must update schemas/examples, backend DTOs and FE generated types together.
4. Prototype requirements describe UX and local simulation. Historical browser checks do not prove scanner/native parser/model/backend integration.
5. Verification records report only executed checks, environment, timestamps, artifact IDs/hashes and limitations. Proposed thresholds belong in evaluation docs, not results.

## 5. Verification and limits

Final document checks are recorded in [the audit manifest](sources/documentation-audit.json): inventory, language screening, local link resolution, required plan headings where applicable, PDF hash/rubric total and acceptance case counts. Vietnamese-character/phrase screening supplements manual English review; it is not a language classifier or proof of technical correctness.

New landscape and architecture references were checked against primary web sources. Earlier research citations retain their recorded access dates; this pass does not claim to have reopened every historical external URL.

Sources remain unchanged: `1.pdf`, retained PDF/text and pinned upstream JSON are reference artifacts. Current prototype HTML/test/screenshots are outside this documentation mutation scope. No application dependency installation, model call, scanner run, external target assessment or platform test execution was performed in this research pass.

The architecture is a fit recommendation. Competition targets, prior-art product claims and real-pilot gates remain distinct from measured CoreVAPT results. No score, detection accuracy, market uniqueness or production-readiness guarantee is made.

## 6. Follow-up research outputs and verification boundary

The next research pass adds [readiness decisions](READINESS_DECISION_REPORT.md), [organizer confirmation](ORGANIZER_CONFIRMATION_PACK.md), [scanner readiness](SCANNER_READINESS_DECISIONS.md), [G0 contract decisions](G0_CONTRACT_DECISIONS.md), [provider decisions](MODEL_PROVIDER_DECISIONS.md), and [safety/recovery/pilot decisions](SAFETY_RECOVERY_PILOT_DECISIONS.md). Existing specs/plans are synchronized with two-stage reservation/final-start authorization, AF-only ZAP and narrow host-launcher ownership; these remain design changes.

Public scanner format-reference metadata is retained in [scanner-readiness.json](sources/scanner-readiness.json). Five public samples were independently fetched/hash-checked and structurally inspected; none was executed by a scanner/application parser or retained as raw redistributed evidence. A legacy Greenbone file's 44 result elements share one UUID and have inconsistent counts; it cannot establish a genuine positive native acceptance fixture. The [follow-up evidence record](sources/readiness-research.json) distinguishes documentary checks from unrun platform gates.

Concurrent frontend work added [UX standards/page mapping](UX_STANDARDS_AND_PAGE_MAP.md) and a [V6.3 prototype plan](../superpowers/plans/2026-11-02-frontend-v6-3.md). They are included in the final language/link inventory. Their presence does not change frontend ownership or prove a V6.3 implementation; inspect the actual artifacts and their own verification record before making a runtime claim.
