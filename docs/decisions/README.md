# Reknyx Decision Overview

This is a concise register of current project direction. It is not an implementation plan or evidence that a planned capability works. Detailed local planning/research and run output remain ignored.

| Decision | Current direction | Verification boundary |
| --- | --- | --- |
| Repository layout | User-approved cybersecurity modules, `main.py`/`api/`, `shared/`, `backend/migrations/`, `deploy/`, `docker-compose.yml` | Initial backend foundation and migrations implemented; import/report worker and local Compose exist; production deployment remains pending |
| Application shape | Existing Next.js frontend; planned FastAPI modular monolith, PostgreSQL, one separate worker and private evidence storage | Explicit preview/API modes; local import/review/draft-PDF workflow verified with synthetic evidence |
| Interface authority | Versioned executable OpenAPI/examples at `contracts/`; generated consumers | G0 offline verification passed against the recorded owner-approved hash; runtime acceptance is separate |
| AI authority | `security_analysis/` proposes evidence-grounded analysis and next actions; independent scope control and human review govern authority | Bounded local review and Groq adapter implemented; fake-transport tests do not establish real-provider evaluation |
| Evidence model | Immutable original bytes, source observations, canonical memberships/findings and attributed review; report snapshots are frozen | Nmap/ZAP/Greenbone import and reporting verified with synthetic evidence; native-capture acceptance remains separate |
| Initial integrations | Bounded Nmap discovery, AF-only origin-wide ZAP baseline, Greenbone native XML import | No live/import integration is enabled by the preview; source/runtime/provenance gates remain |
| Documentation policy | Reader-facing architecture/API/security/decision overviews plus structure/setup/agent guidance | Detailed plans, prototypes, PDFs, local skills and generated evidence stay ignored |

## Changing a decision

Describe the concrete requirement or measured failure, the affected interface/modules, compatibility and ownership, and the corresponding validation. Change code/contracts and their examples together when implemented. Preserve historical source/run records without relabelling old results.

Do not infer a runtime agent mesh, new workflow engine, extra database or execution privilege from the folder layout. Domain roles and coding-agent assignments are different. No organizer permission, target scope, provider spending or production readiness is granted by this register.

See [structure](../architecture/STRUCTURE.md), [architecture](../architecture/README.md), [API](../api/README.md), [security](../security/README.md) and [contributing](../../CONTRIBUTING.md).
