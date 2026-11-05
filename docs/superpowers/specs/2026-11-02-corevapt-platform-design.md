# CoreVAPT — implementation design and ownership

Date: 2026-11-02. Status: **proposed implementation design**; no platform application or platform test results are established by this document. The user requested a master plan, parallel work plans, and testing before implementation. The user appoints the frontend agent; the coordinator must not replace that choice.

## 1. Basis and scope

Sources: [requirements R01–R15](../../research/REQUIREMENTS_MATRIX.md), [technical recommendations](../../research/TECHNICAL_RECOMMENDATIONS.md), [upstream analysis](../../research/UPSTREAM_ARCHITECTURE_COMPARISON.md), and the [current V6.4 prototype](../../../corevapt_frontend_v6.4.html). Earlier plans used V4 as a historical UX reference; its removed file is no longer a dependency. V6.1, V6.2 and V6.3 remain preserved predecessors. The prototype is a UX reference: fixture data and browser-side approval logic must not become canonical application state.

The local MVP lets an identified analyst create an assessment and scope, submit a conversational request, receive an evidence-based proposal, review actions under policy, run/import the three Nmap/ZAP/Greenbone sources, inspect findings with provenance, review them, and download a PDF snapshot. Modules lacking live prerequisites may still be developed and parser-tested independently, but cannot be accepted as live integrations.

The mandatory source is [1.pdf](../../../1.pdf), 10 pages, SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`. Its minimum is three working integrations or supported imports with network and web coverage; it does not require seven live scanners. The eight rubric weights are end-to-end coverage 15, AI reasoning and decisions 20, technical accuracy 15, correlation and false positives 15, risk prioritization 10, safety and scope control 10, report quality 10, and efficiency and robustness 5. These are evaluation weights, not guaranteed scores.

## 2. Architecture and responsibilities

FastAPI modular monolith plus PostgreSQL and a separate worker process from the same codebase; private local artifact volume; frontend HTTP polling. PostgreSQL owns state, revisions, conversation messages, plans, approvals, execution attempts, audit events, report jobs, and manifests. The filesystem holds immutable raw bytes and PDFs. Do not add a broker, vector database, multi-agent runtime, or second workflow engine to the MVP. Development subagents organize delivery; they are not the product's runtime architecture.

- Foundation: application wiring, configuration, shared DTOs, DB sessions, migrations, local analyst authentication, and capability registry.
- Assessment/policy: versioned scope, rules of engagement, action fingerprint, semantic validation, approval, and dispatch authorization.
- Conversation/planner: persisted analyst/assistant messages, bounded context assembled from canonical snapshots, proposal basis IDs, and budgets. Conversation text is untrusted input and never expands scope or authorizes execution.
- Worker/adapters: durable claims, receipts, bounded execution, native parsers, and typed job dispatch. The existing worker also claims import and report jobs; report rendering never invokes a scanner.
- Findings: observations, membership, explainable correlation, and priority with explicit unknowns.
- Reports: freeze state, render the six PDF sections 7.1–7.6, and authorize downloads.
- Frontend: reproduce the current prototype workflow through the contract; every screen expresses actual availability and state.
- Integration/QA: connect modules, provide the local environment, compare contracts, and collect automated/manual evidence.

## 3. Proposed structure and ownership

```text
contracts/                      # OpenAPI + JSON fixtures; contract owner
backend/pyproject.toml           # foundation/integration owner
backend/src/corevapt/
  app.py config.py contracts.py  # foundation/contract owner
  foundation/                   # DB, auth, event log, capability registry
  assessments/                  # includes conversation.py; assessment owner
  artifacts/ policy/ findings/ planner/
  worker/ adapters/             # worker owner; typed scan/import/report jobs
  reports/                      # report owner; snapshot + renderer
backend/alembic/                 # sole foundation owner
backend/tests/                  # each module owner creates its domain tests
frontend/                       # only the agent appointed by the user
ops/                            # integration owner; worker supplies lab network fragment
compose.yaml                    # sole integration owner
scripts/                        # integration/QA
tests/e2e/                      # QA acceptance across the stack
```

Preserve V6.1/V6.2/V6.3 as historical references; use V6.4 for current page composition; frontend implementation changes require the user's appointed owner. The paths above are proposed delivery contracts, not evidence that these modules exist or pass tests. Check the actual workspace before implementation.

## 4. Required invariants

- The backend checks scope/version/ROE; approval never expands scope. The backend derives the actor and does not trust a client-supplied actor.
- Only catalog profiles can be dispatched; UI/model-generated arbitrary shell commands or argv are rejected.
- The worker first reserves a bound attempt after policy checks. After network preparation, the trusted launcher rechecks scope/hash/expiry/budget/grant and consumes the grant in the final `authorize_start` transaction. Scope revision and final start authorization use the same locking mechanism; the physical process-start gap is explicitly reconciled. A later scope change cannot retract traffic already sent: request cancellation of affected attempts and audit the outcome.
- No implemented active exploitation profile is implied. Offensive validation is denied until an explicit profile, scope rule, action-bound human approval, bounded adapter, and outcome/audit tests exist. A prototype approval click is not an execution control.
- A crash after an external side effect must not automatically retry a live scan. Reconcile receipts/process state; otherwise use `execution_unknown`.
- Artifacts are immutable and SHA-256-addressed; normalization never changes raw bytes. DB/filesystem operations do not share an atomic transaction: track and reconcile orphans.
- An observation differs from a finding; an Nmap service is not automatically a vulnerability. Correlation preserves memberships and never merges solely by title/CVE.
- Unknown severity/CVSS/exposure never becomes zero or invented data. Preserve each source's confidence method. Risk inputs include exposure, exploitability, and asset impact with evidence/source references, explicit unknowns, and a versioned ranking rule.
- The model only proposes; independent schema and semantic validators enforce the contract. The model has no scanner credentials, DB access, or direct execution authority.
- Reports use immutable snapshots containing limitations, failed executions, decisions, risk inputs, and evidence references. Rendering runs as a report job on the existing worker, outside the HTTP request transaction.
- Label test/mocked data separately. A mock, API health response, or prototype browser print does not establish platform E2E verification.

## 5. Initial choices

Backend: FastAPI/Pydantic, SQLAlchemy/Alembic, and PostgreSQL; the foundation owner verifies exact versions against official documentation and pins the lockfile before building. Use a deterministic state machine with planner proposals; do not introduce LangGraph initially. Live profiles: bounded Nmap TCP connect and ZAP packaged baseline JSON. Third integration: native Greenbone XML import. PDF: HTML template plus WeasyPrint, with untrusted file/network fetch blocked and pinned Unicode fonts.

The user's frontend agent proposes the frontend stack before scaffolding, while respecting the contract, current prototype UX, and browser tests. That choice does not block backend work. Provider/model details have not been supplied: the planner interface, semantic validation, and deterministic fallback can be tested independently. Enable live LLM capability only after credentials and separate provider tests are available. Do not select a model or call paid APIs during planning.

Live targets must be explicitly authorized by the user/organizer or belong to an isolated project lab. The egress gate must block destinations/redirects outside the lab, including DNS/IPv6. Until that is demonstrated, live capability stays `planned`/`unavailable`. Greenbone needs a genuine native export with provenance to pass the third-integration gate; synthetic fixtures only demonstrate parser behavior.

## 6. Frontend before backend

The API capability manifest distinguishes `planned`, `available`, `unavailable`, and `unsupported`; job state and verification level are separate dimensions. Planned capability displays **“In development”** with the missing work and a disabled mutation control. An unreachable API displays **“Unable to connect to the service”**; it must not become planned or silently fall back to mocks. Explicit fixture preview always displays **“Demo data — backend not connected”** and never presents fixture success as real execution.

Every layout can be tested before backend completion, but record acceptance as `UI preview`, not `integrated`. When the backend is ready, connect the HTTP adapter and run the contract/browser suites; do not alter UI data to conceal a contract violation.

## 7. Coordination and acceptance

The master plan separates contract preparation, parallel implementation, integration, and acceptance. Each task has an owner, prerequisites, owned files, automated cases, a manual procedure, and evidence. Use `planned → in_progress → implemented → local_verified → integration_verified`; record blockers separately. Every status transition requires evidence; document progress is not software progress.

The initial planning survey found no Git repository. That is a historical observation, not a current guarantee. Recheck before implementation; if Git is still absent and repository setup is authorized, the coordinator creates it, adds ignores for credentials/artifacts, then uses branches/worktrees if appropriate. On a shared filesystem, agents respect file ownership and route shared edits through the coordinator. This documentation audit does not initialize Git or implement the platform.

## 8. Frontend V6.2 and remaining backend work

The V6.2 HTML provides a local six-step scenario, deterministic conversation, structured action/approval, per-attempt execution simulator, hashed synthetic fixtures, correlation membership, risk/disposition review, and a frozen report sample. The frontend owner’s [verification record](../../research/FRONTEND_V6_2_VERIFICATION.md) reports browser checks; this documentation audit did not rerun them. Browser-only evidence cannot establish platform integration. Do not promote synthetic fixtures or client-side policy into canonical state.

Map the PDF's eight workflow stages to six views: Scope holds request/authorization; Plan holds planning/approval; Run holds orchestration/ingestion; Analyze holds normalization/correlation; Review holds risk/human review; Report holds snapshot/delivery. Approval appears beside the proposal. Offensive validation always requires approval, even where real ROE permits baseline scans automatically.

Every run needs its own target, ports, scope version, action/approval/attempt references, outcome, and artifacts. Preserve old evidence as history; only target/service-port evidence valid under current scope may support a web action. Retry is bound to the failed run, never reuses a consumed grant, and cannot restart an old failure after a newer attempt has run.

## 9. Architecture and evaluation review

Read the [architecture fit review](../../research/ARCHITECTURE_FIT_REVIEW.md) for the proposed module ownership and unresolved acceptance gaps, and the [competition metrics and real-world validation plan](../../research/COMPETITION_METRICS_AND_REAL_WORLD.md) for rubric-aligned experiments. These extend design/verification requirements; they do not establish implemented capabilities or measured scores.

## 10. Readiness decisions after follow-up research

Use the [readiness decision report](../../research/READINESS_DECISION_REPORT.md) as the current research handoff. The [G0 decisions](../../research/G0_CONTRACT_DECISIONS.md) narrow the first live slice to a dedicated IPv4 asset and explicit TCP ports; imported data may retain broader source identities without authorizing them. The [scanner format/profile decisions](../../research/SCANNER_READINESS_DECISIONS.md) require pinned Nmap XML1.05, AF-only origin-wide ZAP and reviewed native Greenbone selectors. No public test sample establishes working integrations.

The [host launcher design](../../research/SAFETY_RECOVERY_PILOT_DECISIONS.md) defines per-attempt namespace enforcement, local/remote topology gates, final start fencing and restore behavior. The launcher is a privileged, narrowly exposed adapter on a dedicated trusted host, not a second product orchestrator. All implementation/host/network tests remain unrun. The [provider shortlist](../../research/MODEL_PROVIDER_DECISIONS.md) names a conditional first evaluation; no provider is activated or quality winner established. Organizer target/profile/validation and schedule questions remain in the [unsent confirmation pack](../../research/ORGANIZER_CONFIRMATION_PACK.md).

## V6.4 frontend revision — approved page boundaries

The [analyst UX/page map](../../research/UX_STANDARDS_AND_PAGE_MAP.md) is the current frontend reference. Three permanent destinations: Dashboard, Assessments and Agents, with Settings in the footer. Agents describes one Assessment assistant with truthful role/model/mode/capability/limit/activity information. An assessment has Workflow, Findings and Report views; scope/configuration/approval/evidence/comparison are contextual. The read-only Scope/Plan/Collect/Analyze/Review/Report lifecycle stays visible. Workflow shows the current task, reason, basis, required decision and expected result. New assessment appears once in the page header, never in sidebar/mobile navigation. This changes frontend composition without changing the backend ownership or authorization boundary.

Dashboard counts represent authorized current work, not whole-system security posture. Approval, run outcome, technical validation, analyst disposition and report release remain distinct. Current run issues use the latest attempt for the assessment/target/profile; report limitations retain earlier failures after resolution. Workspace defaults are initial draft parameters, never authorization. Browser verification is recorded [separately for V6.4](../../research/FRONTEND_V6_4_VERIFICATION.md); production usability, accessibility conformance, scanner/model integration and persistence remain unverified.

The user-approved [merge rationale](../../research/FRONTEND_V6_2_V6_3_MERGE_RESEARCH.md) governs composition. A clarification message preserves request revisions/grants; Edit request, explicit plan creation, approval and execution start are separate. Retry proposals take precedence over historical failure in the task projection. The preview uses deterministic replies and synthetic evidence; no model is connected. Agents is a view over one assistant role and existing assessment records, not a new runtime service or multi-agent architecture. G0 contracts and backend authority remain unchanged.
