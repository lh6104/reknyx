# CoreVAPT V6.4 — approved merge verification

Date: **2026-11-02**, Asia/Bangkok. Artifact: [standalone V6.4](../../corevapt_frontend_v6.4.html). Basis: user-approved [V6.2/V6.3 merge](FRONTEND_V6_2_V6_3_MERGE_RESEARCH.md), [current UX/page map](UX_STANDARDS_AND_PAGE_MAP.md) and [implementation plan](../superpowers/plans/2026-11-02-frontend-v6-4.md). Scope: local frontend preview; no backend/model/scanner/native-import execution.

## Delivered behavior

- Stable Dashboard/Assessments/Agents navigation with footer Settings. One header New assessment control in Dashboard/Assessments/open assessment, including an empty Dashboard; none in sidebar/mobile menu. Agents uses contextual Open workflow.
- Workflow/Findings/Report preserve an always-visible, read-only Scope/Plan/Collect/Analyze/Review/Report lifecycle. The current task shows phase, reason, evidence basis, human decision and expected result. A fresh retry proposal returns to Plan before the older failure can obscure it.
- One Assessment assistant profile, also bound in the assessment header with a summary dialog: Demo/deterministic, Model Not connected, Provider Not configured, AI planning In development. Capabilities, limits and selected-assessment activity stay explicit. No new runtime agent service or model selector.
- Clarifications preserve request revisions and grants. Edit request, Generate plan, approval and start are separate. Explanations capture the task/request/scope/basis at send time and remain bound to the original assessment during a switch.
- Existing source/attempt/review/snapshot detail is retained. Mobile assistant access sits inline in the current task, keeping scope/approval buttons unobstructed.

## Actual checks

**27 browser check groups passed**, **zero uncaught page errors**, **zero external HTTP(S) requests** in the final suite, exit **0**. Working views and relevant dialogs were checked at **1440, 820 and 390 CSS px** without horizontal page overflow. Separate Dashboard/Workflow/Agents screenshot capture ran at 1440/390; Agents had no overflow at either width. Counts are groups of UI assertions, not passed platform requirements or integrations.

Final command on this machine:

```bash
PLAYWRIGHT_MODULE=/home/longha/.cache/uv/archive-v0/ZQHepr5dJr1sjWGf/playwright/driver/package \
  node tests/prototype-v6.4.spec.cjs
```

[Preserved suite output](sources/frontend-v6.4-browser-2026-11-02.log). Portable invocation is `node tests/prototype-v6.4.spec.cjs` with a compatible installed Playwright/Chromium; use `PLAYWRIGHT_MODULE` or optional `CHROMIUM_EXECUTABLE` for a nonstandard installation. The cache path above records this run, not a setup requirement.

Environment: Node **v22.23.2**, cached Playwright **1.64.0-beta-1791568591000**, Chromium revision **1248**. Prettier **3.6.2** formatted only the new HTML/test. Node `vm.Script` parsed the final inline JavaScript. No application framework, package/lockfile or runtime dependency was added. Some guard cases use browser state evaluation alongside real clicks/forms; these checks do not prove resistance to a malicious client.

| Group | Passing scenario |
| --- | --- |
| 1 | dashboard is the entry point and primary navigation has three stable pages |
| 2 | approval does not dispatch; success creates traceable ZAP output |
| 3 | clarifications preserve approval while explicit request edits invalidate it |
| 4 | next-step explanation follows the current request and keeps its assessment context |
| 5 | timeout retains failed attempt and retry needs fresh approval |
| 6 | evidence raw bytes have a real fixture checksum; no scanner provenance claim |
| 7 | correlation keeps provenance; false positives stay in frozen report |
| 8 | new draft starts empty and switching assessments preserves isolation |
| 9 | scope revisions, denied and expired actions never dispatch |
| 10 | risk context changes review order without changing source severity or validation |
| 11 | failed and partial runs retain limitations; async results stay with their assessment |
| 12 | unknown outcomes require reconciliation and retry cannot repeat a successful replacement |
| 13 | cancel confirms a terminal state and produces no successful evidence |
| 14 | target and port changes require current service evidence for web planning |
| 15 | HTTP port80 fixture preserves the bound endpoint scheme |
| 16 | new report draft retains the previous snapshot until explicit replacement |
| 17 | text escaping, local downloads, focus trap and mobile navigation |
| 18 | background simulation updates retain an unsaved scope form |
| 19 | successful retry resolves dashboard issue count while retaining failed history |
| 20 | dashboard attention deep link preserves assessment context and recomputes after approval |
| 21 | workspace defaults affect new drafts only and invalid values preserve existing state |
| 22 | evidence replaces the finding drawer and Back retains review rationale |
| 23 | one header creation action and no sidebar or mobile-menu duplication |
| 24 | one assistant profile shows truthful model and assessment activity |
| 25 | visible lifecycle and assistant binding remain across all assessment views |
| 26 | workflow current task moves from approval to collection and human review |
| 27 | desktop/tablet/mobile keep all working views and single-overlay keyboard focus |

## Reproduced defects and review

The three-destination baseline assertion was first run against preserved V6.3 and failed (2 destinations versus the required 3). Targeted regressions then reproduced and fixed:

- Independent read-only review found that Why this next step could explain a generic web action after the request became discovery-only. The response now uses the captured current task/basis; the regression also switches assessment before the asynchronous response completes.
- A pending retry was hidden by the older timeout, leaving the lifecycle on Collect instead of Plan. The phase/task projection now prioritizes the fresh valid proposal; approval still does not start an attempt.
- Visual inspection found the mobile floating assistant trigger could cover View scope. Its regression failed before moving access inside the task; the targeted keyboard/mobile test and final full suite passed afterward.

The independent review supplied the first actionable finding. Its follow-up could not finish because the review service reached its usage limit; a final independent pass is **not claimed**. The primary agent checked the fixes, all 27 groups and the rendered artifacts. Human analyst evaluation and a full accessibility/assistive-technology audit remain **not_run**.

## Rendered evidence

- [Dashboard desktop](screenshots/v6.4-dashboard-1440.png) and [mobile](screenshots/v6.4-dashboard-390.png).
- [Workflow desktop](screenshots/v6.4-workflow-1440.png), [mobile](screenshots/v6.4-workflow-390.png) and [tablet](screenshots/v6.4-plan-820.png).
- [Agents desktop](screenshots/v6.4-agents-1440.png) and [mobile](screenshots/v6.4-agents-390.png).
- [Synthetic sample report](screenshots/v6.4-sample-report.pdf): **4 A4 pages**, sections **7.1–7.6** and synthetic/Not client-ready labels confirmed with `pdfinfo`/`pdftotext`. Screen-only skip/navigation text was absent. Browser print is separate from future server PDF delivery.

Desktop Dashboard/Workflow/Agents and the corrected mobile Workflow were visually inspected. These artifacts support a targeted layout review, not a usability improvement percentage or standards-conformance claim. Screenshot files named `v6.4-plan-*` come from the inherited harness and show the Workflow view.

## Integrity and remaining boundaries

SHA-256 after final formatting and checks:

| Artifact | SHA-256 |
| --- | --- |
| `1.pdf` | `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc` |
| `corevapt_frontend_v6.1.html` | `6b65e63d5de0eb1cbbf685b18c42fc51488cbe1758b1809ddd3361f79874b9c7` |
| `corevapt_frontend_v6.2.html` | `ab49f45427282523b99a22f25c45c6d2257d44a795da8343b2fbabf22e6d78d6` |
| `corevapt_frontend_v6.3.html` | `11a63ffdcecfdf269f7a6c807d895768aab992dfb7c31506d395067426b6cf69` |
| `corevapt_frontend_v6.4.html` | `219ca3629951c426bc452ad3eecd1495f9f29e15f957a1b5519562a8cde3a178` |
| `tests/prototype-v6.4.spec.cjs` | `79ce86a3ffebc299d5c422f88be4eb524351df4643fc888ff2bbb3c890875dee` |
| `docs/research/screenshots/v6.4-sample-report.pdf` | `29272a8d1690d278fd0ae0bbddf32d949e00acb153090746372756ef117d4fdc` |

The PDF source and all three predecessor HTML hashes match the inspected baseline. V6.2/V6.3 historical verification and test files were preserved. Active README, research index, page map, requirement mapping, frontend handoff, platform design and master-plan references now describe V6.4; this does not complete their backend tasks.

Documentation check: **42 Markdown documents**, **338 relative links**, **0 missing targets** across root README/AGENTS and project docs. Document titles and code fences passed; changed document identities, English copy and current/historical references were inspected.

| Area | Result / boundary |
| --- | --- |
| V6.4 UI scenarios, inline-script syntax and sample print | **pass**, at the local preview level described above |
| Authenticated API, durable state/audit, worker, enforcement and private artifacts | **not_run**; absent from this standalone deliverable |
| Actual model planning/evaluation, scanner runs and native import adapters | **not_run**; not connected, no external execution performed |
| Server PDF, client-ready assessment release and operational pilot | **not_run**; browser sample does not establish these capabilities |
| Human usability, full WCAG/accessibility audit | **not_run**; targeted reflow/focus checks only |

The prototype still uses synthetic evidence, timed run simulations, deterministic replies and tab-local state/defaults that reset on reload. Three intended integrations remain Planned/In development and four Unsupported. There is no silent live-to-mock fallback. No Git repository, backend service, paid API call, scanner execution, native capture, commit, publication or deployment was created by this task. G0–G4, provider evaluation and organizer validation/permission gates remain unchanged.
