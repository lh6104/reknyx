# Existing Solutions and the CoreVAPT Build Decision

Verification date: **2026-11-02**. Status: **research and proposed design; no product implementation or integration verification**.

**Recommendation:** retain a small CoreVAPT modular monolith and worker for the contest, with three narrow scanner integrations, action approval, evidence handling, and a report renderer. Learn from existing platforms and keep a future export boundary to a vulnerability manager. Do not build a replacement for DefectDojo, Faraday, or Dradis. Their documented capabilities already cover substantial parts of consolidation, triage, collaboration, and reporting.

This recommendation is a **design inference for a solo contest project**, not a finding that custom software is generally better than adopting these products. A security team whose immediate problem is managing scanner results should evaluate an existing manager first.

## 1. Method and evidence boundaries

The research used live web browsing of official documentation and read-only GitHub plugin retrieval of public repository metadata, READMEs, licenses, and selected source files. Repository branch heads were checked on the verification date. No framework was cloned or installed for this landscape, no scanner or upstream application was run, and no model or paid service was called.

The local baseline was [the upstream comparison](UPSTREAM_ARCHITECTURE_COMPARISON.md), [Fennec review](FENNEC_ARCHITECTURE.md), [PentestGPT review](PENTESTGPT_ARCHITECTURE.md), and [technical recommendations](TECHNICAL_RECOMMENDATIONS.md). The contest fit below uses the existing [requirements matrix](REQUIREMENTS_MATRIX.md); this landscape did not independently re-verify organizer rules.

Evidence labels used throughout:

- **Documented fact:** the official source describes the capability. This establishes what is documented, not that it works in our environment.
- **Static source fact:** selected code contains the described structure or behavior at the pinned commit. No runtime test is implied.
- **Design inference:** a proposed CoreVAPT decision derived from the comparison.
- **Not verified:** this research did not establish the capability, entitlement, or behavior. This does not mean the capability is absent.

Vendor effectiveness claims, demo screenshots, repository popularity, and benchmark numbers are not treated as proof of detection quality, safety, or superiority. The comparison is selective rather than an exhaustive market survey. Dradis represents the reporting category and reNgine represents recon orchestration; PwnDoc and Osmedeus were not independently assessed. Commercial platforms such as XBOW and Pentera are outside this comparison, so no performance parity with them is claimed.

## 2. Products solve different parts of the workflow

| Solution | Primary documented job | Execution/import boundary | Relevant source |
| --- | --- | --- | --- |
| DefectDojo | Normalize, triage, and track security findings over time | OSS receives scan files through UI/API; Pro adds upstream result connectors | [Edition comparison](https://docs.defectdojo.com/get_started/about/defectdojo_versions/) |
| Faraday | Organize assessment assets, services, vulnerabilities, and analyst work | Report/console plugins and a separate remote Agent Dispatcher | [Repository README](https://github.com/infobyte/faraday/blob/d00e81cd9c0279e9fa7cc48d80e52f5ced820cb1/README.md) |
| Dradis CE / Pro | Organize issues, instance evidence, notes, and assessment reports | Import scanner output and add analyst findings; advanced workflows vary by edition | [CE overview](https://dradis.com/ce/) |
| reNgine | Run configurable reconnaissance and vulnerability-scanning workflows | YAML scan engines with multiple tools; scan reports are an output | [Scan-engine documentation](https://rengine.wiki/usage/scan_engine/) |
| PentestGPT | Maintain and execute an adaptive pentest task loop | Maintained nested framework uses general provider tools in an isolated deployment | [Agent README](https://github.com/GreyDGL/PentestGPT/blob/e8b1bb77d1ac00329675cec3b060aba971ec1ac8/pentestgpt_agent/README.md) |
| Fennec OSS | Recon, generate hypotheses, test them, and present findings through agents | Role-based graph with optional hypothesis review and tool execution | [Role graph](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/src/graph/role_based_graph.py) |

A dashboard that combines scanner output, severity charts, and AI-generated remediation is therefore insufficient as a novelty claim. The contest opportunity is a coherent, inspectable workflow across these responsibilities, with a smaller supported scope.

## 3. Repository and license snapshot

These are the branch heads returned by GitHub on **2026-11-02**, not a recommendation to deploy development branches. Documentation websites can change independently of repository commits. A license recorded here applies to the inspected repository material; it does not establish the licenses of bundled scanners, images, dependencies, hosted products, or models.

| Repository / checked branch | Commit | Root license evidence |
| --- | --- | --- |
| DefectDojo/django-DefectDojo / `master` | `c360df03a9399cbe6b26138bd0289949c27eb732` | [BSD three-clause text](https://github.com/DefectDojo/django-DefectDojo/blob/c360df03a9399cbe6b26138bd0289949c27eb732/LICENSE.md) |
| infobyte/faraday / `master` | `d00e81cd9c0279e9fa7cc48d80e52f5ced820cb1` | [GNU GPL version 3 text](https://github.com/infobyte/faraday/blob/d00e81cd9c0279e9fa7cc48d80e52f5ced820cb1/LICENSE) |
| dradis/dradis-ce / `develop` | `d9bd8b28a26890f54a952b22ed4addd4237cec75` | [README explicitly identifies GPLv2 for CE and a commercial license for Pro](https://github.com/dradis/dradis-ce/blob/d9bd8b28a26890f54a952b22ed4addd4237cec75/README.md#license); a separate root license file was not retrieved |
| yogeshojha/rengine / `master` | `de4199222cca5618f1255930ce78987e47d43a99` | [GNU GPL version 3 text](https://github.com/yogeshojha/rengine/blob/de4199222cca5618f1255930ce78987e47d43a99/LICENSE) |
| GreyDGL/PentestGPT / `main` | `e8b1bb77d1ac00329675cec3b060aba971ec1ac8` | [MIT](https://github.com/GreyDGL/PentestGPT/blob/e8b1bb77d1ac00329675cec3b060aba971ec1ac8/LICENSE.md) |
| Fennec-AI/Fennec / `main` | `e56c8c1c5cbeea93b719f8001ea136c6b15c7055` | [Apache License 2.0](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/LICENSE) |

**Design inference:** architecture ideas can be studied without copying code. Any later code reuse needs a component-level license inventory and the applicable notices and distribution obligations. A root license is not a blanket permission for everything a framework invokes. No legal compatibility conclusion is made here.

## 4. Findings by solution

### 4.1 DefectDojo: strongest reference for finding lifecycle and import semantics

**Documented facts.** The current OSS hierarchy is Organization → Asset → Engagement → Test → Finding, with affected URL/host locations represented separately. Time-boxed pentests can use distinct engagements, while repeated scans can reimport into a test. This gives scan context a place in the model rather than making every uploaded row an unrelated record. [Official FAQ](https://docs.defectdojo.com/get_started/about/faq/).

Reimport matching is separate from post-import deduplication. Reimport can create new findings, preserve matching ones, close missing ones, and reopen returning ones. Partial scans need care: closing absent findings can misrepresent remediation when coverage changed. [Reimport semantics](https://docs.defectdojo.com/import_data/import_intro/reimport/). Duplicate records are linked to an original rather than automatically discarded; matching scope and fields matter. [Deduplication documentation](https://docs.defectdojo.com/triage_findings/finding_deduplication/about_deduplication/).

**Edition boundary.** The official comparison marks same-tool deduplication, risk acceptance records, and HTML report building as OSS features; cross-tool deduplication, contextual prioritization, and saved PDF reporting are Pro capabilities. An OSS deployment cannot be assumed to satisfy CoreVAPT's correlation and PDF requirements unchanged. A finding risk-acceptance workflow also concerns handling an existing finding, not granting permission to run an offensive action. [Edition comparison](https://docs.defectdojo.com/get_started/about/defectdojo_versions/).

**Design inference — learn/integrate.** Reuse the distinction between scan context, import matching, duplicate membership, and analyst disposition. Keep imported observations when building a canonical finding. Add a downstream export later if teams already use DefectDojo: its [Generic Findings Import](https://docs.defectdojo.com/supported_tools/parsers/generic_findings_import/) documents JSON/CSV intake and API import. CoreVAPT should own its action/approval/evidence chain; the manager should own downstream remediation after an explicit handoff.

**Not verified:** byte-for-byte preservation of every original scanner report, hashes and raw selectors for every parser, exact-action pre-dispatch approval, or the contest's complete adaptive workflow. Those properties require a focused acceptance test rather than an inference from the number of parsers.

### 4.2 Faraday: closest candidate if operational adoption replaces contest construction

**Documented facts.** Workspaces collect the results of assessment tools and commands. Findings attach to assets and, when relevant, services; web vulnerabilities can include request/response data. The UI supports evidence images, severity, impact, references, confirmation state, comments, and analyst edits. [Workspaces](https://docs.faradaysec.com/Workspaces/), [vulnerability management](https://docs.faradaysec.com/Vulns/).

Faraday distinguishes console-output plugins from report-import plugins. Its import matrix explicitly lists Nmap XML, OpenVAS XML, and ZAP XML/JSON. Remote execution is a separate dispatcher responsibility rather than something a file parser inherently supplies. [Supported import formats](https://docs.faradaysec.com/import/), [Agent Dispatcher deployment](https://docs.faradaysec.com/agents-v4/).

The current grouping documentation describes optional automatic grouping by similar names or shared CVE, plus manual groups. Group members remain inspectable, and the highest-risk member represents a group. The separate asset-deduplication operation creates a new workspace while preserving the inactive original; it describes a narrower duplicate-vulnerability match using name, type, description, and service. These are different operations. [Grouping](https://docs.faradaysec.com/Grouping/), [asset deduplication](https://docs.faradaysec.com/Deduplicated-Assets/).

The executive-report documentation describes a customizable HTML builder with PDF export and explicitly distinguishes it from legacy DOCX reporting. **The precise edition entitlement for this builder, grouping, and agent automation was not verified.** A product documentation page is not sufficient evidence that every capability is available in the OSS checkout. [Executive reports](https://docs.faradaysec.com/Executive-Reports/).

**Design inference — evaluate adoption, otherwise learn.** Faraday deserves the first focused trial if the goal becomes an operational multi-tool workspace: it documents both data intake and remote execution. CoreVAPT should learn its host/service/web-location distinctions and preserve group members. Group-by-CVE is useful for rollups; it is not a rule that two affected assets are the same vulnerability instance. A custom planner wrapped around Faraday still needs its own scope policy, action approval, evidence links, and failure semantics.

**Not verified:** the current risk-score formula and treatment of missing inputs; immutable original artifacts for every plugin; a durable approval bound to the exact outgoing action; successful end-to-end execution of the three intended tools; or OSS feature parity with the full documentation.

### 4.3 Dradis: strongest reference for analyst-facing evidence and reporting

**Documented facts.** Dradis separates an Issue's reusable description and recommendation from Evidence that changes per affected instance, such as port, version, and tool output. Evidence belongs to a node representing its context. This is directly relevant to reporting one issue without losing distinct affected instances. [Issue/evidence guide](https://dradis.com/support/guides/projects/issues.html).

The current CE page explicitly advertises scanner imports, manual findings, screenshots, methodology checklists, and **HTML, PDF, and CSV export**. It also describes a single-project workflow and basic, non-branded templates, with advanced QA/approval and customization positioned as Pro features. Therefore, “Dradis CE has no PDF” would be an unsupported claim. [CE overview and edition limitations](https://dradis.com/ce/). The separately documented Rules Engine offers cross-scanner merging and rewriting; its exact entitlement in CE was not verified here and must not be assumed from the general product page. [Rules Engine](https://dradis.com/tools/rules-engine.html).

**Design inference — learn, optionally use for manual reporting.** Borrow the issue/evidence separation, instance-oriented report views, and analyst edit/review flow. Dradis may be the best direct adoption when the real problem is producing reports from already collected evidence. For CoreVAPT, replacing the whole workflow with Dradis leaves the adaptive executor and its approval seam to build, while changing the runtime stack to Rails and its plugins. A separate reporting product is unnecessary for the first contest slice if a small renderer can satisfy the six required sections.

**Not verified:** a live Nmap/ZAP/Greenbone orchestration path, policy-enforced action approval, reproducible artifact hashes/raw locators, automated business-context priority in CE, or a CE template matching the exact contest report. Finding/report QA is not the same control as permission before network activity.

### 4.4 reNgine: practical reference for scanner orchestration and operator controls

**Documented facts.** reNgine scan engines use YAML to configure subdomain discovery, crawling, ports, endpoint collection, vulnerability scans, screenshots, and related tasks. Options include timeouts, concurrency/rates, tool selections, Nmap settings, endpoint deduplication, and optional GPT report content. The documented endpoint deduplication configuration uses fields such as content length and page title; it does not establish semantic cross-scanner finding correlation. [Scan-engine configuration](https://rengine.wiki/usage/scan_engine/).

The official report guide documents Full Scan, Reconnaissance, and Vulnerability PDF reports. The repository also describes database-backed recon organization, projects, subscans, roles, and GPT-assisted vulnerability descriptions/remediation/impact. These are documented features and claims, not measured accuracy or coverage results from this study. [Report guide](https://rengine.wiki/usage/report/), [repository README](https://github.com/yogeshojha/rengine/blob/de4199222cca5618f1255930ce78987e47d43a99/README.md).

**Design inference — learn, do not adopt the whole stack for P0.** Scan history, fixed tool profiles, bounded execution parameters, focused follow-up scans, and visible partial failures are useful patterns. A broad reconnaissance stack brings more tools, target-discovery behavior, configuration surface, and operating work than the three intended integrations require. Represent the small CoreVAPT capability catalog in typed data; do not expose arbitrary YAML or command strings as authority from the model.

**Not verified:** native ZAP and Greenbone result paths suitable for this MVP, evidence-preserving cross-tool canonicalization, contextual risk policy, exact-action approval, current deployment reproducibility, or an adaptive reasoning loop tied to captured evidence. A scanner configuration that names exclusions is not proof that all DNS, crawl, redirect, and subprocess destinations are contained.

### 4.5 PentestGPT: strongest reference for typed decisions and receipt-grounded state

**Documented/static facts.** The maintained `pentestgpt_agent` framework is distinct from the root legacy human-driven workflow. It documents SQLite canonical state, fresh Supervisor/Executor episodes, one leased task at a time, trace recovery, and receipt-backed observations. It also states that both roles have provider tools and `FULL_ACCESS`, relying on an isolated deployment. Its current-limits section places structured findings and product report generation in future work. [Maintained agent README](https://github.com/GreyDGL/PentestGPT/blob/e8b1bb77d1ac00329675cec3b060aba971ec1ac8/pentestgpt_agent/README.md).

The plan compiler checks state revision, allowed target identity, basis observation IDs, dependencies, and completion basis. These are useful semantic validations beyond JSON shape. They do not demonstrate that every tool's actual destination is constrained, or that a person approves every sensitive invocation. [Plan compiler](https://github.com/GreyDGL/PentestGPT/blob/e8b1bb77d1ac00329675cec3b060aba971ec1ac8/pentestgpt_agent/src/pentestgpt_agent/plan.py).

**Design inference — learn, retain a custom execution seam.** Apply the principles of revisioned state, typed action proposals, real receipts, and reconciliation before retry. CoreVAPT should preserve native artifacts in addition to bounded model excerpts. A receipt proves an operation produced captured output; it does not prove that a security conclusion follows from the output. Keep finding validation and risk ranking as separate responsibilities. Adopting the autonomous runner would still leave scanner-specific import contracts, action-bound human approval, the common finding model, and the required PDF to implement.

**Not verified:** a typed Nmap/ZAP/Greenbone adapter suite, cross-scanner finding deduplication, contest risk scoring/reporting, runtime containment, or model effectiveness for CoreVAPT. There is no basis here for transferring CTF or upstream benchmark results to the contest.

### 4.6 Fennec: useful hypothesis workflow, with important OSS execution boundaries

**Documented/static facts.** The role graph separates recon, analyst, pentester, and a deterministic Python orchestrator. Optional human review sits after the analyst; the default graph disables it. The review node interrupts with a hypothesis snapshot and accepts edits or approval when resumed. This is a hypothesis-review mechanism, not evidence of a grant bound to each exact tool invocation. [Role graph](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/src/graph/role_based_graph.py), [human-review node](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/src/agents/human_review.py).

Finding schemas include description, impact, request/response evidence, remediation, and safe/inconclusive verdicts, but rich fields are optional in the model. Their existence does not establish that every finding is evidenced or exploitable. [Result schema](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/src/schemas/pentester_result.py). OSS dashboard jobs are held in process-local dictionaries. Terminal execution includes a local shell path, while browser fetching uses a direct HTTP client. [Job store](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/src/api/job_store.py), [execution tools](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/src/tools/execution.py).

The README describes JSON/Markdown export and a separate hosted offering. Claims about finding effectiveness and scan duration were not validated; hosted persistence and team features cannot be attributed to the OSS implementation. [README](https://github.com/Fennec-AI/Fennec/blob/e56c8c1c5cbeea93b719f8001ea136c6b15c7055/README.md).

**Design inference — learn, avoid wholesale adoption.** Use a small hypothesis record: question, basis observation IDs, expected evidence, stopping condition, and outcome. Let deterministic code decide which supported action is eligible. Keep durable state, scanner permissions, and finding confirmation outside the model. Do not turn an LLM verdict or an expected artifact name into evidence. Preserve the local review's distinction between `execution_status`, hypothesis outcome, validation status, and coverage.

**Not verified:** the required three scanner contracts, reliable cross-scanner correlation, the contest PDF, durable restart recovery, exact-action approval, risk-score validity, or real-world detection performance. Detailed source caveats remain in the [existing Fennec review](FENNEC_ARCHITECTURE.md).

## 5. What the contest still requires from CoreVAPT

This table is a **design assessment against the local requirements matrix**, not a new statement of organizer rules or a declaration that another product cannot be extended.

| Requirement boundary | Existing work to learn from | CoreVAPT responsibility that remains |
| --- | --- | --- |
| Three working integrations spanning network and web | Faraday and Dradis document relevant parsers; reNgine documents execution profiles | Deliver and demonstrate Nmap live XML, a constrained ZAP live profile with native output, and Greenbone native XML import. None is implemented by this research. An upstream plugin listing does not count as a working CoreVAPT integration. |
| Evidence-dependent next step | PentestGPT's typed decisions; Fennec's hypothesis/router pattern | Capture at least one inspectable adaptive branch: observed HTTP justifies a supported web profile; absent or insufficient evidence produces a skip, question, or stop reason. Keep a plan/revision and basis IDs. |
| Human approval before covered active/offensive validation | Human review and risk acceptance exist in several products at different stages | Bind approval to actor, exact action/profile/parameters, target, scope revision, expiry, and budget; recheck at dispatch and record outcome. Analyst confirmation, report QA, risk acceptance, and pre-action permission are distinct decisions. |
| Common data, provenance, correlation, and uncertainty | DefectDojo's lifecycle; Faraday's asset/service organization; Dradis's issue/evidence split | Preserve raw artifacts and parser versions, observations, canonical membership, conflicts, and review reasons. Nmap service discovery is context, not an automatic vulnerability or a duplicate ZAP alert. |
| Explainable priority | Managers expose severity, disposition, and various contextual fields | Preserve source severity/CVSS vector/version, validation method, exposure, exploitability, asset impact, and unknowns separately. Publish a small versioned priority policy. Do not copy an opaque aggregate score or treat model confidence as probability. |
| Required six-section PDF | Existing products demonstrate that rendering and customization are established capabilities | Freeze a reviewed snapshot, then render Executive Summary, Assessment Methodology, Severity Distribution, Detailed Vulnerability Findings, Impact and Remediation, and Assessment Limitations. Include failures, timestamps, historical imports, pending approvals, and evidence references. Validate the actual downloaded file. |
| Failure and recovery | PentestGPT's receipts and recovery; managers' import history | Record attempt IDs, receipts, partial/failed/unknown execution, and assessment coverage. A lost response after dispatch must not trigger a blind rescan. “No findings” does not mean coverage completed or the asset is safe. |

The narrow design remains the existing eight responsibilities: Assessment, Planner, Policy/Approval, Tool Runner, Normalizer, Correlation, Risk, and Report. Keep one canonical store in PostgreSQL, private local artifact storage, and a worker sharing the codebase. These are module boundaries, not eight services. A small static capability catalog and polling UI are enough for the first slice.

## 6. Adopt, integrate, or build

All judgments in this section are **design inferences**. No timed installation or feature-fit trial was performed, so there are no evidence-backed estimates of setup days or operating cost.

| Path | What it can save | Work and risk still introduced | Decision for the solo contest |
| --- | --- | --- | --- |
| Adopt DefectDojo or Faraday as the main product | Established finding intake, lifecycle, collaboration, and views | Edition checks, deployment, data-model mapping, custom planner/policy, provenance gaps, exact report acceptance; Faraday automation needs a focused trial | Strong real-world option when operational vulnerability management is the actual goal; do not assume it is the fastest route to demonstrating the contest's custom adaptive workflow |
| Adopt Dradis for evidence/report delivery | Established analyst organization and report workflow | Separate executor/planner remains; exact template and edition fit; additional application and data handoff | Appropriate for a reporting-first service; unnecessary extra runtime for the first CoreVAPT vertical slice |
| Integrate reNgine, PentestGPT, or Fennec as the execution core | Existing orchestration or adaptive-agent logic | Wider tool authority and runtime, different state models, scanner contract gaps, approval reconstruction, and report work | Do not choose for P0; study patterns and keep the actual runner limited to supported profiles |
| Build the small CoreVAPT modular monolith; use scanners directly | One coherent assessment/action/evidence/report model and controllable demo scope | Own parser correctness, policy enforcement, correlation, recovery, PDF, and acceptance evidence | Recommended for the contest only if the scope stays at three adapters and a few meaningful adaptive decisions |
| Keep CoreVAPT as a bounded coordinator and export to a manager later | Existing teams retain their remediation workflow | Mapping, credentials, idempotency, ownership conflicts, and provenance links | Preferred integration direction after the core path works; start with one export boundary, not bidirectional synchronization |

For a future handoff, CoreVAPT should own assessment decisions, permissions, execution/import receipts, raw artifacts, and its report snapshots. A downstream manager can own remediation tickets and operational dispositions. Export a stable CoreVAPT finding ID, affected instance, source references, and review state; keep a mapping to the downstream ID. Do not permit an exported status such as “accepted risk” to become permission for a new scan. This is a proposed contract, not an existing connector.

## 7. Differentiation, real-world value, and proof

**Proposed differentiator:** an analyst can follow a small, complete chain from captured observation → reason for the next supported action → policy and human decision → actual execution/import receipt → reviewed finding → the corresponding report evidence. The system should explain what it did not test and why it stopped. This is a potential presentation and workflow advantage within the contest; this research does not establish global novelty.

**Real-world value hypothesis:** reduce the analyst's effort to reconcile scanner output and produce a defensible report, while making risky automation more controllable. A useful product would also need supportable deployment, secure artifact access, good parser behavior, reliable updates, and compatibility with an existing remediation system. Having more agents or producing more findings is not by itself a customer benefit.

Proposed measurements, all **not yet run**:

| Question | Appropriate evidence |
| --- | --- |
| Can a reviewer trace report claims? | Percentage of included findings whose evidence IDs resolve to the original artifact, hash, location, run/import, parser, and review decision; verify samples manually |
| Does correlation preserve affected instances? | Precision/recall on labeled observation pairs, including same CVE on different assets and similar titles at different web locations; retain disagreements |
| Does adaptive planning help? | Same lab/evidence set, compared with a fixed allowed workflow; inspect action validity, unnecessary repetitions, coverage, and stopping reasons |
| Do approvals control the intended action? | Negative cases for missing/denied/expired approval, changed parameters, changed scope, and restart while awaiting review; inspect dispatch and audit outcomes |
| Does recovery avoid accidental repetition? | A controlled worker interruption around dispatch/receipt, followed by reconciliation; unresolved external work remains `execution_unknown` |
| Does it save analyst effort? | Paired manual versus assisted workflow on the same evidence, with stated conditions and multiple observations where feasible; record correction effort as well as elapsed time |
| Is the report usable? | Inspect the downloaded six-section PDF, evidence links, counts, Unicode/fonts, page breaks, limitations, and historical-import labels |

Until these checks exist, describe benefits as expected or proposed. Do not claim lower false positives, better coverage, stronger isolation, or faster completion than the surveyed products. Contest scoring depends on organizer rules and demonstrated execution; **this architecture and landscape provide no score or qualification guarantee**.

## 8. Gates before changing this decision

Reconsider adoption if a narrow trial shows an existing platform already provides the required three native paths, provenance, approval control, adaptive extension point, and exact PDF with less total integration work. Conversely, stop expanding the custom scope if any of the three adapters, enforcement, or report path remains unreliable.

Unresolved checks are concrete: approved lab/ROE; permission for any active validation; actual Greenbone export version and provenance; Faraday edition entitlements and risk semantics; Dradis CE report customization and plugin/API availability for a chosen version; licenses of every redistributed component; and a deployment-level scope-control test. No feature or permission marked not verified should silently become an implementation promise.
