# Reknyx Security Overview

Reknyx is an analyst-controlled assessment assistant. **The current preview cannot execute scanners or offensive validation.** This overview states constraints for implementation, not authorization for any target.

## Scope, execution and evidence

- Execute only against explicitly authorized targets. The initial live target model is one exact IPv4 asset with explicit TCP ports; ZAP baseline additionally needs origin-wide web authorization. Historical imports may contain broader identities without authorizing traffic.
- Derive actors from authenticated server context. Scope edits change version/hash and invalidate affected proposals/grants. Exact human approval is required before active exploitation/offensive validation; no such adapter is currently enabled.
- Accept catalog profiles and typed bounded parameters only. Independent policy controls all dispatch; the trusted launcher rechecks final start authorization after network preparation and consumes the grant once. API/planner/worker/scanner have no raw Docker socket.
- Prove egress allow/deny behavior for each supported topology. Never blindly rescan an uncertain attempt after timeout, crash, lease expiry or restore; reconcile exact identity or expose `execution_unknown`. Traffic already sent cannot be revoked retroactively.
- Preserve original bytes before parsing, with SHA-256/provenance/timestamps/locators. Block XML entities, unsafe paths and evidence-supplied renderer resources. Keep private artifacts and secrets out of Git, prompts, ordinary logs and public downloads.
- Keep source facts, AI inferences, validation status, analyst disposition and contextual priority distinct. Open services are not automatically vulnerabilities; correlation cannot merge solely by title/CVE. Unknown values remain unknown.
- Reports freeze consistent state and include executive scope, methodology/ROE, severity/priorities, detailed evidence, impact/remediation and limitations/approvals/failures/timestamps. A ready PDF is not automatically a client-ready assessment.

## Untrusted inputs and authority

Treat scanner banners/HTML/XML, uploaded files, analyst messages and model output as untrusted input. Keep typed bounded inputs and independent schema/semantic checks across the API, AI output, native parser and worker seams. No model/client controls shell, executable, raw argv, image/mount/network selection or arbitrary SQL. Scope records and human grants are server-owned.

`assessments/` records scope revisions and conversations; `scope_control/` enforces permissions and exact approval/dispatch rules. `security_analysis/` proposes grounded interpretations/actions. Canonical `findings/` preserves source facts and memberships; `evidence/` preserves original bytes and provenance. Neither a confident model response nor analyst acceptance alone establishes a confirmed vulnerability.

## AI and operational controls

Bound context and provider requests by approved destination/data use and budget. Preserve provider attempts/failures and label deterministic fallback; do not silently send evidence to another provider. Record prompt/configuration/schema versions, source IDs and unknowns for each decision. Paid evaluations and live scanner runs are explicit opt-in work, not default test behavior.

Use isolated test databases/volumes and private configured artifact storage. Never change unrelated user data, firewall/network rules or secrets incidentally. `deploy/launcher/` is a later narrow trusted-host interface, not a Docker socket mount into API, AI or worker. Backup/restore, retention, diagnostics and operator admission are separate pilot gates.

## Verification boundary

Synthetic fixtures, public format references, authorized native captures, local integration, actual provider evaluation, authorized scanner execution and operational pilot evidence are distinct. Scope/approval tests with fake runners cannot prove a real offensive-validation outcome. No result or path in this overview closes those gates.

See the [architecture](../architecture/README.md), [API overview](../api/README.md), [decision register](../decisions/README.md) and [contributor guide](../../CONTRIBUTING.md).
