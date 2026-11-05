"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, FileText, ShieldCheck } from "lucide-react";
import { createAssessment, approveAction, retryAction, validateNewAssessment } from "@/lib/model";
import { displayTime, makeId, timestamp, usePreview } from "@/lib/preview-context";
import type { Assessment, NewAssessmentInput } from "@/lib/types";
import { Badge, Button, DetailList, Dialog, Field, Notice, StateBadge } from "./ui";

export function NewAssessmentDialog() {
  const { state, setState, close, notify } = usePreview();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [input, setInput] = useState<NewAssessmentInput>({ name: "", request: "", target: "", ip: "", ports: state.preferences.ports, permissionRef: "", acknowledged: false });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const change = (key: keyof NewAssessmentInput, value: string | boolean) => setInput((current) => ({ ...current, [key]: value }));
  useEffect(() => { document.getElementById(step === 0 ? "assessment-name" : step === 1 ? "target-hostname" : "tcp-ports")?.focus(); }, [step]);

  function next() {
    const allErrors = validateNewAssessment(input);
    const keys = step === 0 ? ["name", "request"] : step === 1 ? ["target", "ip", "permissionRef", "acknowledged"] : ["ports"];
    const relevant = Object.fromEntries(Object.entries(allErrors).filter(([key]) => keys.includes(key)));
    setErrors(relevant);
    if (Object.keys(relevant).length) return;
    if (step < 2) { setStep((current) => current + 1); return; }
    if (Object.keys(allErrors).length) { setErrors(allErrors); return; }
    const id = `AST-${String(state.assessments.length + 1).padStart(3, "0")}`;
    const assessment = createAssessment(input, state.preferences, id, timestamp());
    setState((current) => ({ ...current, assessments: [assessment, ...current.assessments] }));
    close(); router.push(`/assessments/${id}/plan`);
    notify("Empty preview assessment created. Nothing has run.");
  }

  return <Dialog title="New assessment" description={`Step ${step + 1} of 3 / ${["Describe the work", "Record the demo scope", "Set the limits"][step]}`} onClose={close}>
    <ol aria-label="Creation steps" className="mb-6 flex gap-2">{["Request", "Scope", "Limits"].map((label, i) => <li key={label} aria-current={step === i ? "step" : undefined} className="flex-1"><div className={`mb-2 h-1 rounded-full ${i <= step ? "bg-lime" : "bg-line"}`} /><span className={`text-[10px] ${i === step ? "font-bold" : "text-muted"}`}>{label}</span></li>)}</ol>
    <form onSubmit={(event) => { event.preventDefault(); next(); }} className="space-y-5">
      {step === 0 && <><Field htmlFor="assessment-name" label="Assessment name" error={errors.name}><input id="assessment-name" autoFocus maxLength={120} value={input.name} onChange={(event) => change("name", event.target.value)} placeholder="Customer portal review" /></Field><Field htmlFor="assessment-request" label="What should be assessed?" error={errors.request}><textarea id="assessment-request" rows={4} maxLength={3000} value={input.request} onChange={(event) => change("request", event.target.value)} placeholder="Review exposed services and common web configuration issues." /></Field></>}
      {step === 1 && <><Field htmlFor="target-hostname" label="Lab hostname" error={errors.target}><input id="target-hostname" maxLength={253} value={input.target} onChange={(event) => change("target", event.target.value)} placeholder="web.lab.example" autoCapitalize="none" autoComplete="off" /></Field><Field htmlFor="target-ip" label="IPv4 with /32" error={errors.ip}><input id="target-ip" value={input.ip} onChange={(event) => change("ip", event.target.value)} placeholder="192.0.2.30/32" /></Field><Field htmlFor="permission-reference" label="Permission reference" error={errors.permissionRef}><input id="permission-reference" maxLength={160} value={input.permissionRef} onChange={(event) => change("permissionRef", event.target.value)} placeholder="LAB-PERM-0042" /></Field><label className="flex items-start gap-2.5 text-xs leading-relaxed"><input type="checkbox" checked={input.acknowledged} onChange={(event) => change("acknowledged", event.target.checked)} className="mt-0.5" />I understand this is a synthetic preview. A recorded permission reference does not verify or authorize live testing.</label>{errors.acknowledged && <p role="alert" className="text-xs text-[#a4432c]">{errors.acknowledged}</p>}</>}
      {step === 2 && <><Field htmlFor="tcp-ports" label="Allowed TCP ports" error={errors.ports} hint="Integer TCP ports from 1 to 65535. No ranges, UDP, or additional hosts."><input id="tcp-ports" maxLength={120} value={input.ports} onChange={(event) => change("ports", event.target.value)} placeholder="80, 443" /></Field><DetailList items={[["Hostname", input.target], ["IPv4 asset", input.ip], ["Default rate", state.preferences.rate], ["Default deadline", state.preferences.deadline]]} /><Notice>Creates an empty draft. Proposal generation, analyst approval, and scanner execution are separate. Execution is In development.</Notice></>}
      <div className="flex justify-between gap-3 border-t border-line pt-5"><Button onClick={() => step ? setStep((current) => current - 1) : close()}>{step ? <><ArrowLeft size={13} />Back</> : "Cancel"}</Button><Button type="submit" variant="dark">{step < 2 ? <>Continue<ArrowRight size={13} /></> : "Create assessment"}</Button></div>
    </form>
  </Dialog>;
}

export function ActionDialog({ assessment, actionId }: { assessment: Assessment; actionId: string }) {
  const { state, close, open, updateAssessment, notify } = usePreview();
  const action = assessment.actions.find((item) => item.id === actionId)!;
  const [rationale, setRationale] = useState("");
  const [error, setError] = useState("");
  const active = action.kind === "Active";
  function decide(decision: "Approved" | "Declined") {
    try {
      const updated = approveAction(assessment, actionId, decision, rationale, timestamp());
      updateAssessment(assessment.id, () => updated);
      notify(`${decision} decision recorded. No execution occurred.`); close();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "The decision could not be recorded."); }
  }
  function retry() {
    if (!state.preferences.tools[action.tool]) { setError(`${action.tool} is turned off in preview preferences.`); return; }
    try {
      const updated = retryAction(assessment, actionId, timestamp());
      updateAssessment(assessment.id, () => updated);
      open({ type: "action", assessmentId: assessment.id, actionId: updated.actions.at(-1)!.id });
      notify("New retry proposal created. The failed attempt is preserved.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "A retry proposal could not be created."); }
  }
  return <Dialog title={action.title} description={`${action.tool} / ${assessment.name} / ${action.id}`} onClose={close}>
    <div className="mb-5 flex flex-wrap gap-2"><StateBadge state={action.state} /><Badge>{action.kind === "Import" ? "Recorded import fixture" : action.kind}</Badge><Badge>Synthetic preview</Badge></div>
    <div className="mb-5 rounded-xl border-l-4 border-lime bg-soft p-4"><p className="mb-1 text-[10px] font-bold text-muted">Proposal rationale</p><p className="text-xs leading-relaxed">{action.why}</p></div>
    <DetailList items={[["Exact target", `${assessment.target} / ${assessment.ip}`], ["Allowed TCP ports", assessment.ports.join(", ")], ["Rate / deadline", `${assessment.rate} / ${assessment.deadline}`], ["Permission reference", assessment.permissionRef], ["Execution", "In development / no scanner connected"]]} />
    {active && <div className="mt-5"><Notice tone="warning">Active validation is unsupported. This fixture proposal can be declined, but cannot be approved or executed.</Notice></div>}
    {action.output && <div className="mt-5"><h3 className="mb-2 flex items-center gap-2 text-xs font-bold"><FileText size={14} />Recorded fixture output</h3><pre className="max-h-60 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-soft p-4 font-mono text-[11px] leading-relaxed">{action.output}</pre></div>}
    {action.state === "Pending" && <div className="mt-5"><Field htmlFor="decision-rationale" label="Decision rationale" hint="Recorded with your decision. Approval never marks this step Done."><textarea id="decision-rationale" rows={3} maxLength={2000} value={rationale} onChange={(event) => setRationale(event.target.value)} placeholder="Explain why this proposal should be approved or declined." /></Field></div>}
    {action.state === "Approved" && <div className="mt-5"><Notice>Approval recorded. No scanner was started and no results were created. The execution control remains unavailable.</Notice></div>}
    {action.state === "Failed" && <div className="mt-5"><Notice tone="warning">A new retry proposal preserves this failed fixture attempt and needs a fresh decision. It cannot start a scanner.</Notice></div>}
    {error && <p role="alert" className="mt-4 text-xs text-[#a4432c]">{error}</p>}
    {action.state === "Failed" && !state.preferences.tools[action.tool] && <p className="mt-4 text-xs text-muted">{action.tool} is turned off in preview preferences. Enable it in Settings to propose a retry.</p>}
    <div className="mt-6 flex flex-wrap justify-end gap-2 border-t border-line pt-5"><Button onClick={close}>Close</Button>{action.state === "Pending" && <><Button variant="danger" disabled={!rationale.trim()} onClick={() => decide("Declined")}>Decline proposal</Button><Button variant="lime" disabled={active || !rationale.trim()} title={active ? "Active validation is In development" : undefined} onClick={() => decide("Approved")}><ShieldCheck size={14} />Record approval</Button></>}{action.state === "Failed" && <Button variant="lime" disabled={!state.preferences.tools[action.tool]} onClick={retry}>Create retry proposal</Button>}{action.state === "Approved" && <Button disabled>Start scan / In development</Button>}</div>
  </Dialog>;
}

export function FindingDialog({ assessment, findingId }: { assessment: Assessment; findingId: string }) {
  const { close, open, updateAssessment, notify } = usePreview();
  const finding = assessment.findings.find((item) => item.id === findingId)!;
  const [disposition, setDisposition] = useState(finding.disposition);
  const [note, setNote] = useState(finding.reviewNote || "");
  function save() {
    if (!note.trim()) return;
    updateAssessment(assessment.id, (current) => ({ ...current,
      findings: current.findings.map((item) => item.id === findingId ? { ...item, disposition, reviewNote: note.trim() } : item),
      audit: [...current.audit, { id: makeId("EV"), at: timestamp(), title: `${finding.id} reviewed`, detail: `${disposition}: ${note.trim()}. Validation status unchanged.` }],
    }));
    notify("Finding review saved. Validation status is unchanged."); close();
  }
  return <Dialog title={finding.title} description={`${finding.id} / ${assessment.name} / Synthetic evidence`} onClose={close} wide>
    <div className="mb-5 flex flex-wrap gap-2"><Badge tone={finding.severity}>{finding.severity}</Badge><Badge tone={finding.status === "Confirmed" ? "success" : "warning"}>{finding.status}</Badge><Badge>{finding.confidence} confidence / fixture label</Badge></div>
    <DetailList items={[["Affected asset", finding.asset], ["CVE / CWE", finding.reference], ["CVSS", "Unknown / no score or vector supplied"], ["Confidence method", "Not supplied; no calibrated probability"], ["Analyst disposition", finding.disposition]]} />
    {finding.correlationNote && <p className="mt-5 rounded-xl bg-soft p-3 text-xs leading-relaxed">{finding.correlationNote}</p>}
    {finding.falsePositiveNote && <div className="mt-4"><Notice tone="warning">{finding.falsePositiveNote}</Notice></div>}
    <h3 className="mb-3 mt-6 text-sm font-extrabold">Trace to source</h3>
    {finding.evidence.map((evidence, index) => <div key={`${evidence.rawRef}-${index}`} className="mb-3 rounded-xl border border-line p-4"><div className="mb-2 flex flex-wrap items-center gap-2"><b className="text-xs">{evidence.tool}</b><Badge>{evidence.provenance}</Badge></div><p className="break-all font-mono text-[10px] text-muted">{evidence.rawRef}</p><p className="mt-1 text-[10px] text-muted">{displayTime(evidence.observedAt)} / SHA-256: {evidence.sha256 || "Not supplied by fixture"}</p><pre className="my-3 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-soft p-3 font-mono text-[11px]">{evidence.excerpt}</pre><Button small onClick={() => open({ type: "action", assessmentId: assessment.id, actionId: evidence.actionId })}>Open source record</Button></div>)}
    {[["Source observation", finding.observation], ["Inference / uncertainty", finding.inference], ["Remediation", finding.remediation]].map(([label, text]) => <div key={label} className="mt-4 border-l-2 border-lime pl-3"><h3 className="text-[11px] font-bold text-muted">{label}</h3><p className="mt-1 text-xs leading-relaxed">{text}</p></div>)}
    <div className="mt-6 grid gap-4 border-t border-line pt-5 sm:grid-cols-[180px_minmax(0,1fr)]"><Field label="Analyst disposition" htmlFor="finding-disposition"><select id="finding-disposition" value={disposition} onChange={(event) => setDisposition(event.target.value as typeof disposition)}><option>Needs review</option><option>Accepted</option><option>False positive</option></select></Field><Field label="Review rationale" htmlFor="finding-review-note"><textarea id="finding-review-note" rows={2} maxLength={2000} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Record the evidence behind your disposition." /></Field></div>
    <p className="mt-3 text-[10px] text-muted">Acceptance is an analyst disposition. It does not change suspected/confirmed status or validate exploitability.</p>
    <div className="mt-6 flex justify-end gap-2"><Button onClick={close}>Close</Button><Button variant="lime" disabled={!note.trim()} onClick={save}><Check size={14} />Save review</Button></div>
  </Dialog>;
}
