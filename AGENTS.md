# CoreVAPT agent instructions

Applies to the entire repository unless a more specific `AGENTS.md` governs a subtree. Follow system/developer instructions and the user's explicit task and constraints first. This file provides project conventions; it does not authorize scans, paid API calls, publication, or unrelated implementation.

## Start each task

1. Inspect the actual checkout, applicable instructions, and files relevant to the task. Use `rg` and `rg --files`; do not infer implementation from a plan, screenshot, filename, or previous session.
2. Read [README.md](README.md), the [readiness decision report](docs/research/READINESS_DECISION_REPORT.md), and the assigned module plan. Read only the additional decision documents needed for that task.
3. For requirement, architecture, security, or acceptance changes, read the relevant sections of mandatory [1.pdf](1.pdf). Read all ten pages for broad requirement/architecture reviews. The reviewed baseline SHA-256 is `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`; verify and disclose a changed source rather than silently replacing it.
4. Identify owned paths, interfaces, prerequisites, verification, and expected deliverables before editing. Read applicable skills in [.agents/skills](.agents/skills); use the actual available tool interfaces.
5. Carry out authorized work without repeatedly requesting permission for routine reversible steps. Ask only for material missing inputs or actions outside the authorized scope; continue independent work when a prerequisite blocks one lane.

## Project purpose and evidence boundary

CoreVAPT is an analyst-controlled, conversational VAPT assistant: authorized request/scope → evidence-led planning → permitted execution/import → normalization/correlation → risk/review → traceable report.

Observed on **2026-11-02**: this checkout contains research, proposed specifications/plans, standalone V6.1/V6.2/V6.3 prototypes, and prototype browser scripts. Backend, database migrations, executable OpenAPI, worker, and Compose deployment were not present. Recheck before relying on this snapshot. A newer prototype file does not establish a passing verification run.

Keep these distinct: proposed design, implemented code, synthetic fixtures, public format references, native captures, local integration, real model evaluation, authorized live scanner execution, and operational pilot readiness. Never promote one into another without evidence.

## Sources and implementation decisions

- Competition requirements come from `1.pdf`; current organizer rules and actual ROE establish external permissions. Project architecture, model choices, and numerical test targets are design decisions, not organizer mandates.
- Use the [platform design](docs/superpowers/specs/2026-11-02-corevapt-platform-design.md), [draft contract](docs/superpowers/specs/2026-11-02-corevapt-contracts.md), and [G0 decisions](docs/research/G0_CONTRACT_DECISIONS.md) together. G0 remains unpassed until executable schemas/examples and semantic checks pass and owners review them.
- Use [scanner decisions](docs/research/SCANNER_READINESS_DECISIONS.md), [provider decisions](docs/research/MODEL_PROVIDER_DECISIONS.md), and [safety/recovery decisions](docs/research/SAFETY_RECOVERY_PILOT_DECISIONS.md) for their respective interfaces and limits. Verify changing versions, models, prices, and provider policies against primary documentation before use; a dated shortlist is not an enabled provider.
- Consult the [organizer confirmation pack](docs/research/ORGANIZER_CONFIRMATION_PACK.md) for unresolved targets, validation acceptance, and duration wording. Do not assume either the six-day listing window or the 24-hour announcement has been definitively confirmed.
- If sources conflict, identify the exact conflict and its affected gate. Do not invent compatibility aliases, permissions, completed work, or deadlines to hide it. Preserve historical records and their original verification dates.

## Architecture and scope

- Keep a FastAPI modular monolith, PostgreSQL canonical state, a separate worker from the same codebase, and private immutable artifact storage. Use frontend HTTP polling initially.
- PostgreSQL owns assessment/scope revisions, conversations, decisions, grants, jobs/attempts, findings/memberships, audit, and artifact manifests. Models and browser state are projections, not canonical authority.
- Do not add a broker, Kubernetes, graph/vector database, distributed runtime agents, or another workflow engine without a concrete requirement or measured failure mode and an explicit design change. Development subagents do not imply runtime multi-agent architecture.
- Keep interfaces small, typed, and testable. Separate native parsing, policy, execution, correlation/risk, and rendering. Avoid unrelated refactoring and speculative abstractions.
- Preserve scope boundaries from the decision documents: the initial live slice is one dedicated authorized IPv4 asset with explicit TCP ports; ZAP requires an origin-wide web scope. Imported historical identities may be broader without authorizing live traffic.
- Target integrations are bounded Nmap discovery, AF-only ZAP baseline, and Greenbone native XML import. The conditional Nikto import fallback requires its acquisition/contract decision; it is not an automatic fourth integration.

Proposed application paths are `backend/src/corevapt/`, `backend/alembic/`, `backend/tests/`, `contracts/`, `frontend/`, `ops/`, and `scripts/`. Create them only as part of assigned implementation; they are not existing build targets merely because this file names them.

## Ownership and parallel work

Follow the [master plan](docs/superpowers/plans/2026-11-02-00-master-plan.md) and [parallel dispatch plan](docs/superpowers/plans/2026-11-02-06-parallel-dispatch.md).

| Owner | Write scope |
| --- | --- |
| Coordinator / foundation / contract | Shared OpenAPI/DTOs, app wiring/configuration, dependencies/lockfiles, model registry, migration graph, Compose/CI, `ops/launcher/`, cross-module integration |
| User-appointed frontend agents | Assigned prototype/frontend subtrees and their browser tests |
| Domain owners | Assigned assessment/conversation, artifact, policy, finding/risk, or planner modules and their tests |
| Worker/scanner owners | Worker/adapter modules, typed launcher client, parser/process tests, and lab integration proposals |
| Report owner | Snapshot/render/template modules and report tests |
| QA owner | Acceptance/evaluation registry, cross-module verification and evidence reports |

- The user chooses frontend agents. Do not replace that assignment or modify frontend assets during backend/research work unless the task includes them. Preserve predecessor prototypes unless the user requests their removal or revision.
- One writer per file. Shared-file changes go through the designated owner; do not concurrently edit migrations, lockfiles, app wiring, or contracts.
- Use subagents only when the user's authorization or applicable skill permits them and tasks have independent owned paths. Include task/spec/contract revision, prerequisites, paths, cases, and expected evidence in each handoff. Review results before integration.
- G0 precedes contract-dependent implementation. Pure parsers/renderers and frontend previews can use agreed fixtures in parallel; DB integration waits for foundation, and live execution waits for authorization and enforcement.
- Check Git state before using branches/worktrees. Do not assume Git exists, initialize it merely for documentation verification, or reset/clean/revert another agent's work. Do not commit, push, merge, publish, or deploy as an incidental part of another task.

## Security, state, and provenance invariants

- Execute only on targets covered by the applicable authorization/ROE. Public fixture addresses, user-entered domains, checkboxes, and generated text are not permission. Project-owned local testing and the organizer-scored lab are separate authorization contexts.
- Accept only catalog profiles and typed bounded parameters. No model/client-controlled shell, argv, executable, image, mount, network selector, or arbitrary SQL endpoint.
- Derive actor identity from authenticated server context. Approval binds the exact action/profile/parameters, target, scope version/hash, expiry, and budget; it never overrides a deny or unsupported capability.
- `authorize_dispatch` reserves an attempt/grant/budget. The trusted launcher performs final `authorize_start` after network preparation and consumes the grant under the same scope serialization discipline. Preparation is not scanner start; retain the physical-start/revocation limitation explicitly.
- API, planner, worker, and scanner receive no raw Docker socket. Use the narrow trusted launcher interface and assessment-bound network enforcement. Local and routed modes require separate allow/deny evidence; Docker `internal` alone is insufficient. Profile-owned ZAP flags/loopback port must match the pinned scanner and firewall specification.
- Never blindly rerun an uncertain live attempt after timeout, lease expiry, crash, or restore. Reconcile exact attempt/fence/process/receipt identity; use `execution_unknown` when unresolved. Reparse immutable bytes without rescanning when safe.
- Store raw bytes before parsing; retain SHA-256, source, timestamps, parser version, and raw locator. Do not overwrite raw evidence, follow untrusted XML entities/URLs, or accept client-selected filesystem paths. Reconcile DB/filesystem publication gaps honestly.
- Keep source observations separate from canonical findings. Open services are not automatically vulnerabilities. Correlation retains every membership/source and does not merge solely by title/CVE; asset, service/location, time, and compatible rule meaning matter.
- Preserve source severity, CVSS vector/version/source, confidence method, validation status, analyst disposition, and contextual risk separately. Unknown stays unknown; never fabricate CVEs, proof, calibrated probabilities, or risk scores.
- Treat scanner banners/HTML/imports/model output as untrusted data. Validate schema, references, assessment ownership, semantic applicability, revisions, preconditions, and budgets independently of model instructions.
- Message append does not invoke inference. Explicit plan requests and other side-effecting creation operations use the specified idempotency semantics. Label deterministic fallback and preserve failed provider attempts; do not silently change provider or send evidence elsewhere.
- Reports render immutable consistent snapshots with sections 7.1–7.6, evidence links, review/approval history, failures, historical inputs, and limitations. A ready PDF file is not automatically a client-ready assessment.
- Keep secrets and sensitive raw data out of source control, browser storage, prompts, reports, and routine logs unless the destination and data use are explicitly covered. Honor existing authorization; do not request it again unnecessarily. A research task alone does not authorize paid generation calls or external messages.
- No active/offensive validation is implied by the baseline catalog. Keep PDF §9.5 unresolved until the permitted capability/demo and required outcome evidence are established; a fake runner is not live validation.

## Frontend and documentation conventions

- Project-authored documentation, comments, product labels, and sample copy are English. User-facing conversation may be Vietnamese. Preserve real identifiers, source bytes, and deliberately multilingual test fixtures.
- Inspect available prototype versions and their matching verification records. For dashboard/page composition, read [UX standards and page mapping](docs/research/UX_STANDARDS_AND_PAGE_MAP.md). Preserve the assessment lifecycle even when several stages share one view; do not reinstate obsolete navigation just because an older plan names it.
- Planned capability displays **“In development”** and disables unavailable mutations. Connection/runtime errors remain errors. Preview always has a synthetic/demo notice; no silent mock fallback, fake success, or invented progress/coverage.
- Keep assessment context, actionable reasons, source uncertainty, and keyboard/overlay behavior visible. Workspace defaults do not modify existing scope or authorize an action.
- Link to the authoritative decision instead of duplicating entire research sections. When editing several documents, reread each file into its own content variable, preserve unrelated sections, check its title, and inspect the resulting content/links before claiming completion.

## Verification and completion

Use the [testing plan](docs/superpowers/plans/2026-11-02-05-testing-acceptance.md) and [competition/real-world evaluations](docs/research/COMPETITION_METRICS_AND_REAL_WORLD.md). A01–A35, M01–M10, E01–E12, provider P01, and safety V01–V14 identify different checks; they are not pre-recorded passes or equivalent evidence levels.

- Run focused automated checks for changed behavior and affected contracts, plus the relevant manual acceptance steps. Do not add tests that merely mirror trivial edits. Record blocked/not_run checks with the actual missing prerequisite.
- Existing prototype scripts are `tests/prototype-v6.2.spec.cjs` and `tests/prototype-v6.3.spec.cjs`. With a compatible existing Playwright/Chromium installation, use:

  ```bash
  node tests/prototype-v6.3.spec.cjs
  # If Playwright is supplied outside normal Node resolution:
  PLAYWRIGHT_MODULE=/absolute/path/to/playwright/package node tests/prototype-v6.3.spec.cjs
  ```

  Optional `CHROMIUM_EXECUTABLE` selects the browser. Inspect the script before running: it can write screenshots/sample PDFs. These are UI scenario checks, not scanner/model/platform tests. Select the script matching the artifact changed; do not reuse machine-specific cache paths as portable setup instructions.
- Backend/Compose commands in plans are future targets until their manifests, dependencies, and files actually exist. Do not invent successful `pytest`, `npm`, migration, or Compose results. Pin dependencies/tool/image versions during implementation and record what was installed or changed.
- For docs-only work, check English copy, local links, preserved source/hash references, code fences, document identity, and cross-document consistency. Do not rerun scanners/models or broad browser suites for an unrelated prose change.
- Native/public/synthetic fixtures must retain their provenance labels. Metrics need exact numerator/denominator, dataset/version, exclusions, and verification level. No claimed judge score, low false-positive rate, speedup, or production readiness without the corresponding evidence.
- Use isolated test projects/volumes/DBs. Never remove user data/volumes or change firewall/network rules incidentally. Pilot admission additionally needs the documented access, retention, diagnostics, consistent backup, and tested restore gates.

Before finishing, inspect changes and report: what changed and why; exact checks actually run; pass/fail/blocked/not_run results; evidence paths/IDs/hashes where relevant; and remaining limitations/dependencies. Keep task progress, runtime availability, and evidence level separate. State completion only for the assigned deliverable, not for the entire planned platform.
