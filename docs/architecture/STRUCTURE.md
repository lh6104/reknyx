# Reknyx Repository Structure

This is the canonical project layout, following the user-approved cybersecurity modules. `reknyx/` denotes the project root; the current local checkout is still named `dataops-research`. The frontend supports explicit preview/API modes; the backend implements the initial import/review/report workflow.

## Final implementation layout

The backend foundation and executable contract candidate now exist. The import/report worker and local deployment files exist; additional folders below remain **planned** unless present in the checkout.

```text
reknyx/
├── backend/
│   ├── src/
│   │   └── reknyx/
│   │       ├── main.py                  # Application composition and ASGI entry
│   │       ├── api/
│   │       │   ├── router.py            # Assemble versioned domain routers
│   │       │   └── dependencies.py      # Trusted request context and dependencies
│   │       ├── assessments/             # Assessment, scope revisions and conversation
│   │       ├── security_analysis/       # AI evidence analysis and assessment planning
│   │       ├── scope_control/           # Scope/capability/approval/dispatch authority
│   │       ├── scanner_integrations/    # Native formats and bounded scanner profiles
│   │       ├── evidence/                # Immutable source bytes and provenance
│   │       ├── findings/                # Observations, correlation, risk and review
│   │       ├── reporting/               # Frozen snapshots and bounded PDF rendering
│   │       ├── orchestration/           # Durable worker jobs, attempts and recovery
│   │       ├── infrastructure/          # Configuration, DB, auth, audit and storage adapters
│   │       └── shared/                  # Small domain-neutral types and errors
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/                        # API/worker/evidence/report acceptance
│   │   ├── evals/                      # Security reasoning and grounding cases
│   │   └── fixtures/                   # Permitted provenance-labelled source cases
│   ├── migrations/                     # One Alembic migration graph
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                        # Routes/layouts; keep current URLs
│   │   ├── features/                   # Assessment/findings/reporting feature behavior
│   │   ├── components/                 # Shared presentation and overlays
│   │   ├── hooks/                      # Reusable UI hooks
│   │   └── lib/                        # Client, generated DTOs, mapping and preview state
│   ├── tests/                          # Existing preview and later actual-HTTP browsers
│   ├── package.json
│   └── package-lock.json
├── contracts/                          # Executable interface authority; required addition
│   ├── openapi.yaml
│   ├── examples/                       # Valid/invalid cases and canonical hash vectors
│   └── README.md
├── docs/
│   ├── architecture/
│   │   ├── README.md                   # System and AI workflow overview
│   │   └── STRUCTURE.md                # This layout and responsibility map
│   ├── api/README.md                   # Interface principles and contract status
│   ├── security/README.md              # Scope, approvals, evidence and AI trust
│   └── decisions/README.md             # Concise decision register
├── scripts/                            # Setup/contract/evaluation helpers when implemented
├── deploy/                             # Environment and operational configuration
│   ├── lab/                            # Later authorized topology configuration
│   └── launcher/                       # Later narrow trusted-host launcher
├── .github/workflows/                  # CI once its real commands exist
├── .env.example                        # Safe configuration template, no credentials
├── docker-compose.yml                  # Local FE/API/worker/PostgreSQL setup
├── AGENTS.md
├── CONTRIBUTING.md
└── README.md
```

`contracts/`, AI evaluation cases, permitted fixtures and dependency lockfiles keep executable interfaces, security reasoning checks and reproducible dependencies in source control. The backend uses `uv` and its lockfile; other planned services still need their own pinned dependencies.

## Module interfaces and ownership

| Module/path | Owns | Must delegate |
| --- | --- | --- |
| `main.py`, `api/` | App wiring, router assembly, authenticated request dependencies and HTTP mapping | Domain decisions remain in their domain modules |
| `assessments/` | Scope/request/conversation records and revisions | Enforcement to scope control; inference to security analysis |
| `security_analysis/` | Bounded evidence context, analysis/planning, output validation, model providers and runtime prompts | Execution authority, canonical facts and human disposition |
| `scope_control/` | Scope/capability policy, exact grants, dispatch/start authorization | Actual process launch to the trusted launcher |
| `scanner_integrations/` | Native parsing and fixed supported scanner profiles | Private storage and durable job lifecycle |
| `evidence/` | Byte integrity, manifests, source locators and authorized access | Storage-specific IO through infrastructure adapters |
| `findings/` | Observations/memberships, defensible correlation/risk and analyst review | Raw evidence mutation and unsupported model claims |
| `reporting/` | Consistent snapshots, template/render rules and report outcomes | Durable render scheduling to orchestration |
| `orchestration/` | One worker's claims, import/scan/report jobs, attempts and recovery | Domain policy, parsing and report logic |
| `infrastructure/` | Typed configuration, DB sessions, authentication, audit, idempotency and concrete IO adapters | Assessment policy and vulnerability reasoning |
| `shared/` | Minimal pure types/errors used by multiple modules | Domain models, provider prompts, orchestration and infrastructure state |

Keep `shared/` small and independent of domain modules; it is not a general utilities or business-logic directory. Domain schemas and mappings must consume the reviewed executable contract without introducing a competing schema authority.

AI engineers primarily work in security analysis and evaluations. Cybersecurity engineers primarily review assessments, scope control, scanner integrations and findings. Platform engineers own infrastructure, orchestration, evidence IO, migrations and deployment wiring. The user-appointed frontend owner handles frontend work; report/QA owners verify reporting and cross-module traceability. Shared files each have one writer.

## Frontend organization

Keep the existing application working while wiring it. Route entry points remain in `app/`; new domain UI behavior can move into `features/` incrementally under frontend ownership. Shared components stay in `components/`; reusable hooks belong in `hooks/`. Put HTTP clients, generated interface types, validation/mappers and explicit preview/API state support under `lib/`. Existing pure fixture/rule helpers remain there until a concrete feature change warrants moving them.

The current frontend has `app/`, `components/` and `lib/`; `features/` and `hooks/` are not yet created. No bulk source move is part of structure finalization.

## Current checkout and Git policy

Implemented locally: frontend preview, contract candidate, backend foundation, one migration graph, Dockerfile and focused tests. Root environment template, local Compose and an import/report worker now exist. CI and production deployment remain implementation targets. Backend workflow checks belong under `backend/tests/e2e/`; browser workflows remain in `frontend/tests/`. No separate root acceptance framework is introduced by this layout.

The chosen names are `main.py`, `api/router.py`, `api/dependencies.py`, `backend/migrations/`, `deploy/`, and `docker-compose.yml`. Earlier local plans naming different paths are historical context, not the current directory contract.

Keep code, runtime prompts, executable schemas, allowed source fixtures, tests and lockfiles in Git. Ignore detailed research/implementation/Superpowers notes, prototypes, original PDFs, local skills, private evidence and generated run/evaluation output. `.gitignore` allowlists only the overview files in these documentation folders. Local ignored records remain on disk and are not required to read the tracked docs or run the preview.
