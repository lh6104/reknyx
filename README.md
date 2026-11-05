# Reknyx — evidence-led assessment workspace

Reknyx is an analyst-controlled, conversational VAPT assistant project, formerly named CoreVAPT. The current checkout contains research, proposed platform specifications, the supplied HTML prototype, and a **Next.js + Tailwind CSS frontend with synthetic mock data**.

The frontend is a working local preview. Backend persistence, model inference, scanner execution, native import parsing, and final PDF generation are **In development**. Historical research retains its original CoreVAPT titles and verification dates.

## Run the frontend

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**. Requires Node.js 20.9 or later. See [frontend setup and behavior](frontend/README.md) for pinned versions, production commands, routes, testing, and preview limitations.

The frontend converts [Reknyx V7.4 HTML](reknyx_frontend_v7_4.html) into typed React components while retaining its visual direction and workflows. The original HTML is preserved unchanged and can still be opened directly in a browser.

Implemented preview flows include the dashboard, assessment creation and scope, deterministic assistant, plan and approval review, failure/retry history, finding evidence and disposition, local file attachments, frozen sample reports, browser printing, and preferences. Every route labels synthetic data. Approval never executes a scan, and attachments never claim native parsing.

New assessment data and reports reset on reload; only non-sensitive preferences persist. Do not use the preview for production evidence or authorization.

## Verification

```bash
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

The browser suite needs compatible Playwright Chromium and uses loopback port 3100. It writes screenshots, traces, and a synthetic sample PDF. See the [current verification record](docs/implementation/reknyx-frontend-verification.md) for actual results and evidence. Preview checks do not establish live scanner, model, backend, or platform readiness.

## Project context

- [Mandatory requirements: 1.pdf](1.pdf) and [source provenance](docs/research/sources/requirements-1-provenance.json).
- [Project context](context.md), [readiness decisions](docs/research/READINESS_DECISION_REPORT.md), and [research index](docs/research/README.md).
- [Reknyx frontend design](docs/superpowers/specs/2026-11-05-reknyx-frontend-design.md) and [implementation plan](docs/superpowers/plans/2026-11-05-reknyx-frontend.md).
- [Platform design](docs/superpowers/specs/2026-11-02-corevapt-platform-design.md), [draft contracts](docs/superpowers/specs/2026-11-02-corevapt-contracts.md), and [G0 decisions](docs/research/G0_CONTRACT_DECISIONS.md).
- [Master plan](docs/superpowers/plans/2026-11-02-00-master-plan.md), [frontend handoff](docs/superpowers/plans/2026-11-02-01-frontend-handoff.md), [parallel ownership](docs/superpowers/plans/2026-11-02-06-parallel-dispatch.md), and [testing plan](docs/superpowers/plans/2026-11-02-05-testing-acceptance.md).
- [Scanner readiness](docs/research/SCANNER_READINESS_DECISIONS.md), [provider decisions](docs/research/MODEL_PROVIDER_DECISIONS.md), [safety/recovery](docs/research/SAFETY_RECOVERY_PILOT_DECISIONS.md), and [competition/real-world evaluation](docs/research/COMPETITION_METRICS_AND_REAL_WORLD.md).

The proposed backend remains a FastAPI modular monolith with PostgreSQL canonical state, a separate worker, and private immutable artifacts. G0 executable schemas and backend integration remain pending. The preview introduces no backend endpoint or live execution capability.

Historical V6.2–V6.4 verification records and screenshots remain research evidence for their dated prototype runs. Their HTML files are absent from this checkout; the current user-selected source is V7.4. The current frontend navigation follows that source while preserving the six assessment lifecycle meanings.

Project documentation and UI copy are English. Development [skills](.agents/skills) guide implementation; they are not runtime product features. Competition requirements, proposed architecture, synthetic UI behavior, and verified operational capabilities remain distinct.
