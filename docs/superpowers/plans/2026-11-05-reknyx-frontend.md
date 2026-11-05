# Reknyx Frontend Implementation Plan

> **For agentic workers:** Use scoped implementation and review agents for independent owned files. Track steps below; do not commit, push, publish, or initialize Git.

**Goal:** Convert the supplied Reknyx V7.4 HTML into a functioning local Next.js + Tailwind preview with typed mock data.

**Architecture:** Next.js App Router pages share a client preview provider and typed domain helpers. Domain helpers own fixture transitions; React components own rendering and local interaction. No backend contract is invented.

**Tech Stack:** Next.js 16.4.5, React 19.3.1, Tailwind CSS 4.3.4, TypeScript 5.9.3, locally served Manrope, Lucide icons, Node tests through tsx, Playwright.

**Spec:** [Frontend design](../specs/2026-11-05-reknyx-frontend-design.md).

## Global constraints

- Preserve `reknyx_frontend_v7_4.html` unchanged.
- All frontend files belong to `frontend/`; documentation describes only the delivered preview.
- Synthetic notice on every route; scanner/model/backend capabilities are In development.
- Approval does not execute; raw attached files are not parsed; report snapshots do not change.
- Source requirements hash remains `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

## Task 1: Typed preview domain and independent behavior tests

Owned files: `frontend/src/lib/{types,fixtures,model}.ts`, `frontend/tests/model.test.ts`.

- [x] Define typed assessment, action, finding/evidence, preferences, report snapshot, and audit records.
- [x] Write tests that reject invalid octets/fractional or unbounded ports, keep new drafts empty, prevent duplicate/out-of-scope proposals, preserve failed attempts, separate approval from execution, and freeze report data.
- [x] Run tests before implementation to establish missing behavior, implement pure immutable helpers, and rerun.
- [x] Preserve the source's two assessment scenarios and four findings as explicitly synthetic fixtures; export seven truthful integration descriptors.

## Task 2: Next.js shell and mock workflows

Owned files: package/config/lockfile, `frontend/src/app/**`, `frontend/src/components/**`, `frontend/src/lib/preview-context.tsx`.

- [x] Install pinned framework, Tailwind, font, icon, type, and test dependencies with npm.
- [x] Build the shared responsive shell with sidebar, search, notifications, preview notice, theme, and accessible native dialogs.
- [x] Build dashboard, assessments, assessment tabs/lifecycle, approvals, evidence details, reports, settings, and deterministic assistant using the typed domain.
- [x] Add a validated creation wizard; distinct generation/approval/start controls; safe file attachment with hash; frozen report preview and browser printing.
- [x] Run typecheck, production build, and focused browser tests after integration.

## Task 3: Review, verification, and handoff

Owned files: `frontend/tests/frontend.spec.ts`, `frontend/playwright.config.ts`, `frontend/README.md`, root `README.md`, `docs/implementation/reknyx-frontend-verification.md`.

- [x] Verify all source destinations, hard reload and unknown routes, creation/isolation, search, notifications, approval/retry behavior, evidence escaping, snapshots, storage failure, keyboard/focus, dark mode, and 390px/1440px layouts.
- [x] Review code against the design and address material findings.
- [x] Record exact commands, versions, pass/fail counts, screenshots, source hashes, and blocked backend checks.
- [x] Update the current project title and run instructions to Reknyx while preserving historical research names and dates.
