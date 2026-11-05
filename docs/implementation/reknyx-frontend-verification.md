# Reknyx frontend verification

Deliverable: local Next.js + Tailwind frontend derived from `reknyx_frontend_v7_4.html`, verified on 2026-11-05 local time. Evidence level: **synthetic frontend preview**. This record does not establish backend, scanner, model, or operational readiness.

## Delivered scope

The new `frontend/` application provides Dashboard, Assessments, Approvals, Findings, Reports, Settings, assessment scope/plan/findings/report/audit views, and a contextual deterministic assistant. It preserves the supplied visual direction, serves Manrope locally, and uses responsive Tailwind layouts, native dialogs with keyboard focus handling, and real App Router URLs.

The user-selected V7.4 HTML takes precedence over the historical V6.4 page inventory for this conversion. Source risk heuristics were replaced with source-severity ordering and unknown CVSS. Approval no longer implies completed execution. File attachment no longer claims native parsing. Report snapshots retain frozen evidence and preferences. Research documents keep their historical names and dates; current branding and run instructions use Reknyx.

## Environment and checks

Node.js **22.23.2**, npm **10.9.8**, Linux, Next.js **16.4.5**, React **19.3.1**, Tailwind CSS **4.3.4**, TypeScript **5.9.3**, Playwright **1.64.1**, installed compatible Chromium. Browser checks use a production Next.js server on `127.0.0.1:3100`. Viewports: **1440 × 1100** and **390 × 844**.

| Command actually run | Working directory | Final outcome |
| --- | --- | --- |
| `npm install --no-fund` | `frontend/` | Pass; lockfile created, npm reported 0 vulnerabilities |
| `npm test` | `frontend/` | **13/13 pass**, 0 fail, 0 skipped |
| `npm run typecheck` | `frontend/` | Pass, exit 0 |
| `npm run build` | `frontend/` | Pass, exit 0; static pages and dynamic assessment route generated |
| `npm run test:e2e` | `frontend/` | **19/19 pass**, 0 fail, 0 skipped; 15.1 seconds for final run |
| `sha256sum 1.pdf reknyx_frontend_v7_4.html` | Project root | Pass; original hashes unchanged |
| `pdfinfo` and `pdftotext -layout` on the retained sample PDF | Project root | Pass; seven A4 pages, all six report sections and synthetic notice present, sidebar copy absent |

The initial dashboard check failed before implementation. Regression tests reproduced unsupported port/protocol requests, duplicate retry proposals, and retries ignoring disabled-tool preferences; the corrected cases passed. Native dialog tab order initially passed through the document body; explicit wrapping now keeps focus inside the dialog. Other early browser failures were scoped-selector/hydration timing issues in the test harness and were corrected without weakening the asserted product behavior. The final table reports the integrated result, not those earlier failures.

The independent reviewer found no critical issues. Three important findings were corrected and re-reviewed: conservative handling of unsupported request parameters, equivalent-work suppression on retries, and retry preference enforcement. No material issue remained in the scoped re-review. Playwright emitted environment `NO_COLOR`/`FORCE_COLOR` warnings; they did not fail checks.

## Browser cases

These are local preview checks, not the historical API/DB acceptance cases F01–F15.

1. Dashboard exposes fixture provenance and separate pending/failure counts.
2. Source destinations and assessment URLs render after direct navigation/refresh.
3. Creation rejects invalid IPv4 octets and fractional ports, then creates no actions or findings.
4. Approval records Approved, keeps execution unavailable, and creates no findings.
5. Assessment messages remain isolated; generation is explicit and duplicate proposals are suppressed.
6. A request for another assessment's target is rejected and audited.
7. Unsupported active validation cannot be approved; it can be declined with a rationale.
8. Retry preserves the failed attempt and creates a distinct Pending proposal.
9. Retry respects disabled preview tools.
10. Finding review preserves evidence and does not confirm a suspected banner; filtering works.
11. Local synthetic file attachment yields a SHA-256 record and escaped scanner text, with no native parsing or findings.
12. A report contains sections 7.1–7.6, supports print layout, and remains unchanged after later finding review.
13. Search, the `/` shortcut, and notifications enter the correct context.
14. Tab remains inside dialogs; Escape closes and restores opener focus.
15. Preferences persist while existing assessment scope remains unchanged.
16. Storage failure remains visible and session preferences continue to apply.
17. Desktop/mobile layouts fit their viewports; mobile navigation, finding dialogs, and all primary mobile pages remain usable.
18. Unknown routes and reload of an ephemeral draft explain recovery.
19. The exercised preview workflow makes no external, scanner, provider, or `/api/` requests and records no browser page errors.

Model tests independently cover invalid/required scope, empty drafts, foreign/mixed targets, duplicate proposals, observed web-service prerequisites, unsupported numeric/protocol syntax, approval/execution separation, unsupported active approval, failure-preserving retries, retry deduplication, snapshot immutability, and correctly scoped aggregate views.

## Retained evidence

- [Desktop dashboard](evidence/reknyx-frontend/reknyx-dashboard-desktop.png), visually inspected.
- [Mobile dashboard](evidence/reknyx-frontend/reknyx-dashboard-mobile.png), visually inspected.
- [Synthetic sample PDF](evidence/reknyx-frontend/reknyx-synthetic-sample.pdf), produced through Chromium print emulation; **not** a backend-generated or client-ready report.
- [Machine-readable verification and source/artifact hashes](evidence/reknyx-frontend/verification.json).
- Executable cases: [domain tests](../../frontend/tests/model.test.ts) and [browser tests](../../frontend/tests/frontend.spec.ts).

The exact frontend file manifest and source bundle SHA-256 are in the JSON record. The original source hashes are:

| Original | SHA-256 |
| --- | --- |
| `1.pdf` | `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc` |
| `reknyx_frontend_v7_4.html` | `9e6d7bfe6c203eb557398b3be42ded175258f84077e36aab8b939c258d8be48b` |

## Remaining dependencies and limits

| Check | Status / missing prerequisite |
| --- | --- |
| G0 executable schemas and HTTP integration | **Not run**; no frozen executable API contract or backend provided |
| F01–F15 against authenticated API, PostgreSQL, worker | **Not run**; only memory-based preview state exists |
| Native parsing and authorized scanner execution | **Not run**; no parser/launcher/scanner integration assigned or enabled |
| Real provider/model evaluation | **Not run**; no model configured or called; deterministic rules only |
| Backend PDF release and pilot acceptance | **Not run**; browser sample printing only, no report service/release gate |
| Other browsers and assistive technology audit | **Not run**; Chromium keyboard/layout scenarios are not a full accessibility certification |
| Deployment/publication | **Not run**; local frontend deliverable only |

Assessment data, attachments, decisions, conversations, and snapshots are session-memory projections and reset on reload. Only non-sensitive preferences persist locally. There is no authentication, durable evidence storage, or live scope enforcement. All integrations remain **In development**. The original HTML and PDF remain unchanged; no Git repository was initialized, no commit was made, and nothing was published.

See [frontend instructions](../../frontend/README.md), [design](../superpowers/specs/2026-11-05-reknyx-frontend-design.md), and [plan](../superpowers/plans/2026-11-05-reknyx-frontend.md).
