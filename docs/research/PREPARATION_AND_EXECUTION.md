# CoreVAPT — preparation and revised solo schedule

Status: **post-research proposal**, not an approved implementation plan. All times are **UTC+7**. Event timestamps/source are recorded in the [research report](RESEARCH_REPORT.md); the schedule below is internal, not an additional organizer deadline. Original research: **2026-11-01**; English audit: **2026-11-02**. Historical environment checks were not rerun.

## 1. What Phase A should deliver

The user selected Statement 1, solo participation, and the balanced strategy. Retain these choices. Research identified remaining decisions: conversational UX, lab/ROE, evidence/action contracts, correlation rules, and demonstration approach.

| Work package | Research input | Formal output | Exit criteria |
| --- | --- | --- | --- |
| WP-01 Product | PDF and requirement matrix | `docs/PRODUCT_SPEC.md` | Acceptance for every MVP requirement; explicit exclusions |
| WP-02 Architecture | Technical recommendations | `docs/ARCHITECTURE.md` | Clear state/evidence ownership, enforcement, and worker failure handling |
| WP-03 Technical design | Scanner/agent research | `docs/TECHNICAL_DESIGN.md` | Interfaces, invariants, errors, and one connected happy path |
| WP-04 Data/API | Proposed entities/contracts | `docs/DATA_MODEL.md`, `docs/API_SPEC.md` | Versioned action approval, observations, traceability, consistent JSON examples |
| WP-05 Environment | Historical snapshot below | Checklist; skeleton if event rules permit | Pinned versions; actual build/healthcheck before verified claims |
| WP-06 UX/demo | Rubric/live checklist | `docs/UI_UX.md`, `docs/DEMO_SCENARIO.md` | Request, evidence, uncertainty, approval, and failure represented |

Research supplied inputs to these outputs. It did not complete all six packages. Later documents/prototypes must be assessed separately; do not assign arbitrary 0%/100% completion. Research evidence, design decisions, and runtime gates are distinct.

### Before prebuild permission is verified

Read sources, settle scope, draw documentation diagrams/wireframes, define acceptance, and draft questions. The original research copied skills/docs and performed read-only environment checks. “Preparation” did not imply authorization for application code, migrations, parsers, or scanner fixtures before kickoff.

If organizers permit generic scaffolds/existing code, disclose baseline commit/timestamp, template/dependency provenance, and work completed during the event. If prohibited, start product code at kickoff. Without an answer, record unknown and follow the user's chosen implementation boundary. This historical rule discussion is not a claim about permissions subsequently granted by the user or organizer.

## 2. Organizer questions — draft, not sent

Check official Discord announcements/pins before asking. Do not ask questions already resolved by the PDF, such as whether native imports are allowed.

1. **Prebuild:** Which documents, wireframes, generic scaffolds, templates, and existing code are allowed? Must code start at kickoff? Is baseline/history disclosure required?
2. **AI assistance:** Are coding agents/model APIs allowed? Are disclosures, tool restrictions, or credits involved?
3. **Lab/ROE:** When are targets/credentials supplied? Which IPs/domains/ports, rates/concurrency, replicas, DNS/redirect/egress rules, and data-handling terms apply?
4. **Validation:** Which active profiles can be approved and which remain prohibited? If no active permission is supplied, does a blocked gate with audit satisfy the checklist?
5. **Evidence:** Are native exports provided for import/correlation? Can teams capture authorized-lab fixtures and publish redacted copies?
6. **Submission/judging:** Is submission earlier than event end? PPT/video length, live judging, private-repository review, and report/evidence access requirements?
7. **Participation:** Can a Vietnam-based participant receive prizes/internships? What payout/KYC, IP, open-source, and reuse conditions apply?

These are unresolved questions, not asserted restrictions. The original research did not enter private Discord or contact organizers.

## 3. Historical local environment snapshot

Observed **2026-11-01**, without installations/service changes. Not rerun during translation.

| Item | Observation |
| --- | --- |
| Python / python3 | 3.13.13 |
| Node / npm | v22.23.2 / 10.9.8 |
| Docker / Compose | 29.6.2 / v5.5.1 |
| Git | 2.43.0 |
| Logical CPUs | 16 |
| RAM | Approximately 15 GiB total; 4.3 GiB available at observation |
| Swap | 4 GiB total; approximately 1.5 GiB used |
| Workspace filesystem | Approximately 14 GiB free; 92% used |

These are recorded command outputs, **not a compatibility-tested version matrix**. PostgreSQL, image cache, scanners, Java/browser dependencies, model credentials, and port conflicts were not checked. RAM/disk values are snapshots to refresh before building; do not stop containers/delete data without authorization.

**Design inference from that snapshot:** full live Greenbone plus concurrent browsers/scanners risks resource pressure. Prefer import-only Greenbone, one scanner job at a time, and storage/log limits. No benchmark establishes exact memory/disk requirements.

When implementation is authorized, select compatible interpreter/container releases, lock packages, pin scanner releases/digests, and smoke-test those versions. Latest documentation alone is not a reason to upgrade the whole machine.

Compose readiness requires `healthcheck` and `depends_on: condition: service_healthy`; started containers do not establish DB readiness. Make migration a separate prerequisite to API/worker, avoiding competing automatic migrations. [Docker startup order](https://docs.docker.com/compose/how-tos/startup-order/).

## 4. Proposed solo schedule using vertical slices

The recorded event window is approximately 130 hours, **not 130 continuous work hours**. Proposed focused effort is 40–45 hours, allowing sleep/buffer. Estimates are not measured development throughput.

| Internal block | Focus | Observable result | Suggested effort |
| --- | --- | --- | ---: |
| 02 November afternoon/evening | Foundation, scope, import slice | Assessment → labeled native fixture import → observation → initial PDF | 5h |
| 03 November | Nmap, ZAP, evidence | Two bounded live profiles on authorized lab; genuine status/raw/parsing | 8h |
| 04 November | Third adapter, correlation, risk | Multi-source ingestion; positive/negative merge cases; explainable ranking | 8h |
| 05 November | Adaptive planner, policy/approval, failure | Evidence changes action; invalid action blocked; audit to outcome | 8h |
| 06 November | E2E, UI/report refinement, demo draft | Complete assessment, all report sections, trial recording | 7h |
| 07 November | Fix, verify, submit early | Repository/README, PPT, video, PDF, matrix, reviewer link access | 6h |

Scope/policy/execution guards belong in the foundation; 05 November expands workflow/UX. An early PDF checks that contracts support reporting before visual refinement.

### Solo risk gates

- No working slice after foundation: reduce UI and stop adding dependencies.
- No valid third-adapter native data: choose/disclose fallback immediately rather than spend a day building a full scanner stack.
- Unstable live scanners: prioritize one reliable live path with supported imports; fixtures cannot impersonate execution.
- LangGraph pause/resume increases risk: use the designed state-machine alternative transparently; avoid a hidden last-night stack change.
- One day before submission: freeze features and prioritize correctness, failures, reports, and access. Mark unfinished advanced work Planned/Unsupported.

## 5. UX questions for wireframes

The original proposal grouped six views within one assessment workspace. The current [v6.2 requirements](FRONTEND_V6_2_REQUIREMENTS.md) refine this into six workflow steps; the underlying analyst questions remain applicable.

| View | Analyst question |
| --- | --- |
| Request & scope | What testing am I authorizing, against which targets, and when? |
| Plan & timeline | What will the agent do, why, what is waiting, and what failed? |
| Findings | What requires remediation/verification, and on which asset? |
| Finding detail | What is fact/inference, and what evidence/source/validation supports it? |
| Approval | Which exact action, impact, and validity am I approving? |
| Report | What was tested, untested, blocked, or failed; which PDF can I download? |

Use text/icons as well as color. Adaptive workflows should not invent completion percentages; phase/job counts and elapsed time are more defensible. Display `unknown`, `partial`, `import-only`, and `needs_review` at decision points.

## 6. Proposed 6–8 minute demonstration

This is an internal timebox; organizer demo duration was unverified.

1. **Request/scope:** enter a natural-language request and lab target; show a denied out-of-scope action with its reason.
2. **Plan:** select discovery with rationale/evidence context and visible granted authority.
3. **Execution:** genuine Nmap status/XML; propose web assessment only after observing HTTP. Use a labeled counterexample/replay to show the no-HTTP branch.
4. **Multi-tool:** ZAP output and Greenbone native import; disclose source timestamps/modes and inspect one source record.
5. **Intelligence:** correct merge, correct non-merge, both sources, uncertainty, and analyst disposition. Disclose captured-fixture use.
6. **Approval:** pending validation cannot run; reject/approve the exact lab-authorized action and show its actual outcome. Do not claim unsupported offensive adapters.
7. **Report/failure:** download PDF, trace one finding to original evidence, and disclose timeout/partial coverage and the integration matrix.

Recorded video may cut long waits while preserving assessment IDs/timestamps. Distinguish recorded output from current execution. Keep receipts/artifacts for fallback when model/network access fails.

## 7. Pitch and submission package

Suggested seven-slide pitch: analyst problem; CoreVAPT value; flow/architecture; adaptive evidence-backed decision; correlation/risk/evidence; scope/approval/limitations; measured results and demo/setup. Seven slides is a recommendation, not an organizer rule.

Repository contents: reproducible README, dependencies/lockfiles, secret-free sample config, migrations/setup, lab assumptions, truthful integration matrix, evidence provenance, license assumptions, and limitations. Exclude credentials, tokens/cookies, and sensitive raw data. Share sample PDF/redacted fixtures only with permission; keep raw private where needed.

Proposed presubmission checks: fresh README setup; primary workflow and relevant negative cases; downloadable/readable PDF; consistent metrics; reviewer links accessible while logged out; all submission fields present; Planned work never labeled Implemented. The original research did not run these checks.

## 8. Efficient learning order

1. PDF §§3/5/6/7/10/11: acceptance and rubric.
2. Nmap XML and ZAP baseline/JSON: native evidence and execution states.
3. Greenbone native XML/QoD: import scope and provenance.
4. Action/scope/approval/worker lifecycle: side-effect control.
5. Correlation identity, confidence, and CVSS context: correct data before narrative.
6. LangGraph persistence/interrupts if selected: replay semantics before live tools.
7. Reporting/UX/demo: evidence translated into clear decisions.

Metasploit, multi-agent orchestration, LLM training, and Kubernetes are not needed for this MVP. Its value must be demonstrated through evidence-backed decisions and reproducible operation.
