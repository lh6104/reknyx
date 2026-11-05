# Reknyx frontend

A Next.js + Tailwind CSS implementation of [the supplied V7.4 HTML](../reknyx_frontend_v7_4.html). The source's Manrope typography, lime-and-gray palette, sidebar, dashboard, and assessment flows are preserved in React components. This is an explicit **synthetic preview**, with no backend, scanner, model, or live API integration.

## Run locally

Requires Node.js 20.9 or later and npm. Verified with Node 22.23.2 and npm 10.9.8.

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**. The server binds to loopback. To use another port: `npm run dev -- --port 3001`.

For the production build:

```bash
npm run build
npm run start
```

## Stack and structure

| Dependency | Pinned version |
| --- | --- |
| Next.js / App Router | 16.4.5 |
| React / React DOM | 19.3.1 |
| Tailwind CSS / PostCSS plugin | 4.3.4 |
| TypeScript | 5.9.3 |
| Manrope / Fontsource | 5.3.0 |
| Lucide React | 1.68.0 |
| Playwright | 1.64.1 |

Versions were checked against npm; setup follows the official [Next.js installation](https://nextjs.org/docs/app/getting-started/installation) and [Tailwind Next.js guide](https://tailwindcss.com/docs/installation/framework-guides/nextjs). The npm lockfile pins transitive dependencies. Fonts are served locally; there is no Google Fonts runtime request.

```text
src/app/                   App Router routes, metadata, global tokens and print styles
src/components/            Shell, views, accessible dialogs, frozen report rendering
src/lib/types.ts           Frontend preview types; not generated backend contracts
src/lib/fixtures.ts        Two synthetic assessments, four findings, seven-tool inventory
src/lib/model.ts           Pure validation, proposal, decision, retry and snapshot helpers
src/lib/preview-context.tsx Shared memory state and non-sensitive preference storage
tests/model.test.ts        Domain behavior and regression checks
tests/frontend.spec.ts     Browser workflow, keyboard, layout and request checks
```

## Routes and preview behavior

| Route | Implemented behavior |
| --- | --- |
| `/` | Dashboard with derived findings, source counts, decisions, run issues and activity |
| `/dashboard` | Redirect to `/` |
| `/assessments` | Search assessments and create a validated empty draft |
| `/assessments/:id/scope` | Recorded exact IPv4 /32 asset, TCP ports, limits and permission context |
| `/assessments/:id/plan` | Request, proposals, synthetic history, separate decisions and file attachments |
| `/assessments/:id/findings` | Filtered register, source tracing, confidence and analyst disposition |
| `/assessments/:id/report` | Readiness, frozen draft creation, sample preview and printing |
| `/assessments/:id/audit` | Synthetic history and timestamped session events |
| `/approvals` | Pending proposals and a separate failed-attempt register |
| `/findings` | Cross-assessment candidate register and evidence details |
| `/reports` | Assessment report workspaces and frozen session snapshots |
| `/settings` | Analyst, report options, theme, bounded defaults and truthful integration inventory |

The sidebar follows the user-selected V7.4 HTML, superseding the historical V6.4 navigation inventory for this deliverable. The six lifecycle meanings remain visible within assessments.

- All routes show **Synthetic preview**. New assessments, messages, attachments, decisions, and reports reset on reload. Only preferences persist under `reknyx.preview.preferences.v1`. Storage failures remain visible.
- `/` opens two source scenarios: customer portal findings with an unsupported active-validation proposal, and a staging API discovery timeout. All Done/Failed history and observations are fixtures.
- New drafts have **no actions or findings**. Generate preview proposal adds Pending discovery. Approval records **Approved**, never Done. Starting a scanner remains disabled.
- The assistant uses fixed rules and an explicit assessment context. Sending a message, generating a proposal, recording approval, and execution are separate operations. Foreign targets, unsupported protocols, ambiguous numeric parameters, and duplicate work are rejected conservatively. This helper is not a security enforcement boundary or a general natural-language parser.
- A retry creates a fresh proposal and keeps the failed attempt. It respects tool preferences and refuses equivalent existing work.
- Attach synthetic files up to **1 MiB**. Bytes are read locally for a SHA-256 digest; the first 16 KiB display as escaped text. Nothing is uploaded or natively parsed, and no finding is generated. Reload clears attachments.
- Candidate ordering uses source severity. CVSS and calibrated confidence probabilities remain unknown. Analyst acceptance does not confirm a suspected issue.
- All seven integrations show **In development**, with intended modes separately identified. Enabling a preview preference does not connect an integration. Nikto remains a conditional import roadmap item.
- Draft reports copy the assessment and report preferences. Later changes do not alter the snapshot. The sample contains PDF sections 7.1–7.6 and explicit uncertainties, failures, provenance, and decision history. **Save sample PDF** opens the browser print dialog. Final backend PDF generation is disabled.

Do not enter real credentials, sensitive evidence, or production data. There is no authentication or durable assessment storage in this preview.

## Checks

```bash
npm test
npm run typecheck
npm run build
npm run test:e2e
```

The browser suite starts the production server on loopback port **3100**, so build first. Use an unused port 3100. On first setup, if a compatible Chromium is missing:

```bash
npx playwright install chromium
```

`CHROMIUM_EXECUTABLE` may select an existing compatible browser. For an explicit development-server check use `E2E_SERVER_MODE=dev npm run test:e2e`. The default checks use the production build. Playwright creates `test-results/` and `playwright-report/`, including desktop/mobile screenshots, traces for failures, and a synthetic sample PDF. These directories are ignored.

Manual walkthrough: create a draft; generate a proposal; record an approval and observe unavailable execution. On Customer portal review, inspect the three source memberships for F-01, decline unsupported validation with a rationale, create a sample report, then review a finding and reopen the original snapshot. Also try the assistant's outside-scope suggestion, a staging API retry, the `/` search shortcut, mobile navigation, and Escape to close dialogs.

Actual results and retained screenshots are in the [verification record](../docs/implementation/reknyx-frontend-verification.md). The historical F01–F15 API/DB cases, G0 schemas, real scanner/model evaluation, and platform acceptance are **not passed by these UI tests**.

The original HTML SHA-256 is `9e6d7bfe6c203eb557398b3be42ded175258f84077e36aab8b939c258d8be48b`; it is unchanged. The requirements PDF baseline remains `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`. See the [design](../docs/superpowers/specs/2026-11-05-reknyx-frontend-design.md) and [implementation plan](../docs/superpowers/plans/2026-11-05-reknyx-frontend.md).
