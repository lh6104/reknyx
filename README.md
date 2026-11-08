# Reknyx

Reknyx is an analyst-controlled AI assistant for authorized vulnerability assessment and penetration testing. It is designed to interpret scanner evidence, explain the next investigation, correlate findings, support human review, and produce a traceable report.

**Current status:** the frontend supports explicit synthetic preview and authenticated API modes. The Phase 1 import/review/PDF workflow has passed a real HTTP browser test with synthetic evidence. The backend supports authenticated assessment/message persistence, private artifacts, durable Nmap/ZAP/Greenbone import, attributed finding review and immutable draft PDF reports. G0 executable contract verification is recorded. Explicit evidence review supports labelled local deterministic review, an optional Groq adapter and independent minimum topic/reference coverage checks. A bounded synthetic Groq development benchmark has run; broader AI acceptance and scanner execution remain **In development**. See the [backend setup](backend/README.md) for worker commands and recovery limits.

## Run the current application

Requires Node.js 20.9 or later and npm. Versions are pinned in the frontend lockfile.

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. See the [frontend guide](frontend/README.md) for production and verification commands. Assessment data resets on reload; only non-sensitive preferences persist. Use synthetic data in this preview.

## Understand the project

| Read | Purpose |
| --- | --- |
| [Architecture and AI workflow](docs/architecture/README.md) | How evidence, AI analysis, policy, execution and review fit together |
| [Project structure](docs/architecture/STRUCTURE.md) | Existing code, target modules, engineering ownership and Git policy |
| [API overview](docs/api/README.md) | Interface authority, lifecycle and frontend integration |
| [Security overview](docs/security/README.md) | Scope, approvals, evidence and model trust |
| [Decision overview](docs/decisions/README.md) | Current architectural direction and pending gates |
| [Contributor guide](CONTRIBUTING.md) | How to develop, verify and describe a change |
| [Agent instructions](AGENTS.md) | Repository rules for coding assistants |

The intended workflow is authorized request/scope → evidence-led planning → permitted import/execution → normalization/correlation → AI analysis and risk review → human decision → immutable report. Models propose interpretations/actions; server policy and explicit grants control execution.

## Implementation direction

Keep the existing frontend and add a FastAPI modular monolith, PostgreSQL canonical state, a separate worker from the same backend package, and private immutable evidence storage. Organize the backend by cybersecurity responsibility: `assessments/`, `security_analysis/`, `scope_control/`, `scanner_integrations/`, `evidence/`, `findings/`, and `reporting/`, supported by `infrastructure/` and `orchestration/`. Use `main.py` and `api/` for assembly/request wiring, `shared/` for minimal pure shared types, `backend/migrations/` for Alembic, and `deploy/` with root `docker-compose.yml` for deployment setup when implemented. The security analysis module proposes evidence-grounded interpretations and next actions; scope control, scanner parsing, canonical findings and reporting enforce their own responsibilities.

The first implementation milestone is implemented: durable import → finding review → evidence-linked draft PDF, including real frontend/API wiring. Executable OpenAPI schemas and validated examples define the interface. Real provider evaluation and authorized live execution have separate prerequisites and evidence gates.

## What belongs in Git

Version application code, dependencies, executable contracts, runtime prompts, permitted test fixtures, tests, CI/runbooks when implemented, and the overview docs above. Detailed research, implementation plans, Superpowers documents, standalone prototypes, source PDFs, local skill packs, screenshots and evaluation/run outputs are ignored and retained locally.

Tracked docs are self-contained and do not require local planning files. Ignoring a path does not erase older Git history; this cleanup changes the next repository snapshot only. No backend or AI runtime is implemented by the repository cleanup.
