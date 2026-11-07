# Reknyx Agent Instructions

Applies to the repository unless a subtree has more specific instructions. Follow the user's explicit task and system/developer instructions first. Repository guidance authorizes no scans, paid calls, external messages, publication or deployment.

## Start here

Read [README.md](README.md), [architecture](docs/architecture/README.md), [structure](docs/architecture/STRUCTURE.md), [API overview](docs/api/README.md), [security overview](docs/security/README.md) and [contributor guide](CONTRIBUTING.md), then inspect actual files and Git state with `rg`/`rg --files`. Do not infer implementation from a filename, plan or screenshot. The current app is a synthetic Next.js preview; backend, native parsers, providers, scanners and backend PDF remain unimplemented until actual evidence says otherwise.

Tracked guidance must work without ignored research, Superpowers plans, prototypes or copied local skill packs. They remain optional local context, not required onboarding. Their historical paths/plans may be stale; current reviewed contracts and actual code take precedence. For version-specific Next.js edits, consult the installed package's `node_modules/next/dist/docs/` guidance.

If changing requirements/architecture/acceptance and the supplied source is available, review the relevant `1.pdf` sections (all ten pages for a broad review) and verify SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`. Disclose a changed source. If it is absent and necessary to decide a requirement, request that source; do not manufacture rules or permissions. Continue independent work where possible.

## Architecture and ownership

- Keep FastAPI modular monolith, PostgreSQL canonical state, a separate worker from the same package, private immutable artifacts and initial HTTP polling. Add no broker, graph/vector DB, Kubernetes or runtime agent mesh without a demonstrated requirement and reviewed design change.
- The planned AI module is `backend/src/reknyx/security_analysis/`: evidence context, evidence analysis, assessment planning, output validation, model providers and runtime prompts. It proposes; independent `scope_control/`, native `scanner_integrations/`, canonical `findings/`, `evidence/`, `orchestration/` and `reporting/` enforce their own responsibilities. `assessments/` owns scope/conversation state and `infrastructure/` supplies authentication, database and audit support. Use `main.py` and `api/router.py`/`api/dependencies.py` for assembly/request seams. Keep `shared/` small, pure and domain-neutral. The single Alembic graph belongs under `backend/migrations/`; operational configuration belongs under `deploy/` with root `docker-compose.yml`. Keep these names consistent across guidance and future implementation.
- G0 executable schemas/examples/semantic checks/hash vectors and FE/BE review precede contract-dependent implementation. Pure parsers/renderers can use agreed labelled fixtures. No mock, healthy API or browser print establishes platform acceptance.
- The user appoints frontend contributors. Do not replace that assignment or modify frontend during unrelated backend work. Keep current routes/design and truthful capability states.
- One writer owns each shared contract, app/config file, dependency/lockfile and migration graph. Module owners submit coordinated changes; use isolated test DBs and do not concurrently migrate one DB.
- Use development subagents only when explicitly authorized or an applicable skill calls for them. Check prerequisites and independent owned paths; review returned work. Role tables do not authorize delegation.
- Preserve existing user changes. Do not initialize Git, reset/clean/revert other work, commit, push, merge, publish or deploy as an incidental action. Untracking a requested local asset preserves its working copy.

## Security, AI and provenance invariants

- Only explicitly authorized targets/ROE permit execution. Public sample addresses, checkboxes, natural language and generated text are not authorization. Project-owned local testing and the organizer-scored lab are separate contexts.
- Initial live scope is one dedicated IPv4 asset with explicit TCP ports; ZAP baseline requires origin-wide web authorization. Historical imported identities can be broader without enabling live traffic. No active/offensive validation is implied by baseline profiles.
- Accept catalog profiles and bounded typed parameters only. No model/client shell, argv, executable/image/mount/network selector or arbitrary SQL authority. Actor identity comes from authenticated server context.
- Approval binds exact action/profile/parameters, target, scope version/hash, expiry and budget; it never overrides deny or unsupported capability. `authorize_dispatch` reserves attempt/grant/budget; trusted launcher `authorize_start` rechecks after preparation and consumes once under the same scope serialization. Preparation is not scanner start; retain the physical-start/revocation limitation.
- API/planner/worker/scanner receive no raw Docker socket. Use a narrow trusted launcher and assessment-bound egress enforcement; local/routed topologies need separate allow/deny evidence. Profile-owned flags/ports must match pinned tools/network rules.
- Never blindly rescan after timeout, lease expiry, crash or restore. Reconcile exact attempt/fence/process/receipt; expose `execution_unknown` if unresolved. Reparse immutable bytes without rescanning when safe.
- Store raw bytes before parsing; retain SHA-256, source, observed/ingested timestamps, parser version and locator. Do not overwrite evidence, resolve untrusted XML entities/URLs, or accept client filesystem paths. Reconcile DB/filesystem publication gaps honestly.
- Scanner banners, HTML, imports and model output are untrusted data. Independently validate schema, references, assessment ownership, revisions, applicability, preconditions and budgets. Models do not receive direct execution authority or raw sensitive evidence without destination/data-use coverage.
- Keep observations separate from canonical findings; open services are not automatically vulnerabilities. Correlation retains all memberships/sources and cannot merge solely by title/CVE: asset/service/location/time/rule meaning matter.
- Preserve source severity/CVSS vector/version/source, confidence method, technical validation, analyst disposition and contextual priority separately. Unknown stays unknown; never fabricate CVEs, proof, calibrated probabilities or numeric risk scores.
- Message append does not invoke inference. Explicit plan/analysis and side-effecting creation use the frozen replay/idempotency rules. Preserve provider failures and labelled deterministic fallback; no silent provider switch or evidence transmission.
- Reports render immutable consistent snapshots with scope, methodology/ROE, severity/priorities, detailed source evidence, impact/remediation and limitations/approvals/failures/timestamps. A ready PDF is not automatically client-ready. Approval-control tests/fake runners do not prove an offensive validation outcome.
- Keep secrets/private raw data out of Git, browser storage, prompts, reports and routine logs unless the specific destination/use is covered. Existing authorization persists; research does not authorize paid generation, scans or messages. Never alter user data/volumes/firewall/network settings incidentally.

## Git and documentation policy

Only README/setup/contributing and the allowlisted architecture/API/security/decision overviews plus the structure guide are reader-facing tracked documentation. Keep root AGENTS.md for portable agent rules. Detailed research/implementation/Superpowers docs, original PDFs, standalone prototypes, copied local skills and generated evidence remain ignored locally. Do not force-add them. Runtime prompts, executable contracts, sanitized permitted fixtures, tests and dependency lockfiles remain source and should be versioned.

Project-authored copy/comments are English; user conversation may be Vietnamese. Preserve real source bytes/identifiers and deliberate multilingual fixtures. Preview is labelled synthetic; planned capabilities show “In development” with disabled mutations. Connection errors remain errors with no silent mock fallback, invented success or progress. Defaults do not revise existing scope or authorize an action.

## Verify and finish

Run focused checks appropriate to changed behavior/contracts and relevant manual steps. Report exact commands and pass/fail/blocked/not_run with missing prerequisites and evidence level. No successful backend/migration/Compose/model/scanner command may be invented before the actual setup exists.

For docs/ignore/index changes, verify tracked links, identities/fences, ignore rules, intended index removals and preserved local hashes. Do not run unrelated broad suites. For code, keep unit, schema, native parser, local integration, real-provider, authorized-live and pilot evidence distinct. Metrics need dataset/version, exact numerator/denominator, exclusions and execution level.

Use isolated test projects/DBs/volumes. Retention/access/diagnostics/consistent backup/tested restore are separate pilot gates. Before claiming completion, inspect the actual diff and state what changed, what ran, and remaining limits; complete only the assigned deliverable.
