# Reknyx Frontend

The application has explicit **preview** and **api** modes with React, TypeScript and Tailwind CSS. Preview uses synthetic in-memory state. API mode connects authenticated assessments, messages, source imports, finding review and immutable backend PDF reports. AI providers and scanner execution remain in development. Dependencies are pinned in `package.json` and `package-lock.json`; fonts are served locally.

## Run

Requires Node.js 20.9 or later and npm. From this directory:

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. The server binds to loopback. For production preview:

```bash
npm run build
npm run start
```

For API mode, start the backend and worker as described in [backend setup](../backend/README.md), configure its allowed frontend origin, and use one loopback hostname consistently:

```bash
NEXT_PUBLIC_REKNYX_MODE=api REKNYX_BACKEND_ORIGIN=http://127.0.0.1:8000 npm run dev
```

Production builds require those same mode/origin values during both build and startup. Missing or invalid configuration fails; connection failures remain errors. The backend receives same-origin `/api/v1` requests through a fixed server rewrite. Session cookies are HttpOnly; CSRF and pending replay keys remain in memory, with no credential/evidence browser storage. Messages do not invoke inference. The API screens display server capabilities and keep provider/scanner actions disabled.

## What is available

Dashboard, assessments/scope, contextual deterministic assistant, plan/approval review, findings/evidence, reports and settings have working local preview flows. Every route labels synthetic data. Messages, approval, proposal generation and execution remain separate. Local attachments are hashed and displayed as escaped text; they are not natively parsed or uploaded. Frozen report samples support browser printing, not backend PDF generation.

Assessment data, attachments, conversations, decisions and report samples reset on reload. Only bounded non-sensitive preferences persist under `reknyx.preview.preferences.v1`. Recording a permission reference or enabling a tool preference grants no authorization. Do not enter credentials or private production evidence.

## Routes and code

Pages are under `src/app/`, reusable screens/dialogs under `src/components/`, and preview types/fixtures/rules/context under `src/lib/`. Existing routes include `/`, `/assessments`, assessment `scope|plan|findings|report|audit` views, `/approvals`, `/findings`, `/reports` and `/settings`; `/dashboard` redirects to `/`.

API transport/runtime validation is under `src/api/`; the authenticated API workspace uses the existing routes, typography, navigation and card styles. Existing preview components and state remain separate. Types consume `contracts/generated/api.d.ts`; runtime schemas are generated from the same OpenAPI source with `npm run generate:api`. Check freshness with `node scripts/generate-api.mjs --check`. API mode loads authorized server collections with bounded pagination, retains drafts/errors, and uses explicit mutations and read-only status polling. Download links serve only ready stored backend PDFs; frozen previews display snapshot state.

## Check

```bash
npm test
npm run typecheck
npm run build
npm run test:e2e
```

Additional API checks:

```bash
npm run test:contract
npx tsx --test tests/api-client.test.ts
node scripts/generate-api.mjs --check
```

`npm run test:api` requires separately running **API-mode** frontend, backend, worker and a dedicated disposable database/account. Set `REKNYX_BROWSER_ORIGIN` (default `http://localhost:3100`), `REKNYX_BROWSER_USERNAME` and `REKNYX_BROWSER_PASSWORD` privately. It performs actual HTTP sign-in, creation, messaging, synthetic import, review, stored PDF download, reload, mobile overflow and keyboard checks without HTTP interception. It creates synthetic records and must not target user data. A missing password skips this explicitly configured integration suite. Stop an API-mode server before running the preview suite on its shared port; preview tests must never reuse the API server.

The Playwright suite uses Chromium and loopback port 3100. Build first for its default production-server mode. Install compatible Chromium if needed with `npx playwright install chromium`; optional `CHROMIUM_EXECUTABLE` selects an installed browser. It writes ignored screenshots/traces/sample PDFs to generated test directories. Existing browser tests assert zero backend/provider/scanner requests and do not establish actual HTTP, persistence or AI acceptance.

See the [project architecture](../docs/architecture/README.md), [structure](../docs/architecture/STRUCTURE.md), [contributor guide](../CONTRIBUTING.md), and [root agent rules](../AGENTS.md). Historical prototypes, supplied source PDFs, detailed plans and local verification records are intentionally ignored; none is required to run this preview.
