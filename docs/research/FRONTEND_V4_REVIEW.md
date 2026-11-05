# CoreVAPT frontend v4 — scope review

> Historical analysis. V3/V4 HTML files are absent from the current checkout. Use [prototype 6.2](../../corevapt_frontend_v6.2.html) and [current requirement/UX](FRONTEND_V6_2_REQUIREMENTS.md) for new work. Historical verification below is not a current runtime claim.

The historical V4 prototype adapted V3 to the platform described in [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md) and [TECHNICAL_RECOMMENDATIONS.md](TECHNICAL_RECOMMENDATIONS.md). The visual foundation was retained; that revision focused on product responsibilities and analyst workflows. Both V3/V4 source files have since been removed. This historical review and its 2026-11-02 checks were not rerun during the English documentation audit. Current prototype: [v6.2 requirements](FRONTEND_V6_2_REQUIREMENTS.md), with v6.1 retained as predecessor.

## Fit assessment

| V3 element | Decision | V4 behavior / reason |
| --- | --- | --- |
| Assessment, asset, finding, evidence, approval and audit views | Keep | These support the request-to-report VAPT workflow. |
| Generic security operations dashboard and historical activity charts | Replace | Assessment overview shows counts derived from its own scenario records; no invented observation totals or percent completion. |
| Findings from web, API and legacy assessments mixed into one report | Change | Selected assessment filters observations, artifacts, findings, actions, audit and snapshots. New drafts start empty. |
| No conversational request | Add | Request captured at creation and editable in the planner. Scenario proposal branches on existing HTTP service evidence; no claim that free text is interpreted by a model. |
| HTTP/open-port discovery as a vulnerability | Separate | Service observations appear in scope/services and evidence, excluded from finding counts. |
| Unsupported high/critical severity and numeric CVSS examples | Change | CSP scenario uses a labeled illustrative severity; uncertain component severity/CVSS stays Unknown. Confidence, priority, exposure, impact and validation are separate fields. These are not calibrated scanner outputs. |
| Cross-tool consolidation asserted without review | Add | Same-asset/location/weakness CSP candidate can be linked or kept separate; historical timing uncertainty and member observations remain visible. Cookie finding remains distinct. |
| Review button without rationale | Change | Reviewed observation / needs review / false positive require a rationale; original observations remain available. Review does not confirm exploitation. |
| All scanner coverage shown as completed | Change | Full seven-tool matrix retains Planned/Unsupported workspace status. Execution timeline explicitly labels illustrative completion, timeout and historical import scenarios. |
| Approval based mainly on target name | Change | Local decision checks target, exclusions, allowed profile, scope version, evidence ownership, exact payload and expiry. Denial remains possible for blocked proposals. Approval never dispatches work. |
| Placeholder checksum and integrity totals | Remove | No raw artifacts supplied; checksum, parsing and integrity remain unverified. Metadata references expose source locators and collection timestamps. |
| Partial executive report with implied included sections | Expand | Explicit snapshot includes all six required sections, per-finding evidence chain, remediation, unknowns, timeout and human decision limitations. |
| Print view based on changing live browser state | Change | Explicit deep-copy snapshot remains unchanged by later triage; replacing it requires an explicit button. Print and JSON export use that snapshot. |
| Broad global search / export labels | Narrow | Search and exports explicitly apply to current assessment findings, manifest or local audit. |

## Prototype boundary

Implemented here: navigation, assessment selection/creation, request storage, evidence-driven scenario branch, correlation membership review, triage rationale, local approval/denial with invalidation scenarios, metadata lineage, frozen report preview, scoped downloads and browser printing. State lives only in page memory; reloading resets it.

Not implemented: a model, real scan execution, native XML upload/parser, raw artifact storage/checksums, authenticated reviewers, worker/network scope enforcement, cryptographic approval binding, durable audit, database persistence, server-rendered downloadable PDF or E2E scanner validation. Local payload comparison demonstrates exact-action binding but is not a security boundary. A permission reference or checkbox is not independently verified authorization.

The three intended integrations remain Nmap live, ZAP live and Greenbone native XML import. Integration readiness follows the current research baseline. No fictional scenario counts toward the requirement for three working integrations/imports.

Historically, V4 opened directly in a browser without a server, package installation, or external network access. The original review preserved V3 at that time; both historical HTML files are absent from the current checkout.

## Historical local verification — 2026-11-02, not rerun

- Inline JavaScript parsed successfully in Node.js.
- Headless Chromium exercised all 11 navigation views, assessment isolation, correlation linking, triage with rationale, approval with no execution, draft creation, scoped CSV download and snapshot immutability.
- Excluded/unsupported actions were unavailable for approval; stale scope, changed payload and expired action scenarios were blocked.
- Desktop (1440 px) and mobile (390 px) checks found no horizontal page overflow; mobile navigation opened and closed.
- Browser printing produced a PDF; text extraction found each section 7.1 through 7.6. This verifies the local print path, not a server-generated report or production pagination quality.
- No page errors or external network requests were observed during the workflow checks.
- A separate historical code review found no important functional defects within its stated frontend scope. The later [V4 analysis](FRONTEND_V4_ANALYSIS.md) recorded request, local-policy, ranking, and count-semantics gaps; this earlier review is not evidence those platform capabilities worked.
- SHA-256 comparison confirmed the source v3 file was unchanged.

These checks validate prototype interactions only. No scanner, model, parser or platform E2E behavior was tested.
