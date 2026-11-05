# CoreVAPT — researched merge of V6.2 and V6.3

Date: 2026-11-02. Original status: **research and proposed UX merge**. Subsequent status: **approved by the user and implemented as the standalone V6.4 preview**; see [implementation/verification](FRONTEND_V6_4_VERIFICATION.md). User scope: reconsider the merge, remove redundant sidebar creation, make Agents and Workflow understandable, and avoid unnecessary pages/configuration. The user explicitly selected **one assessment assistant**, showing its role, model, capabilities, limits and assessment activity. This is not a request for a runtime multi-agent system.

Original research outputs: this report and [inspection evidence](sources/frontend-merge-inspection-2026-11-02.json), plus discovery links in existing documentation. That research used V6.3 as its runnable baseline and did not edit HTML. V6.2/V6.3 HTML, their browser scripts, backend contracts and historical verification records remain unchanged. The approved follow-up created [V6.4](../../corevapt_frontend_v6.4.html) and a [separate browser suite](../../tests/prototype-v6.4.spec.cjs). Sections below preserve the research rationale and proposed acceptance wording; actual results are recorded separately.

## 1. Basis and fresh observations

Read the root [README](../../README.md), [readiness decisions](READINESS_DECISION_REPORT.md), [frontend handoff](../superpowers/plans/2026-11-02-01-frontend-handoff.md), [current UX/page model](UX_STANDARDS_AND_PAGE_MAP.md), relevant [G0 decisions](G0_CONTRACT_DECISIONS.md), and provider-neutral planning boundaries in [provider decisions](MODEL_PROVIDER_DECISIONS.md). All ten pages of [1.pdf](../../1.pdf) were reread. Its SHA-256 remains `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

The mandatory PDF describes eight workflow activities, adaptive evidence-led decisions, analyst control, traceable findings and six report sections. It does not mandate six separate pages, a configurable workflow builder or several independent AI agents.

Fresh inspection opened the existing assessment in both prototypes at 1440 and 390 CSS pixels. Temporary screenshots and source inspection were used; no broad prototype suite was rerun. Four inspected local views had no uncaught page errors, external HTTP(S) requests or horizontal page overflow. These observations do not measure usability, integration or security enforcement. The earlier [V6.2](FRONTEND_V6_2_VERIFICATION.md) and [V6.3](FRONTEND_V6_3_VERIFICATION.md) suites remain historical evidence, not new results from this research.

| Question | V6.2 observation | V6.3 observation | Merge implication |
| --- | --- | --- | --- |
| Where does work start? | Opens the Plan stage; no dedicated cross-assessment dashboard | Dashboard supports current attention and recent assessments | Keep V6.3 Dashboard |
| Is the lifecycle visible? | Six visible stage buttons: Scope, Plan, Run, Analyze, Review, Report | Three working views; lifecycle is inside a closed `details.lifecycle-summary` by default | Restore visible lifecycle orientation without restoring six compulsory pages |
| What is the assistant? | `Assessment agent` is a workspace destination and chat panel; no assistant profile page | Agent is embedded in `Agent & runs`; no Agents destination | Add one explicit assistant profile and a visible assessment binding |
| Is creation navigation or an action? | `renderSidebar()` creates a New assessment launcher; workspace also defines a mobile header launcher | Same sidebar launcher; mobile header launcher; Dashboard/Assessments also have their own creation CTA | Remove creation from sidebar/mobile navigation and standardize the header action |
| Can the analyst understand execution? | Separate Run view and detailed attempt cards | Compact run list; details open contextually | Keep compact list, preserve detailed attempt/provenance views |
| Can analysis/review stay coherent? | Analyze and Review are separate working views | Findings combines the register and review entry points | Keep one Findings workspace with explicit source-comparison and risk/review tasks |
| Are limits disclosed? | Synthetic fixtures, no connected model/scanners | Same, with workspace defaults isolated from current scope | Preserve these boundaries and make them visible in Agents/Workflow |

**Creation nuance:** the inspected assessment had one visible exact-label New assessment button at each tested viewport, not two simultaneously visible buttons in every layout. The source nevertheless assigns the same action to sidebar, mobile menu and page contexts; Dashboard/Assessments add their own creation action. The recommendation addresses redundant/inconsistent placement, not a fabricated universal duplicate count.

**Correction to the earlier V6.3 rationale:** fewer views did not by itself make the process easier to understand. Moving lifecycle orientation into collapsed disclosure removed a useful first-level explanation. The merge must preserve process orientation and reduce only unnecessary navigation and detail.

## 2. Additional primary UX guidance

Sources checked on 2026-11-02. These inform design decisions; they do not certify compliance or prescribe the exact CoreVAPT page count.

| Source | Relevant guidance | CoreVAPT inference |
| --- | --- | --- |
| [Microsoft HAX G1](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-what-the-system-can-do/) | Set expectations about the AI's supported tasks and scope | Agents explains one assistant's role/capabilities/limits before users rely on it |
| [Microsoft HAX G11](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/) | Make explanations available, while avoiding inflated trust | Workflow explains each proposal with source references, unknowns and the required human decision; explanatory prose is not proof |
| [Carbon progress indicator](https://www.carbondesignsystem.com/building-blocks/core/components/progress-indicator/guidelines) | Conventional progress indicators suit linear multistep tasks; conditional/reorderable processes need care | Use a lifecycle status overview with adaptive loops, not a forced six-step wizard or completion percentage |
| [Carbon modal guidance](https://www.carbondesignsystem.com/building-blocks/core/components/modal/guidelines) | Use focused interruptions sparingly; repeated work belongs on the page | Keep Workflow, conversation and the Findings register on-page; use overlays for bounded details/decisions |
| [Carbon UI shell source](https://github.com/carbon-design-system/carbon/blob/main/packages/react/src/components/UIShell/README.md) | Distinguishes navigation links and action components | Treat New assessment as a page action. Removing it from this sidebar is a CoreVAPT choice, not a universal Carbon prohibition |
| [GOV.UK task list](https://design-system.service.gov.uk/components/task-list/) | Simplify services before adding task navigation; its task-list pattern is not a forced sequence | Group by analyst tasks and make dependencies visible, without adding a workflow-template editor |

Existing accessibility/focus/reflow principles in [UX standards](UX_STANDARDS_AND_PAGE_MAP.md) still apply. A readable label and visible state are more useful here than adding animation, agent avatars or a larger menu.

## 3. Options and recommendation

| Option | Benefit | Problem | Decision |
| --- | --- | --- | --- |
| Add Agents/Dashboard to V6.2 and retain all six stage pages | Immediate stage visibility | Restores repeated switching between plan/run and analysis/review | Do not adopt wholesale |
| Keep V6.3 composition; restore visible lifecycle; make Workflow and one assistant explicit | Combines overview, process clarity and focused workspaces | Needs a real workflow-state presentation, not just a renamed tab | **Recommended** |
| Make Agents and a global workflow builder the center | Supports a future orchestration product | Adds runtime/team/template concepts outside the current one-assistant MVP | Defer |

Keep from V6.2: lifecycle clarity, full decision/attempt/evidence/risk information and source-linked explanations. Keep from V6.3: actionable Dashboard, compact attempt list, a unified Findings register, session-default separation and contextual details. Neither file is copied wholesale into the other.

## 4. Proposed information architecture

```text
Primary sidebar
  Dashboard
  Assessments
  Agents                 [one Assessment assistant]

Sidebar footer
  Settings               [drawer: Tools / New assessment defaults]

Assessment header
  Assessment identity + target + scope version
  Assigned assistant + current response mode
  Edit scope             [secondary action]
  New assessment         [one creation action in the page header]

Assessment working views
  Workflow | Findings | Report

Visible lifecycle overview
  Scope → Plan → Collect → Analyze → Review → Report
  Each phase has its own current state; adaptive investigation may loop back.
```

Dashboard/Assessments/Agents are stable destinations. The selected assessment is reached from Assessments, Dashboard attention or an activity link; it is not another permanent sidebar entry duplicating the header selector. Workflow belongs to that assessment, not to a separate global builder.

The lifecycle overview is visible without expanding a disclosure, including after switching to Findings or Report. It is an ordered status list, visually distinct from the three working-view navigation controls. It must not introduce a second competing tab bar. Its statuses may change after new evidence, request/scope revisions or recovery; no `4/6 complete` percentage or irreversible completion line is asserted.

Proposed label `Collect` includes both scan execution and recorded-result ingestion. Its cards retain separate modes and attempt/import identity. This is a UI phase name, not a replacement for execution/import contract enums.

## 5. One creation action, predictable placement

- Remove New assessment from desktop sidebar and mobile navigation drawer.
- Use the same label, **New assessment**, in the header of Dashboard, Assessments and an open assessment. The existing assessment header action is retained and made consistent across desktop/mobile.
- Opening it shows the same bounded creation form. Saving creates an empty draft and opens its Workflow; cancel preserves the current context.
- An empty-state illustration may explain how to create work, but should not add a second competing creation button when the header button is already visible. On an empty page, the single primary action may instead sit in the empty-state area.
- Agents uses **Open assessment** for its contextual link; it does not need an assistant-creation button or another New assessment launcher.

This is one creation control per page state, not a global floating action plus sidebar action plus header action.

## 6. Agents: one assistant, clearly described

The user confirmed one assessment assistant, not several specialist agents. `Agents` is a discoverable profile destination with one entry, **Assessment assistant**. Its explanation must distinguish logical product role from an enabled model or a running scanner.

| Section | Visible information | Boundary |
| --- | --- | --- |
| Role | Helps plan an authorized assessment, interpret supplied evidence and draft explanations/report content | Proposes; cannot grant permission, silently widen scope or establish exploit proof |
| Response mode | Demo/deterministic, connected LLM, or unavailable/error as appropriate | A connection failure is not a successful deterministic fallback |
| Provider/model | Exact enabled backend identity when known; otherwise **Not connected** | Do not copy a research shortlist into a claimed active configuration |
| Capabilities | Supported planning tasks and intended discovery/web/import capabilities; link to the full seven-tool matrix | Tool support/readiness remains distinct from assistant role and model availability |
| Limits | Effective action/runtime/model budgets when authoritative values exist; uncertainty/missing configuration disclosed | No invented remaining budget, cost, accuracy or confidence percentage |
| Assessment activity | Short assessment-bound references to proposals/decisions/outcomes, with **Open workflow** links | Reuse canonical message/action/attempt IDs; not a second audit-log subsystem |

In the current preview, display **Demo · deterministic**, **Model: Not connected** and **AI planning: In development**. One profile card does not establish one deployed model runtime. Do not fabricate a configured model, online status, successful reasoning evaluation or several specialist agents to fill the page.

The assessment header identifies this same assistant. **View assistant** opens a small profile summary without losing the current workflow; the complete Agents page is available from navigation. Do not show a selector with one usable option merely to imply configurability.

Keep authority legible:

| Actor/component | Responsibility |
| --- | --- |
| Human analyst | Defines authorization/scope, reviews proposals/findings and makes consequential decisions |
| Assessment assistant | Produces bounded explanations/proposals grounded in available evidence; exposes unknowns |
| Policy/worker/launcher | Independently checks authority and manages actual execution state/receipts |
| Nmap/ZAP/import adapters | Produce or ingest source observations; they are tools, not additional AI agents |

No new agent resource/API, permission system or runtime orchestration is implied. The page projects agreed capabilities/model configuration; executable schema decisions remain with G0 owners.

## 7. Workflow: visible cause, decision and next result

Rename the assessment view **Agent & runs → Workflow**, but do not stop at renaming. Keep a single visible lifecycle overview and one primary current-task panel. Show earlier decisions and full logs on demand; avoid six expanded stage forms plus another progress/navigation bar.

Each current-task panel answers:

1. **Where are we?** Phase, assessment target and concrete state.
2. **What did we observe?** Facts with source IDs and collection times; historical data marked.
3. **Why this next action?** A short, evidence-linked rationale and uncertainty.
4. **What does the analyst need to decide?** One task-specific primary action and its consequences.
5. **What happens afterward?** Expected artifact/result and the next dependency.

| Phase | Minimum visible content | Focused action / next result |
| --- | --- | --- |
| Scope | Authorized asset, ports/origin, ROE reference, exclusions/limits summary and scope version | Edit scope drawer; revision invalidates old proposals/grants |
| Plan | Request revision, assistant/source mode, selected profile, basis, rejected alternatives if relevant, unknowns | Explicit Generate plan or Review action; not automatic inference on page load |
| Collect | Exact action/approval/run or import identity, current attempt outcome and output availability | Separate start, cancel, inspect, reconcile or new retry proposal, as permitted |
| Analyze | Normalized candidates, source overlap and distinct endpoints; observations remain separate | Compare sources or inspect evidence; no automatic merge by title/CVE |
| Review | Priority factors, confidence/validation and analyst disposition | Open Findings review; acceptance does not confirm exploitation |
| Report | Pending review/coverage/approval limitations and frozen draft status | Open Report; PDF readiness and client-ready release remain separate |

Example after the HTTPS discovery fixture: **Plan · Waiting for approval → HTTP observation OBS-201 → proposed bounded baseline on the permitted origin → Review action → approval saved, then a separate run request → attempt outcome/artifact → compare sources**. The initial ZAP proposal has no earlier ZAP output.

A timeout/unknown is represented by its own attempt. Inspect/reconcile first; retry is a new action/approval. A successful replacement resolves the current issue across Dashboard/lifecycle/report readiness while retaining earlier failure in history/limitations. Replanning is a controlled return to Plan, not an automatic new scanner sequence.

Message append, explicit planning, action approval and execution start remain separate operations as specified by [G0 decisions](G0_CONTRACT_DECISIONS.md). Asking why a proposal exists must not by itself invalidate a still-valid approval. Sending a new request must not silently spend model budget or trigger a scan.

## 8. Page/detail responsibilities and configuration

| Surface | Keep on the page | Contextual detail |
| --- | --- | --- |
| Dashboard | Attention queue and assessment resume; small, defined current-state counts | Open an assessment-bound decision; avoid duplicating the same primary task in a large hero and queue |
| Workflow | Visible lifecycle, current task/plan, assistant conversation, compact attempts | Scope, exact-action approval, run logs, raw evidence, earlier decisions |
| Findings | Searchable ranked candidate register and source-comparison entry | Existing finding/risk/review drawer and evidence inspection; retain filters/selection/drafts on return |
| Report | Readiness and long-form executive/technical frozen report | Explicit draft acknowledgement/replacement and source inspection |
| Agents | Single assistant role/mode/model/capability/limit summary | Detailed tool status and assessment-linked activity |

Only one overlay is active. Evidence opened from a review replaces that overlay and offers Back, retaining draft rationale, selections and focus. A popup is suitable for one approval or infrequent edit; whole Workflow, repeated chat, a workflow editor and long report reading do not move into modals.

Settings remains a small drawer with **Tools** and **New assessment defaults**. Ports/rate/deadline seed new drafts only. Current authorization remains in Edit scope; exact proposed parameters remain read-only in approval. Provider/model credentials remain backend-owned; no browser key storage or invented connect success. The live handoff retains one authorized IPv4 asset, explicit TCP ports and origin-wide ZAP scope from [readiness/G0](READINESS_DECISION_REPORT.md).

No agent cloning/deletion, role marketplace, workflow-template catalogue, drag-and-drop graph, arbitrary CLI, custom prompt editor, team administration, scheduling or extra analytics destination is introduced.

## 9. Proposed scenarios and acceptance

These are future checks for an approved merge, not fresh passing tests.

| Scenario | User path | Required observable outcome |
| --- | --- | --- |
| M01 Create once | Dashboard/Assessments/assessment header → New assessment → cancel/save | Exactly one creation action in the current page state; none in sidebar/mobile menu; empty draft on save |
| M02 Understand the assistant | Agents → role/mode/model/limits → Open workflow | One assistant; Demo/Not connected shown truthfully; context preserved; no scan started |
| M03 Understand the process | Open an assessment at desktop/mobile | All six phase names/states discoverable without opening collapsed progress; current next task/why/basis/action/result visible |
| M04 Decision to output | Review baseline proposal → approve → separately request run → inspect artifact | Approval is not execution; action/approval/attempt/evidence chain is coherent |
| M05 Cross-tool review | Workflow → Findings → compare → review disposition | Same issue/location compatibility required; raw members and uncertainty survive link/rejection |
| M06 Recovery | Unknown/timeout → inspect/reconcile → new retry approval → success | No blind rescan; latest issue resolved consistently; historical failure retained |
| M07 Contextual inspection | Finding rationale → raw evidence → Back | One overlay, no lost draft/filter/selection; keyboard focus returns logically |
| M08 Defaults and scope | Change defaults → inspect existing assessment → create a new one → edit current scope | Defaults never mutate current authorization; scope revision stales previous grants |
| M09 Draft report | Review readiness → acknowledge limitations → freeze → later triage | Six required sections; no client-ready claim; old snapshot remains unchanged |

Before building, use these scenarios for a short prototype review with the user. After implementation, adapt the matching browser checks to the new navigation rather than reporting historical 17/22 groups as proof of the merge. Then ask representative analysts to explain the assistant's authority, current phase, next task, evidence basis and failure recovery without coaching. Record real observations; no percentage usability improvement or conformance claim is justified yet.

## 10. Bounded implementation handoff after approval

1. Preserve predecessor files. Remove sidebar/mobile creation launchers and standardize the current-page header action.
2. Restore an always-visible lifecycle overview; compose Workflow from the V6.3 workbench plus the V6.2 stage/decision detail. Preserve state semantics, not duplicate stage pages.
3. Add one Agents profile and the header binding/summary, with truthful mode/model/capability metadata.
4. Reuse Findings, report, scope, run and evidence components; keep repetitive work on-page and one overlay at a time.
5. Recheck current-attempt consistency, scope invalidation, form retention, source traceability, message/planning separation and mobile keyboard behavior.
6. Update active page/route handoff only when the implementation is accepted; keep G0/API ownership and platform evidence gates unchanged.

No HTML merge, backend, model call, scanner run, native capture or publication occurred during this research. Prototype hashes remain V6.2 `ab49f45427282523b99a22f25c45c6d2257d44a795da8343b2fbabf22e6d78d6` and V6.3 `11a63ffdcecfdf269f7a6c807d895768aab992dfb7c31506d395067426b6cf69`.
