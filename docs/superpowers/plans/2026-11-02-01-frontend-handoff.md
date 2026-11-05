# CoreVAPT — Frontend Parallel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The user's appointed frontend agent builds the current prototype UX in parallel with the backend through a shared contract and accurately represents unavailable functionality.

**Architecture:** Frontend owns views/state and the HTTP adapter; backend owns policy, authorization, persistence, and scanners. Fixture preview is explicit; live mode never silently falls back to mocks after a failed request.

**Tech Stack:** The frontend owner chooses and records the framework/build tool before scaffolding; TypeScript, generated contract types, browser tests. Do not change the backend stack.

**Spec:** [Design](../specs/2026-11-02-corevapt-platform-design.md), [contracts](../specs/2026-11-02-corevapt-contracts.md), [current V6.4 prototype](../../../corevapt_frontend_v6.4.html). V4 was the historical reference for the initial plan; its removed file is not required. Preserve V6.1, V6.2 and V6.3 as predecessors.

## Global Constraints

- The user appoints the frontend agent; the coordinator must not replace that choice.
- Preserve existing prototype references; implementation belongs to the appointed frontend owner.
- Planned capability displays “In development”; connection failure is a separate error.
- Mocks, API health, and prototype browser print do not establish platform E2E verification.
- Shared contracts, migrations, dependency lockfiles, Compose, and application wiring each have one owner.

## FE-01 — shell, contract client, and feature availability

**Prerequisites:** G0 executable contracts+fixtures. Before G0, inventory prototype views but do not invent endpoints/types.

**Files:** Create `frontend/package.json`, lockfile, `frontend/src/app/`, `frontend/src/api/client.ts`, `frontend/src/api/types.generated.ts`, `frontend/src/features/capabilities/`, `frontend/src/preview/`, `frontend/tests/capabilities.spec.ts`. The contract owner owns `contracts/`; frontend only regenerates types.

**Interfaces:** Consumes `/api/v1/auth/me`, `/capabilities`, and the error schema; produces an authenticated `ApiClient`, capability views, and three primary destinations (Dashboard/Assessments/Agents), three contextual assessment views (Workflow/Findings/Report), and focused drawers. Base URL is configuration; cookies/CSRF go through the client; the bundle contains no password/key.

- [ ] Map Dashboard/Assessments/Agents and the Workflow/Findings/Report working views. Keep the six-phase lifecycle visible, and bind the one assistant profile to assessment context. Scope, action approvals, source comparison, evidence and configuration are contextual drawers; audit/logs/raw payloads are disclosed on demand. Six lifecycle meanings do not require six separate routes.
- [ ] Write failing F01–F05 before availability handling.
- [ ] Create the app shell/shared client; generate G0 types and display runtime contract errors with request IDs.
- [ ] Separate an explicit preview adapter through environment/build mode; display a fixture banner on every route and prohibit scanner/live mutations from preview.
- [ ] Run typecheck/build and targeted browser tests; record viewport, preview/live mode, and request logs.

Illustrative Playwright test after the frontend owner installs the harness:

```typescript
import { test, expect } from '@playwright/test';
test('F01 planned PDF never pretends to be ready', async ({ page }) => {
  await page.route('**/api/v1/capabilities', route => route.fulfill({
    json: { contract_version: '0.1.0', capabilities: [{
      id: 'reports.pdf', availability: 'planned',
      reason_code: 'module_in_progress', message: 'In development',
      mode: 'server_pdf', evidence_level: 'none'
    }] }
  }));
  // The harness seeds an authenticated session and empty assessment from G0 fixtures.
  await page.goto('/assessments/00000000-0000-0000-0000-000000000001/reports');
  await expect(page.getByTestId('capability-reports.pdf')).toContainText('In development');
  await expect(page.getByRole('button', { name: 'Generate PDF' })).toBeDisabled();
});
```

This proposed test is not executable until the harness/auth fixtures exist. The owner adds a request counter asserting zero POST reports calls, proving absence of the side effect.

| Case | Setup/action | Expected |
| --- | --- | --- |
| F01 | reports.pdf planned | “In development”, disabled mutation, zero POST |
| F02 | Abort capabilities network request | Connection error + retry; no preview/fake data |
| F03 | 401 / 403 / 500 | Distinct login / denial / server error; never planned |
| F04 | Explicit preview | Banner on every view, fixture data, no scanner API |
| F05 | API returns an invalid enum | Contract error with request ID; no empty-state concealment |

## FE-02 — assessment, planner, and approval

**Files:** Create `frontend/src/features/{assessments,scope,planner,approvals,timeline}/`, `frontend/tests/assessment-flow.spec.ts`, `frontend/tests/approval.spec.ts`. Include persisted conversation in the planner view through the G0 message contract; do not keep assessment history solely in browser memory.

**Interfaces:** Consumes G0 assessment/scope/request/messages/plans/actions/approvals/executions/timeline endpoints; sends expected revisions/hashes; produces contract-valid UI events and requests. Action proposals remain read-only until the backend decides.

- [ ] Write F06 assessment isolation, F07 stale scope, F08 approval denial, and F09 double submission/retry.
- [ ] Convert the prototype assessment selector/create form to server state; a new draft is empty and has no automatic findings.
- [ ] Display LLM/deterministic source, evidence basis, policy result, exact target/profile, expiry, and limitations.
- [ ] Submit grant/reject with rationale/hash; 409 requires refresh and another review, never automatic resubmission of approval.
- [ ] Preserve the execution idempotency key when retrying the same body; approval is not scan success.
- [ ] Poll with backoff/stop/unmount; cancellation remains requested until the server confirms a terminal state.
- [ ] Run browser tests with explicitly labeled mocked HTTP; after G3 rerun against the actual API.

Manual F06–F09: create A/B and switch assessments without leaking observations; change scope in tab two, then approving in tab one must return 409; rejection creates no execution; double click produces one job. Preserve redacted HAR, screenshots, and audit IDs.

## FE-03 — findings, evidence, correlation, and reports

**Files:** Create `frontend/src/features/{findings,correlation,evidence,reports,integrations}/`, `frontend/tests/findings-report.spec.ts`, `frontend/tests/layout.spec.ts`.

**Interfaces:** Consumes observations/findings/review/correlation/artifacts/reports endpoints and provenance; the server authorizes artifact/PDF downloads. Browser print is not a replacement for a backend PDF.

- [ ] Write F10 historical/unknown, F11 review revision, F12 snapshot immutability, F13 escaped scanner HTML, F14 layout/keyboard, and F15 reload persistence.
- [ ] Distinguish observations from findings; show source-specific confidence, unknown missing CVSS, and separate observed/ingested timestamps for historical data.
- [ ] Trace the detail drawer through observation → artifact/hash/locator; never render raw scanner HTML as trusted DOM.
- [ ] Require a rationale for correlation review; do not merge different assets/locations automatically or change canonical membership when the backend rejects it.
- [ ] Display report pending/rendering/failed/ready states; download only when ready; later triage does not change older snapshots. These are report states, separate from tool execution states.
- [ ] Display all seven tools, live/import/unsupported modes, and evidence levels; a UI control does not turn Planned into Working.
- [ ] Verify 1440 px desktop and 390 px mobile: no overflow, keyboard focus for drawers/modals, labels, loading/empty/error states, and assessment-scoped downloads.

Manual: import scanner text containing `<script>` and confirm it remains text; review a finding and reload to verify server persistence; generate a PDF, change triage, and redownload the same report with the same SHA; show partial limitations after a timeout. Preserve browser trace, download SHA, and report ID.

## FE-04 — handoff and test commands

**Files:** Create `frontend/README.md`, `frontend/.env.example`; update evidence/status through the coordinator; do not edit backend files.

- [ ] Record framework/version, install/run/build/test commands, type-generation command, preview/API mode, and base URL.
- [ ] Provide `typecheck`, `build`, and `test:e2e` package scripts; frontend owns its lockfile and CI calls the handed-off scripts.
- [ ] Deliver route mapping F01–F15, per-view status, and backend blockers; completed screens remain UI preview while HTTP is mocked.
- [ ] At G3, rerun F06–F15 against actual API/DB/worker; retain correct labels for mock-only cases.

Target commands after harness creation: `npm --prefix frontend ci`, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`, `npm --prefix frontend run test:e2e`. No package/harness was established by the initial plan; never report a pass before actually running the checks.

## Follow-up contract/readiness input

Consume the [G0 decisions](../../research/G0_CONTRACT_DECISIONS.md) and [readiness report](../../research/READINESS_DECISION_REPORT.md) when executable schemas are frozen. Message append is idempotent and does not call the model; planning is a separate explicit idempotent operation. Preparation/reservation does not mean scanner running: show actual start receipts and preserve cancel-requested/unknown outcomes. The first live profile is one dedicated IPv4 asset, explicit TCP ports and an origin-wide web scope; broader imported historical identities remain evidence, not authorization. Keep preview data and live API availability separate. No follow-up research changes the user's ownership of frontend implementation.

## FE-06 — V6.4 dashboard, workflow and single assistant

The [current page map and settings/demo specification](../../research/UX_STANDARDS_AND_PAGE_MAP.md) implements the approved V6.2/V6.3 merge and supersedes their navigation inventories. Preserve all evidence/policy/attempt/snapshot semantics; do not add backend services to reproduce browser-local defaults.

- Dashboard: valid Pending approvals; latest unresolved run per assessment/target/profile; canonical needs-review candidates; frozen local drafts. Every CTA enters the correct assessment. Do not aggregate source observations as vulnerabilities or call candidate severity an overall risk score.
- Workflow: visible lifecycle and current task/reason/basis/decision/expected result; request/conversation, compact plan and attempt list. Messages, Edit request, Generate plan, approval and start stay separate. Scope/action/log detail opens contextually. A new retry proposal returns the task to Plan; an old failure cannot hide a valid proposal.
- Agents: one Assessment assistant with role, mode, provider/model availability, capabilities, limits and assessment activity. The assessment header binds that same assistant and opens a short profile summary. No agent-creation/model-key/marketplace controls.
- Navigation: Dashboard/Assessments/Agents plus footer Settings. New assessment appears once in the current page header; none in sidebar/mobile menu. Workflow/Findings/Report keep the read-only Scope/Plan/Collect/Analyze/Review/Report lifecycle visible.
- Findings: ranked candidate register, source-comparison entry, risk/disposition drawer, evidence register and audit. Do not restore separate Analyze/Review pages for the same repeated task.
- Report: readiness, explicit draft limitations, executive/technical frozen snapshot and truthful backend download status.
- Tools/defaults drawer: seven-tool current/target status plus three bounded new-assessment defaults. No API credentials or arbitrary tool/model controls in the client.

For live integration, dashboard counts need authorized server aggregates over complete data, not totals from a paginated browser subset. Use the same current-attempt definition across dashboard, lifecycle and report readiness; retain superseded failures in history/limitations. Workspace defaults copy into new draft scope only. A current assessment edit must create a scope revision and invalidate grants. Background polling must not discard unsaved forms; explicit Send must clear the sent composer. One overlay at a time, with contextual Back and logical keyboard focus.

[Actual V6.4 browser evidence](../../research/FRONTEND_V6_4_VERIFICATION.md) is independent of future HTTP/platform cases F01–F15. No backend gate is passed by these UI checks.

## Approved V6.4 preview handoff

The user approved the [merge research](../../research/FRONTEND_V6_2_V6_3_MERGE_RESEARCH.md). The [standalone V6.4 implementation plan](2026-11-02-frontend-v6-4.md) and [fresh verification](../../research/FRONTEND_V6_4_VERIFICATION.md) document the delivered preview. The profile exposes one assistant, not a runtime multi-agent system. Current model is Not connected; provider is Not configured; responses are deterministic. Capture the current task/request/scope/evidence basis when a message is sent, so an asynchronous explanation does not use another assessment or contradict an edited request.

This page composition introduces no new backend endpoint or frozen executable schema. Existing G0 ownership and F01–F15 HTTP/platform acceptance remain pending; their checkboxes are not completed by the standalone browser tests. Mobile assistant access is inline with the current task, avoiding a floating control over scope/approval actions.
