# CoreVAPT 6.2 — local frontend verification

Execution date: **2026-11-02**, Asia/Bangkok. Artifact: [HTML 6.2](../../corevapt_frontend_v6.2.html). These are the frontend implementation session's recorded **UI-scenario** checks, not model/scanner/native-import/backend E2E. English translation preserved the reported results; the documentation audit did not independently rerun this suite. Hashes below identify the artifact at that session's final check and must be refreshed if the HTML changes.

## Observed results

**17 browser-check groups passed**, with no uncaught page errors or external HTTP(S) requests in the suite. The six steps were exercised at desktop **1440 px**, tablet **820 px**, and mobile **390 px**, without page-wide horizontal overflow in the inspected views.

Command actually recorded:

```bash
PLAYWRIGHT_MODULE=/home/longha/.cache/uv/archive-v0/ZQHepr5dJr1sjWGf/playwright/driver/package \
  node tests/prototype-v6.2.spec.cjs
```

Recorded environment: Node **v22.23.2**, cached Playwright **1.64.0-beta-1791568591000**, Chromium revision **1248**. No scanner/model or HTML runtime dependencies were installed. The script accepts `PLAYWRIGHT_MODULE` and `CHROMIUM_EXECUTABLE`; other machines need compatible Playwright/Chromium installations.

Final output: `RESULT 17 checks passed; zero page errors; zero external requests.` Formatted inline JavaScript was also parsed with Node `vm.Script`. Formatting used Prettier 3.6.2; V6.1 remained unchanged.

## Checked behavior

| # | Group | Recorded confirmation |
| --- | --- | --- |
| 1 | Lifecycle | Six navigable steps, one h1 per view. V6.1 failed this baseline with zero step buttons versus six expected |
| 2 | Approval → execution | Initial ZAP has no run/output; approval does not dispatch; separate simulation creates one successful attempt with linked observations |
| 3 | Conversation | Discovery-only request updates intent/revision, stales old action, and retains the labeled demo response |
| 4 | Timeout/retry | Timeout creates no successful ZAP evidence; failed run remains; retry creates a new Pending action with `retryOf` |
| 5 | Raw evidence | SHA-256 matches independent Node computation over exact fixture bytes; drawer discloses synthetic data; Escape closes it |
| 6 | Correlation/report | Link merges only the same endpoint and retains observations; false positive remains in appendix; live title/revision changes do not mutate snapshot |
| 7 | Assessment isolation | Empty draft has no findings/observations/runs; switching back restores the prior assessment's data |
| 8 | Policy negatives | Scope revision, denied action, excluded host, expiry, changed payload, and foreign evidence block execution |
| 9 | Risk context | High analyst impact plus reachable lab exposure moves a candidate to Review first, preserving source severity/validation |
| 10 | Failure/partial/async | Failure has no output; partial retains evidence/limitation; double start produces one run; switching assessments during execution does not leak results |
| 11 | Unknown/retry | Unknown requires reconciliation; retry needs new approval; an older failure cannot create another retry after a newer successful attempt |
| 12 | Cancellation | Requested → cancelled; old timer cannot later add successful evidence |
| 13 | Target/port revisions | Changed hostname/ports cannot reuse stale HTTPS basis; SSH-only discovery creates TCP 22 fixture; XPath resolves in its XML; no automatic web proposal |
| 14 | HTTP endpoint | Port 80 fixture uses raw `http://host` URI and normalized port 80; default HTTPS uses 443 |
| 15 | Snapshot replacement | Prepare new draft/Escape preserves prior snapshot; executive view hides per-finding technical detail and technical view restores it |
| 16 | Escaping/download/keyboard/mobile | HTML-like inputs create no img/script; download uses synthetic filename; focus trap/Escape, mobile system navigation, and Send work; focus remains in dialog after response |
| 17 | Responsive views | Six steps at 1440/820/390 show no overflow; action dialog focus/Escape works; browser screenshots captured |

Groups contain multiple assertions. **17 is a group count**, not completed runtime requirements, working integrations, or AI accuracy. Tests use browser evaluation for state/negative guards/checksums alongside real form/button interactions. UI-only enforcement is not proven secure against a malicious client.

## Sample PDF and screenshots

- [Desktop Plan, 1440 px](screenshots/v6.2-plan-1440.png).
- [Tablet Plan, 820 px](screenshots/v6.2-plan-820.png).
- [Mobile Plan, 390 px](screenshots/v6.2-plan-390.png).
- [Sample draft from Chromium printing](screenshots/v6.2-sample-report.pdf): **four A4 pages** in the recorded run, with print margins and navigation/skip link omitted.

The frontend session used `pdfinfo`/`pdftotext` to check sections **7.1–7.6**, the false-positive appendix, human decisions, original source severity/confidence, raw references, and SHA-256. It inspected rendered first/last pages while fixing a printed skip-link issue, then regenerated the PDF with print CSS/A4 margins. This is sample browser printing, not server PDF generation or production pagination acceptance.

## Independent review and fixes

The frontend session used `requesting-code-review` for two read-only review rounds, without backend changes. Reproduced issues were addressed: evidence target/service port no longer in scope, missing seeded discovery-approval provenance, executive-view detail reduction, focus after approval/mobile Send, hard-coded Nmap 443 locator with port 22 fixtures, and incorrect ZAP raw scheme with HTTP 80. The main implementation agent added old-attempt retry prevention, explicit snapshot replacement, and print CSS. Corresponding paths have the browser regression checks above.

## Artifact integrity at the recorded check

- `corevapt_frontend_v6.1.html`: SHA-256 **`6b65e63d5de0eb1cbbf685b18c42fc51488cbe1758b1809ddd3361f79874b9c7`**, matching the prework checksum; predecessor preserved.
- `corevapt_frontend_v6.2.html`: SHA-256 **`ab49f45427282523b99a22f25c45c6d2257d44a795da8343b2fbabf22e6d78d6`** at that session's final verification.
- Root `1.pdf` and `sources/statement-1.pdf`: identical SHA-256 **`cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`**.

No Git repository existed at the session's start; no commit/worktree or website publication was created.

## Unproven capabilities

No AI inference, scanner execution, supported native parsing, authenticated actor, durable audit/state, worker/network enforcement, calibrated confidence, risk-accuracy benchmark, or server PDF was demonstrated. The three intended tools remain Planned; four others remain Unsupported. Conversation uses fixed demo intents rather than general request understanding. Unknown data is not zero. Reload loses browser state/snapshots. Live handoff: [frontend plan](../superpowers/plans/2026-11-02-01-frontend-handoff.md) and [R01–R15](REQUIREMENTS_MATRIX.md).
