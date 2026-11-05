# CoreVAPT — Parallel Dispatch Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user's appointed frontend and backend lanes develop in parallel with explicit inputs, file ownership, and integration gates.

**Architecture:** One coordinator owns contracts/integration; each task has one writer. Lanes consume frozen interfaces; pure modules can use fixtures before runtime dependencies are available.

**Tech Stack:** Follow the [master plan](2026-11-02-00-master-plan.md); dividing work among agents does not justify more technology.

**Spec:** [Design](../specs/2026-11-02-corevapt-platform-design.md), [contracts](../specs/2026-11-02-corevapt-contracts.md).

## Global Constraints

- The user appoints the frontend agent; the coordinator must not replace that choice.
- Preserve V6.1; V6.2 is the current UX reference.
- Shared contracts, migrations, dependency lockfiles, Compose, and application wiring each have one owner.
- Mocks, API health, and prototype browser print do not establish platform E2E verification.
- Planned capability displays “In development”; connection failure is a separate error.

## 1. Role allocation

These names identify roles, not agents already assigned implementation. The user may appoint multiple frontend agents; partition owned paths or work sequentially within frontend.

| Role | Owned writes | Must not independently edit | Deliverable |
| --- | --- | --- | --- |
| C coordinator/contract/integration | Contracts, shared DTOs, app/config/dependencies/migrations/Compose/CI, STATUS | External frontend code | G0 contract, integration patches, runnable stack |
| User-appointed FE agent(s) | Frontend with one writer per subtree | Backend, preserved prototype, shared OpenAPI | UI, HTTP adapter, browser tests, build handoff |
| B domain | assessments/conversation/artifacts/policy/findings/planner and task tests | Shared registry/config/migrations | Services/router/model proposals and cases |
| W worker/scanner | worker/adapters, worker/parser tests, lab fragments | Main Compose, policy semantics, shared DTOs | Receipts/jobs/parsers/profiles and lab evidence |
| R reports | reports/templates and report tests | Artifact route ownership, app wiring, scanner | Immutable snapshots/PDFs and auth tests |
| Q QA | Acceptance registry, validation/run scripts, cross-module tests | Domain implementation to hide failures | Test matrix and independent evidence/report |

C and foundation may be the same agent; never add a second writer to shared files. When one agent has several roles, STATUS still records task/role explicitly. Lane concurrency follows actual harness capacity; do not exceed slots or assume external frontend occupies an in-session slot.

## 2. Waves — without unsupported time estimates

| Wave | External frontend lane | B/C lane | W lane | R/Q lane | Synchronization |
| --- | --- | --- | --- | --- | --- |
| W0 | Read prototype, map views, propose stack | C creates executable contracts/fixtures/types/ownership | Review parser/receipt DTOs and generic job separation | Q writes negative contract validation | G0: freeze complete schemas/errors/examples |
| W1 | FE-01 shell/preview/availability; FE-02/03 with fixtures | BE-01 foundation, then BE-02/03 | WS-01..04 parser/profile unit tests | RP2 renderer fixture; QA1 registry | Independent module tests; no integrated claim |
| W2 | HTTP adapter flows; planned while endpoints are missing | BE-04 policy + BE-05 findings with distinct owners/files; BE-06 after contracts | WS-05..07 worker DB/process after foundation/policy | RP1/RP3 after DB/artifacts; QA2 integration | Master G1/G2; contract regression on merge |
| W3 | Actual API mode; browser integration/error states | BE-07 assembly/registry/migrations | WS-08 isolated lab egress gate | DL1 Compose/CI; QA3 actual HTTP browser | G3 platform integration; mock intercepts off |
| W4 | Manual responsive/accessibility/download | C reviews requirement gaps | Live Nmap/ZAP + native Greenbone evidence | QA4 + PDF manual review | G4 lab acceptance and evidence report |

BE-02 scope/conversation and BE-03 artifacts may run in parallel after foundation; BE-04 policy and BE-05 findings may run in parallel once their dependencies are ready. With three child-agent slots, prioritize foundation + parsers + renderer/QA, then domain + worker + report integration. External frontend remains independent. QA need not hold an idle agent through W1–W4; dispatch by deliverable.

## 3. Task PD-01 — assignment packet and handoff

**Files:** `docs/implementation/STATUS.md` (C writer); module outputs follow their plans. These are planned outputs, not files created by planning.

**Interfaces:** Consumes G0 contracts, design, and subplan; produces scoped dispatch packets and merge requests.

- [ ] C checks each task's prerequisites, contract revision, and owned paths before dispatch.
- [ ] Give the agent task ID, plan/spec paths, ownership, upstream readiness, automated/manual case IDs, expected evidence, and shared-file change-request procedure.
- [ ] Agent runs targeted tests and returns exact commands/exit codes/counts/logs/IDs/hashes. Unexecuted manual checks remain not_run with missing prerequisites.
- [ ] C reviews spec compliance, then code correctness; return issues to the same owner. Do not open another writer while the task is under repair.
- [ ] C integrates shared DTOs/models/routers/migrations, then runs contract regression and affected integration seams.
- [ ] C updates capabilities at the supported level; availability changes never automatically raise evidence_level.
- [ ] Q independently verifies critical negative cases before G3/G4. Finished frontend preview keeps its label while backend remains incomplete.

## 4. Contract drift and blockers

A change request includes old/new field/route, reason, compatibility, affected owners, and fixture/test updates. C bumps the contract version, updates schemas/examples/DTOs together, and informs FE/B/W/R/Q. Lanes must not invent independent aliases merely to pass a build.

Lab/native Greenbone/provider blockers stop dependent cases only; labeled synthetic parsers, policy guards, layouts, snapshots, and error flows can continue. Foundation blockers stop DB integration, not pure parser/renderer/frontend preview. Record branch status and blockers separately; never turn a failure into skipped to pass a gate.

Conversation history/decision persistence, complete risk input schemas, and generic job/report/tool-execution separation are G0 prerequisites for their consumers. Unimplemented active-validation adapters remain denied; approval control tests never satisfy a real validation outcome or close the PDF section 9.5 gap.

## 5. Frontend handoff for the user's agent

Read the [frontend plan](2026-11-02-01-frontend-handoff.md), design, contracts, and current prototype. Before G0, map views only; after G0, build within `frontend/` and preserve prototype references. Missing backend features display “In development” with disabled mutation controls. Preview has a demo banner; network/API errors remain distinct errors. Never independently edit backend or enable capabilities. Deliver build scripts, generated contract types, F01–F15 results, manual evidence, and route-to-view mapping to C/Q.

## 6. Follow-up research prerequisites

The [readiness report](../../research/READINESS_DECISION_REPORT.md) belongs in every task packet. Contract owner resolves G0 semantics before W1 consumers. Coordinator/integration owns `ops/launcher/` and privileged-host setup; W owns the typed client and supplies preparation/start/cancel/receipt tests. The helper is not another scheduler. Import/report and FE fixture work may proceed while model access, native acquisition, remote topology or organizer permissions remain blocked. Treat the [duration-source conflict](../../research/ORGANIZER_CONFIRMATION_PACK.md) as unresolved scheduling input, not authority to extend a deadline.
