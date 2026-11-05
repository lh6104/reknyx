# Reknyx frontend design

The user requests conversion of `reknyx_frontend_v7_4.html` into a Next.js and Tailwind CSS frontend using mock data. This is a new frontend application based on existing, concrete interaction flows. Their instruction to proceed authorizes local implementation. No publishing, backend, model calls, or scanner execution is included.

## Reference and decisions

- Preserve the V7.4 sidebar destinations: Dashboard, Assessments, Approvals, Findings, Reports, Settings. Preserve its search, notifications, contextual assistant, assessment creation, scope, plan, evidence, audit, and report flows. This user-selected HTML takes precedence over the historical V6.4 navigation inventory.
- Preserve the original HTML bytes. The new application lives in `frontend/`. This directory is not currently a Git checkout; do not initialize Git or create a worktree.
- Retain the six lifecycle meanings Scope → Plan → Collect → Analyze → Review → Report within assessment views.
- The palette follows the supplied design: background `#ececec`, surface `#ffffff`, ink `#141a14`, lime `#9fd04f`, muted `#626b62`, border `#e3e7df`. Use locally served Manrope; rounded white panels and hatched severity visualization match the source, rather than introducing a new visual identity. Mobile uses a compact header and accessible navigation drawer.
- Implement real App Router paths, typed React components, shared preview state, and Tailwind utility styling. No iframe, injected legacy scripts, invented API endpoints, or generated API types before G0.

## Preview behavior and corrections

All routes display a synthetic preview notice. Mutable assessment data is memory-only and resets on reload. Only non-sensitive preferences may persist locally, with a visible storage-failure message. The original contains numerical risk heuristics, approval-to-completion shortcuts, fake import success, and intended integration labels; these must not become implementation claims. Use severity-led ordinal priority and unknown CVSS, keep approval separate from execution, mark integrations In development, and attach preview files without claiming parsing. Fixture observations retain provenance and timestamps. The version banner remains a suspected issue, not a confirmed vulnerability.

Creation validates a single hostname, IPv4 /32 with valid octets, bounded integer TCP ports, request, permission reference, and an explicit preview acknowledgment. It creates an empty draft; generating a deterministic plan is a separate action. Messages, proposal generation, approval, and execution remain distinct. A failed attempt remains historical when a new retry proposal is added. Real start remains disabled.

The assistant is one deterministic assessment assistant, with no model connected. Messages are assessment-specific; explicit proposal generation validates target identity and avoids duplicate work. Unsupported active validation remains In development. Analyst decisions have rationale and audit entries; approval never confirms a finding.

Report drafts deep-copy the assessment and report preferences. Subsequent decisions do not rewrite an existing snapshot. Preview/print contains sections 7.1–7.6 with traceable synthetic evidence, unknown CVSS, approvals, failures, timestamps, and limitations. Browser printing is labeled Save sample PDF; backend PDF generation is disabled as In development.

## Verification

Use focused model tests for malformed scope, assessment isolation, approval/execution separation, retries, duplicate/out-of-scope proposals, and frozen reports. Use Playwright for navigation, search, creation, dialogs/focus restoration, evidence escaping, settings, report printing, mobile layout, dark mode, and absence of scanner/provider requests. Run TypeScript checks and a production build. Record actual outcomes separately from pending backend/G0/platform checks.

The mandatory PDF SHA-256 is unchanged: `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`. Relevant sections 4–7 and context were read. No competition or architecture requirement is changed by this preview.
