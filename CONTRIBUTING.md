# Contributing to Reknyx

Read the [README](README.md), [architecture](docs/architecture/README.md), [project structure](docs/architecture/STRUCTURE.md) and [agent rules](AGENTS.md). This guide is self-contained; ignored research/plans/prototypes and local skill packages are optional context, not setup dependencies.

## Current setup

The Next.js frontend has explicit synthetic preview and authenticated API modes. Use the [frontend guide](frontend/README.md) and existing npm lockfile. The [backend guide](backend/README.md) describes the implemented foundation and isolated PostgreSQL tests. The import/report worker is implemented; AI provider and scanner services remain planned; do not invent successful results for them.

## First implementation milestone

Start with executable OpenAPI schemas, examples, semantic checks and FE/BE review. Reconcile the existing browser routes with server state, including global workspace totals, immutable snapshot preview, retry/status responses, richer domain types and session/replay rules. Generated types consume the frozen contract; handwritten preview types do not define it.

Then implement authenticated persistence/artifact storage, connect existing assessment/messages UI, and complete one import → observation/finding → review → immutable PDF workflow. Keep preview/API modes explicit. Enable later AI/live capabilities only after their own implementation and acceptance evidence.

## Working by engineering role

Use the cybersecurity domain names and ownership map in the structure guide. AI work belongs in `security_analysis/` and its evaluation cases; state affected prompt/provider/schema versions and grounding/unknown/failure behavior. Security work belongs in `assessments/`, `scope_control/`, `scanner_integrations/` and `findings/`; state scope/profile/parser assumptions, source provenance, deny cases and execution consequences. Platform work belongs in `infrastructure/`, `orchestration/` and `evidence/`; assembly/dependency wiring uses `main.py` and `api/`, and report work belongs in `reporting/`. Changes should identify state transitions, ownership, migration or contract impact and evidence links.

Keep the one Alembic graph under `backend/migrations/`, deployment configuration under `deploy/`, and local Compose in `docker-compose.yml`. Keep backend workflow acceptance under `backend/tests/e2e/`, model cases under `backend/tests/evals/`, and browser checks in `frontend/tests/`. `shared/` is restricted to small pure domain-neutral types/errors. One writer owns each shared file. Scope work by domain and coordinate changes to executable contracts, dependencies, migrations and app wiring. The user appoints frontend contributors. Delegation and runtime AI roles are different; a role table does not authorize new development agents or infrastructure.

## Tests and evaluations

The existing frontend scripts are:

```bash
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

The browser suite needs compatible Playwright Chromium and loopback port 3100; it writes ignored screenshots/traces/sample PDFs. These are preview checks, not backend/scanner/model verification. Separate actual-HTTP checks are required once API integration exists.

Backend tests must use isolated PostgreSQL databases/volumes where database semantics matter. Keep source fixtures and their provenance in Git only when permitted; keep sensitive raw results and generated output private/ignored. Tests may not contact live targets or paid providers by default. Real provider evaluation is explicit, budgeted and records the actual dataset/version, numerator/denominator, prompt/configuration and failure results.

Evaluate model grounding, valid evidence references, scope/action applicability, unknown handling, malicious-evidence resistance and graceful provider failure separately from parser fidelity and authorized live scanner execution. A synthetic fixture is not a native capture; a valid schema is not a grounded conclusion; a generated report is not a verified assessment.

The [CI workflow](.github/workflows/ci.yml) runs the offline contract gate, frontend
checks and a disposable Compose/browser integration lane. See [backend setup](backend/README.md#ci-and-disposable-container-verification)
for local prerequisites and the exact runner. The [staging setup](backend/README.md#vultr-staging-preparation)
uses a separate image-only configuration and read-only preflight. CI does not publish,
deploy, run scanners or call model providers. Hosted CI, container execution, remote
TLS and operational recovery each require their own actual results.

## Reporting a change

State the problem and resulting behavior, affected paths/interfaces, exact checks actually run, outcomes and evidence level, and remaining dependencies. Distinguish planned/implemented/locally verified/integrated behavior from runtime availability. Do not claim judge scores, production readiness, calibrated confidence or efficiency without corresponding evidence.

For documentation/Git-policy changes, check tracked links, document identity/fences, ignore behavior, index state and preservation of local files. Do not rerun scanners/models or broad browser suites for prose or ignore-rule edits. Do not commit, push, publish or deploy unless requested.

## Local sources and requirements

Original requirements/research and detailed implementation records may be available locally but are not distributed with the overview docs. If a requirement decision depends on a missing original source, obtain it rather than inferring organizer permission or inventing a rule; independent implementation can continue within known constraints. The historical local `1.pdf` baseline is SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

Competition evidence still needs a conversational request/auditable plan, three working integrations or supported imports covering network/web, source-linked findings/risk/review, professional PDF and explicit approval before offensive validation. Organizer-provided scope/ROE and accepted validation outcomes remain external prerequisites; no documentation grants authorization.
