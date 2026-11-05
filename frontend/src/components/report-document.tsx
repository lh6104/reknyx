import type { ReportSnapshot, Severity } from "@/lib/types";
import { displayTime } from "@/lib/preview-context";
import { Badge, DetailList, Notice, StateBadge } from "./ui";

const SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low"];

export function ReportDocument({ report }: { report: ReportSnapshot }) {
  const assessment = report.assessment;
  const findings = assessment.findings
    .filter((finding) => report.includeSuspected || finding.status !== "Suspected")
    .toSorted((a, b) => SEVERITIES.indexOf(a.severity) - SEVERITIES.indexOf(b.severity));
  const excluded = assessment.findings.length - findings.length;
  const pending = assessment.actions.filter((action) => action.state === "Pending");
  const failed = assessment.actions.filter((action) => action.state === "Failed");
  const approved = assessment.actions.filter((action) => action.state === "Approved");
  const declined = assessment.actions.filter((action) => action.state === "Declined");

  return <div className="report-copy min-w-0 break-words">
    <header className="mb-6 border-b border-line pb-6">
      <Badge tone="warning">Synthetic sample report</Badge>
      <h2 className="mt-4 text-[25px] font-extrabold tracking-[-.04em]">Vulnerability assessment report</h2>
      <p className="mt-1 font-bold">{assessment.name}</p>
      <p>Snapshot {report.id} · {displayTime(report.createdAt)}</p>
      <p>Analyst: {report.analyst}. Assessment: {assessment.id}, created {displayTime(assessment.createdAt)}.</p>
      <p className="mt-2">This frozen preview contains synthetic fixtures and any explicitly labelled preview attachments. No scanner, model, or backend produced this document. It is not a client-ready assessment.</p>
    </header>

    <section aria-labelledby={`${report.id}-summary`}>
      <h3 id={`${report.id}-summary`}>7.1 Executive summary</h3>
      <p>The recorded scope covers {assessment.target} ({assessment.ip}) on TCP ports {assessment.ports.join(", ")}. This snapshot contains {findings.length} finding(s), including {findings.filter((finding) => finding.status === "Suspected").length} suspected finding(s). Confirmation labels describe the synthetic observation; they do not establish live validation.</p>
      <p className="mt-2">Priority follows source severity in the order Critical, High, Medium, Low. CVSS and contextual risk scores are unknown. No numerical risk score is calculated.</p>
    </section>

    <section aria-labelledby={`${report.id}-method`}>
      <h3 id={`${report.id}-method`}>7.2 Scope and methodology</h3>
      <DetailList items={[
        ["Assessment request", assessment.request],
        ["Recorded permission", assessment.permissionRef || "Not recorded"],
        ["Target / IPv4", `${assessment.target} / ${assessment.ip}`],
        ["Allowed TCP ports", assessment.ports.join(", ") || "None recorded"],
        ["Rate / deadline", `${assessment.rate} / ${assessment.deadline} per action`],
        ["Exclusions", assessment.exclusions || "None recorded"],
      ]} />
      <p className="mt-3">Method: inspect labelled fixture observations, retain each source membership, separate observations from inference, and record analyst disposition. A permission reference is recorded context and does not verify authorization. Preview attachments are stored in memory as attachments; they are not parsed or executed.</p>
      {assessment.actions.length ? <div className="overflow-x-auto"><table><caption className="sr-only">Recorded method and action states</caption><thead><tr><th scope="col">Step / tool</th><th scope="col">Method / state</th><th scope="col">Rationale</th></tr></thead><tbody>{assessment.actions.map((action) => <tr key={action.id}><td>{action.id}: {action.title}<br />{action.tool}</td><td>{action.kind === "Import" ? "Historical import / fixture" : action.kind}<br /><StateBadge state={action.state} /></td><td>{action.why}{action.retryOf && <p>Retry proposal for {action.retryOf}; prior attempt retained.</p>}</td></tr>)}</tbody></table></div> : <p>No method steps have been proposed.</p>}
    </section>

    <section aria-labelledby={`${report.id}-severity`}>
      <h3 id={`${report.id}-severity`}>7.3 Severity distribution</h3>
      <div className="flex flex-wrap gap-2">{SEVERITIES.map((severity) => <Badge tone={severity} key={severity}>{severity}: {findings.filter((finding) => finding.severity === severity).length}</Badge>)}</div>
      <p className="mt-3">Severity is the preserved synthetic source label, separate from confidence, validation status, and analyst disposition. CVSS score, vector, version, and source are unknown; they have not been inferred from severity.</p>
    </section>

    <section aria-labelledby={`${report.id}-findings`}>
      <h3 id={`${report.id}-findings`}>7.4 Detailed findings and evidence</h3>
      {findings.length ? findings.map((finding, findingIndex) => <article key={finding.id} className="mt-4 rounded-xl border border-line p-4">
        <h4 className="text-[14px] font-extrabold">{finding.id}: {finding.title}</h4>
        <div className="my-3 flex flex-wrap gap-2"><Badge tone={finding.severity}>{finding.severity}</Badge><Badge tone={finding.status === "Suspected" ? "warning" : "neutral"}>{finding.status}</Badge><Badge>{finding.disposition}</Badge></div>
        <DetailList items={[
          ["Asset / location", finding.asset],
          ["Reference", finding.reference || "Unknown"],
          ["Source severity", finding.severity],
          ["CVSS", "Unknown score, vector, version, and source"],
          ["Confidence", `${finding.confidence} — fixture label; confidence method not supplied and probability not calibrated`],
          ["Validation status", `${finding.status}; no live validation in this preview`],
          ["Analyst disposition", finding.disposition],
        ]} />
        <p className="mt-3"><strong>Source observation:</strong> {finding.observation}</p>
        <p className="mt-2"><strong>Inference / potential impact:</strong> {finding.inference}</p>
        {finding.correlationNote && <p className="mt-2"><strong>Correlation:</strong> {finding.correlationNote}</p>}
        {finding.falsePositiveNote && <p className="mt-2"><strong>False-positive uncertainty:</strong> {finding.falsePositiveNote}</p>}
        {finding.reviewNote && <p className="mt-2"><strong>Analyst rationale:</strong> {finding.reviewNote}</p>}
        <p className="mt-3 font-bold">Source evidence ({finding.evidence.length})</p>
        {finding.evidence.length ? <ol className="mt-2 space-y-3">{finding.evidence.map((evidence, evidenceIndex) => {
          const evidenceId = `${report.id}-evidence-${findingIndex}-${evidenceIndex}`;
          return <li key={evidenceId} id={evidenceId} className="rounded-lg bg-soft p-3 text-xs">
            <a href={`#${evidenceId}`} className="font-bold underline decoration-line underline-offset-4">{evidence.tool}: {evidence.rawRef}</a>
            <p>Provenance: {evidence.provenance}. Observed: {displayTime(evidence.observedAt)}. Action: {evidence.actionId}.</p>
            <p>SHA-256: {evidence.sha256 || "Not supplied in synthetic source record"}.</p>
            <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-xs leading-relaxed">{evidence.excerpt}</pre>
          </li>;
        })}</ol> : <p>No source evidence is attached. This finding needs evidence review.</p>}
      </article>) : <p>No findings are included in this snapshot. This does not establish that the scope is free of vulnerabilities.</p>}
      {assessment.attachments.length > 0 && <div className="mt-4"><h4 className="font-bold">Preview attachments</h4>{assessment.attachments.map((attachment) => <p key={attachment.id} className="mt-2">{attachment.name} — {attachment.tool}, {attachment.size}. Preview attachment, not parsed. Attached {displayTime(attachment.attachedAt)}. SHA-256: {attachment.sha256}.</p>)}</div>}
    </section>

    <section aria-labelledby={`${report.id}-remediation`}>
      <h3 id={`${report.id}-remediation`}>7.5 Impact and remediation</h3>
      {findings.length ? <table><caption className="sr-only">Potential impact and recommended remediation by finding</caption><thead><tr><th scope="col">Finding</th><th scope="col">Potential impact / uncertainty</th><th scope="col">Remediation</th></tr></thead><tbody>{findings.map((finding) => <tr key={finding.id}><td>{finding.id}<br />{finding.severity}</td><td>{finding.inference}</td><td>{finding.remediation}</td></tr>)}</tbody></table> : <p>No finding-specific remediation is available.</p>}
    </section>

    <section aria-labelledby={`${report.id}-limitations`}>
      <h3 id={`${report.id}-limitations`}>7.6 Limitations and review history</h3>
      <Notice tone="warning">Synthetic frontend preview only. Scanners, model inference, active validation, and backend PDF generation are In development. Historical fixture completion does not show execution by Reknyx. Attachments are not parsed. A sample PDF does not establish assessment readiness.</Notice>
      <p className="mt-3">Frozen report options: suspected findings {report.includeSuspected ? "included" : "excluded"}; detailed audit trail {report.includeAudit ? "included" : "excluded"}. {excluded} suspected finding(s) excluded by these snapshot settings. Later settings or assessment changes do not update this snapshot.</p>
      <p className="mt-2">Pending approvals: {pending.length}. Approved but not executed: {approved.length}. Failed actions: {failed.length}. Declined actions: {declined.length}. An approval records an analyst decision; it does not authorize unsupported capabilities, execute a scanner, or confirm a finding.</p>
      {assessment.actions.filter((action) => action.state !== "Done").map((action) => <div key={action.id} className="mt-3 rounded-lg border border-line p-3"><p><strong>{action.id}: {action.title}</strong> — {action.state}</p><p>{action.why}</p>{action.output && <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-xs">{action.output}</pre>}</div>)}
      <p className="mt-3">Assessment approval and client release have not been established. Source completeness, real target behavior, vendor backports, and exploitability remain unverified. Sensitive production evidence should not be entered into this preview.</p>
      {report.includeAudit ? <><h4 className="mt-5 font-bold">Frozen audit trail</h4>{assessment.audit.length ? <table><caption className="sr-only">Timestamped assessment review and approval history</caption><thead><tr><th scope="col">Time / event</th><th scope="col">Detail</th></tr></thead><tbody>{assessment.audit.map((event) => <tr key={event.id}><td>{displayTime(event.at)}<br />{event.title}</td><td>{event.detail}</td></tr>)}</tbody></table> : <p>No audit events were recorded at snapshot creation.</p>}</> : <p className="mt-3">Detailed timestamped audit history was excluded by the frozen report preference. The action states and limitations above remain included.</p>}
    </section>
    <footer className="mt-6 border-t border-line pt-3"><p>Sample snapshot {report.id} · frozen {report.createdAt} · browser printing only</p></footer>
  </div>;
}
