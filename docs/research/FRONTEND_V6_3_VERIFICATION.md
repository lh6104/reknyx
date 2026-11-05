# CoreVAPT V6.3 — dashboard and simple-workspace verification

Date: **2026-11-02**, Asia/Bangkok. Artifact: [V6.3 standalone HTML](../../corevapt_frontend_v6.3.html). Specification: [UX standards, page map, settings and S01–S07 scenarios](UX_STANDARDS_AND_PAGE_MAP.md). Scope: local frontend scenarios, not backend/model/scanner/native-import execution.

## Observed result

**22 browser check groups passed**, with **zero uncaught page errors** and **zero external HTTP(S) requests** during the suite. Workspace views and contextual dialogs were checked at **1440, 820 and 390 px** without horizontal page overflow. Dashboard screenshots at 1440/390 also showed no overflow. These are targeted checks, not a full accessibility conformance audit or a human usability study.

Actual command:

```bash
PLAYWRIGHT_MODULE=/home/longha/.cache/uv/archive-v0/ZQHepr5dJr1sjWGf/playwright/driver/package \
  node tests/prototype-v6.3.spec.cjs
```

Environment: Node v22.23.2; cached Playwright 1.64.0-beta-1791568591000; Chromium revision 1248. `PLAYWRIGHT_MODULE`/`CHROMIUM_EXECUTABLE` may point to compatible installations on another machine. HTML itself needs no server/build/runtime dependency. Prettier 3.6.2 formatted the new HTML/test files. Node `vm.Script` parsed the final inline script successfully.

Final suite output: `RESULT 22 checks passed; zero page errors; zero external requests.` The dashboard entry-point check was first run against preserved V6.2 and failed because its initial view was the plan rather than Dashboard. The new background-form regression was reproduced as a lost hostname before its fix and passed afterward.

## Checked behavior

| Group | Observed verification |
| --- | --- |
| 1 | Dashboard entry point; two permanent navigation pages; three assessment views; six lifecycle statuses retained without a six-button page selector |
| 2 | Approval creates no run; an explicit simulation creates exactly one attempt with linked output |
| 3 | Conversation request revision and discovery-only routing invalidate older proposals |
| 4 | Timeout produces no successful web evidence; retry is a fresh proposal with retryOf |
| 5 | Exact raw-fixture SHA-256 verified independently with Node; synthetic label and keyboard dismissal |
| 6 | Source linking preserves observations; false positives remain in the report appendix; later live-state changes do not change a frozen snapshot |
| 7 | New assessment starts empty; switching assessments preserves isolation |
| 8 | Scope revision, denial, excluded host, expiry, changed payload and foreign evidence block dispatch |
| 9 | Analyst risk context changes review order without changing source severity or technical validation |
| 10 | Failed/partial outcomes preserve appropriate evidence/limitations; duplicate start produces one run; async results remain assessment-bound |
| 11 | Unknown execution requires reconciliation; retry needs fresh approval; an old failed attempt cannot trigger another retry after a newer successful attempt |
| 12 | Cancellation is requested then confirmed; old timers do not produce successful output afterward |
| 13 | Target/port edits cannot reuse an out-of-scope HTTP basis; SSH-only discovery stays non-web; raw XPath resolves to its actual port |
| 14 | Bound HTTP port 80 produces HTTP raw URLs and normalized port 80 |
| 15 | Draft replacement is explicit; Escape preserves the old snapshot; executive screen hides per-finding details and technical view restores them |
| 16 | Untrusted HTML-like text remains text; synthetic download filename; focus trap/Escape; mobile navigation, message submission/clearing, and no duplicate empty resubmission |
| 17 | A scope hostname being edited survives a background terminal run transition while canonical scope stays unchanged |
| 18 | Timeout → successful retry resolves Dashboard issues, lifecycle Run status and report-readiness gate consistently; failed history remains |
| 19 | Dashboard action deep link opens the right assessment and recomputes approval counts after a decision |
| 20 | Workspace defaults do not change existing assessment/grants; invalid values retain input and preserve saved defaults; new drafts inherit copied ports/rate/deadline |
| 21 | Raw evidence replaces rather than stacks the finding drawer; Back restores the review rationale |
| 22 | All working views reflow at 1440/820/390; Tools/defaults is reachable at each width; dialog focus/Escape and screenshots |

The count is test groups, not scanner integrations, individual assertions, model accuracy or passed platform requirements. Some guards/state assertions use browser evaluation alongside real button/form interactions. These tests do not establish malicious-client resistance.

## Review findings and fixes

Independent read-only review used `requesting-code-review`. Findings addressed:

- Background `renderOverlay()` discarded unsaved scope/default/new/reconciliation form values. Background rerenders now retain editable fields, disclosure and scroll state; explicit actions regenerate from their new state.
- Historical timeout caused lifecycle/report readiness to disagree with the dashboard after successful retry. Shared latest-attempt selectors now determine current unresolved outcomes; old failures remain in limitations.
- Generic form retention preserved sent text in the mobile agent composer. Explicit Send now clears both composer instances before rerender; the test checks empty resubmission does not increment request revision.
- Tablet navigation could hide Tools/defaults between desktop and phone breakpoints. Its labelled sidebar icon remains reachable at tablet widths.

Review inspected task links, defaults isolation, single-overlay Back behavior and reflow. It did not audit a live backend or certify WCAG compliance.

## Screenshots and sample report

- [Dashboard desktop 1440](screenshots/v6.3-dashboard-1440.png).
- [Dashboard mobile 390](screenshots/v6.3-dashboard-390.png).
- [Workspace desktop 1440](screenshots/v6.3-workspace-1440.png).
- [Workspace mobile 390](screenshots/v6.3-workspace-390.png).
- [Workspace tablet 820](screenshots/v6.3-plan-820.png).
- [Synthetic sample PDF](screenshots/v6.3-sample-report.pdf): **4 A4 pages** in the recorded run, with printed sections **7.1–7.6** verified using `pdfinfo` and `pdftotext`.

Desktop/mobile dashboard and desktop workspace screenshots were visually inspected. The dashboard prioritizes an actual next decision rather than a marketing block. Only the current attention queue is filtered; no fabricated trend/overall-risk chart is shown. The PDF is browser print, not server rendering/download integration. Screen-only navigation and skip link are omitted from print.

## Integrity and handoff

SHA-256 at verification:

| Artifact | SHA-256 |
| --- | --- |
| V6.1, unchanged | `6b65e63d5de0eb1cbbf685b18c42fc51488cbe1758b1809ddd3361f79874b9c7` |
| V6.2, unchanged | `ab49f45427282523b99a22f25c45c6d2257d44a795da8343b2fbabf22e6d78d6` |
| V6.3 | `11a63ffdcecfdf269f7a6c807d895768aab992dfb7c31506d395067426b6cf69` |

Final relative Markdown link-target check: **269 links**, **0 missing targets** across root README and project docs. README, research index, active frontend handoff, platform design and requirements matrix point to the new page model. Historical V6.2 verification remains unchanged. No Git repository, backend service, scanner, provider credential or deployment was created for this work.

Remaining limits: deterministic agent replies; synthetic evidence/run timers; tab-local state/defaults; no genuine supported native import, live scanner, authenticated approval, durable audit, private artifact service or server PDF. Three intended tools remain Planned; four remain Unsupported. Dashboard current counts do not establish a security posture or confirmed exploit count. Human usability testing and full assistive-technology/accessibility evaluation remain future validation.
