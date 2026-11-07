# Reknyx API Overview

**Status:** [contract candidate 0.1.0](../../contracts/README.md) and an initial authenticated backend foundation are implemented. Admin approved both owner reviews; G0 executable verification is recorded against that approved hash. The backend supports sessions, assessments, messages, audit, private artifacts, Nmap/ZAP import, finding review, frozen report snapshots and draft PDF downloads. Planner and scanner execution remain planned. See [backend setup](../../backend/README.md).

## Contract authority

[`contracts/openapi.yaml`](../../contracts/openapi.yaml) and its validated examples define the candidate external interface. The backend validates requests against that candidate; the API-mode frontend consumes generated TypeScript declarations and runtime-validates response schemas. [Contract setup and checks](../../contracts/README.md#run-offline-verification) are independent of running application services.

The intended HTTP base remains `/api/v1`. The folder changes do not themselves add or rename HTTP resources. Do not invent endpoint aliases to match component names.

## HTTP organization

`backend/src/reknyx/main.py` assembles the app. `api/router.py` registers domain routers, and `api/dependencies.py` derives authenticated context and injects dependencies. Domain modules own behavior and authorization; API wiring does not bypass them. `shared/` holds minimal reusable pure types/errors, not another schema or business-logic authority.

The contract must cover sessions/capabilities; assessments/scope/conversations; analysis/plans/decisions; proposals/approvals; imports/executions/jobs; observations/findings/review; evidence; immutable report snapshots/downloads; and audit. Workspace/global list projections need complete authorized pagination/totals. All names, request fields and error details are frozen during executable contract authoring.

## State and mutation rules

Derive actor identity from the authenticated session and protect mutations with the reviewed session/CSRF/origin design. Every read/write/download verifies assessment ownership. Use bounded pagination, explicit state/scope/finding revisions, server-computed hashes and replay protection for side-effecting creation.

Message append never invokes inference. Explicit analysis/planning, approval, execution and cancellation are separate operations. A grant cannot override scope or an unavailable capability. Report creation freezes a consistent revision and queues rendering; ready-only downloads serve stored bytes. Import/report jobs do not consume scanner grants.

Keep scheduler job state, scanner execution state, parser import state, approval state, technical validation, analyst disposition and report state separate. Runtime/dependency failures remain errors, not planned capabilities or synthetic success. API mode never silently falls back to fixture state.

## Frontend integration

Keep existing route URLs. During implementation, `frontend/src/lib/` holds the typed HTTP client, generated DTOs, response validation/mapping and explicit preview/API support. Features consume those interfaces; route and shared presentation files do not manufacture server state. Select `NEXT_PUBLIC_REKNYX_MODE=api` with a fixed server-only `REKNYX_BACKEND_ORIGIN`; preview remains the default. API failures remain errors.

See the [architecture](../architecture/README.md), [structure](../architecture/STRUCTURE.md), [security rules](../security/README.md) and [contributor guide](../../CONTRIBUTING.md). Only executable validation and actual integration results can establish API readiness.
