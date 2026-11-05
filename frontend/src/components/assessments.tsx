"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronRight, ClipboardList, FileText, History, Plus, ShieldCheck, Sparkles, Upload } from "lucide-react";
import { makeId, timestamp, usePreview, displayTime } from "@/lib/preview-context";
import { assessmentStatus, createReportSnapshot, proposeAction, severityCounts } from "@/lib/model";
import type { Assessment } from "@/lib/types";
import { Badge, Button, Card, CardTitle, DetailList, EmptyState, Heading, Notice, StateBadge, buttonClass, severityColors } from "./ui";
import { SEVERITIES } from "./dashboard";
import { FindingRegister } from "./findings";

export function AssessmentsPage() {
  const { state, open } = usePreview();
  const [query, setQuery] = useState("");
  const assessments = state.assessments.filter((assessment) => `${assessment.name} ${assessment.target} ${assessment.id}`.toLowerCase().includes(query.toLowerCase()));
  return <><Heading title="Assessments" description="From a scoped request to a traceable report. You decide what happens next." action={<Button variant="dark" onClick={() => open({ type: "new" })}><Plus size={15} />New assessment</Button>} />
    <div className="mb-5 max-w-[420px]"><input type="search" aria-label="Filter assessments" placeholder="Find an assessment or target…" value={query} onChange={(event) => setQuery(event.target.value)} className="!bg-surface" /></div>
    <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">{assessments.map((assessment) => {
      const counts = severityCounts(assessment.findings);
      return <Link href={`/assessments/${assessment.id}/plan`} key={assessment.id} className="group block rounded-[20px] bg-surface p-5 transition-shadow hover:ring-2 hover:ring-lime sm:p-6"><div className="mb-5 flex items-center justify-between gap-3"><span className="grid size-10 place-items-center rounded-xl bg-soft"><ClipboardList size={19} className="text-forest" /></span><Badge tone={assessment.actions.some((action) => action.state === "Pending") ? "warning" : assessment.actions.some((action) => action.state === "Failed") ? "danger" : "neutral"}>{assessmentStatus(assessment)}</Badge></div><h2 className="text-base font-extrabold">{assessment.name}</h2><p className="mt-1 break-all text-xs text-muted">{assessment.target}</p><div className="my-5 flex h-2.5 gap-1 overflow-hidden rounded-full bg-soft">{SEVERITIES.filter((severity) => counts[severity]).map((severity) => <span key={severity} className="hatched" style={{ flex: counts[severity], backgroundColor: severityColors[severity] }} />)}</div><p className="text-[11px] text-muted">{assessment.findings.length ? SEVERITIES.filter((severity) => counts[severity]).map((severity) => `${counts[severity]} ${severity.toLowerCase()}`).join(" / ") : "No findings. Start with a scoped proposal."}</p><div className="mt-6 flex items-center justify-between border-t border-line pt-4 text-[10px] text-muted"><span>{assessment.id} / Synthetic preview</span><ArrowUpRight size={16} className="text-forest" /></div></Link>;
    })}</div>{!assessments.length && <Card><EmptyState title="No matching assessments" description="Try a different name or target, or create a new empty assessment." /></Card>}
  </>;
}

const TABS = [{ id: "scope", name: "Scope" }, { id: "plan", name: "Plan & runs" }, { id: "findings", name: "Findings" }, { id: "report", name: "Report" }];

export function AssessmentPage({ assessmentId, tab }: { assessmentId: string; tab: string }) {
  const { state, open } = usePreview();
  const assessment = state.assessments.find((item) => item.id === assessmentId);
  if (!assessment) return <Card><EmptyState title="Assessment unavailable in this session" description="New demo assessments reset on reload. Open a seeded assessment or create a new one."><Link href="/assessments" className={buttonClass}>View assessments</Link></EmptyState></Card>;
  if (![...TABS.map((item) => item.id), "audit"].includes(tab)) return <Card><EmptyState title="Assessment view not found" description="Choose scope, plan, findings, report, or the audit trail."><Link href={`/assessments/${assessmentId}/plan`} className={buttonClass}>Open plan</Link></EmptyState></Card>;
  const lifecycle = ["Scope", "Plan", "Collect", "Analyze", "Review", "Report"];
  const index = tab === "scope" ? 0 : tab === "plan" ? 1 : tab === "findings" ? 4 : tab === "report" ? 5 : -1;
  const tabIndex = TABS.findIndex((item) => item.id === tab);
  return <>
    <Link href="/assessments" className="mb-4 inline-flex items-center gap-1.5 text-[11px] text-muted"><ArrowLeft size={13} />All assessments</Link>
    <Heading title={assessment.name} description={`${assessment.target} / ${assessment.id}`} action={<div className="flex flex-wrap items-center gap-2"><Badge>{assessmentStatus(assessment)}</Badge><Link href={`/assessments/${assessment.id}/audit`} className={`${buttonClass} !min-h-8 !px-3 !py-1 !text-[11px]`}><History size={13} />Audit trail</Link></div>} />
    <div aria-label="Assessment lifecycle" className="mb-5 flex flex-wrap items-center gap-2 rounded-2xl border border-line p-3 text-[10px] text-muted">{lifecycle.map((phase, i) => <span key={phase} className="contents"><span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 ${i === index ? "bg-ink font-bold text-surface" : ""}`}>{i === 0 ? <ShieldCheck size={12} /> : null}{phase}</span>{i < 5 && <ChevronRight size={11} className="opacity-50" />}</span>)}<span className="ml-auto hidden text-[9px] sm:inline">Assessment lifecycle</span></div>
    <nav aria-label="Assessment views" className="mb-5 flex gap-1 overflow-x-auto rounded-2xl bg-surface p-1.5">{TABS.map((item) => <Link key={item.id} href={`/assessments/${assessment.id}/${item.id}`} aria-current={item.id === tab ? "page" : undefined} className={`min-w-max flex-1 rounded-xl px-3 py-2.5 text-center text-xs font-bold ${item.id === tab ? "bg-lime text-[#141a14]" : "text-muted hover:bg-soft"}`}>{item.name}</Link>)}</nav>
    {tab === "scope" && <ScopePanel assessment={assessment} />}
    {tab === "plan" && <PlanPanel assessment={assessment} />}
    {tab === "findings" && <FindingRegister assessmentId={assessment.id} />}
    {tab === "report" && <ReportPanel assessment={assessment} />}
    {tab === "audit" && <AuditPanel assessment={assessment} />}
    <div className="mt-5 flex flex-wrap items-center justify-between gap-3">{tabIndex > 0 ? <Link href={`/assessments/${assessment.id}/${TABS[tabIndex - 1].id}`} className={buttonClass}><ArrowLeft size={13} />{TABS[tabIndex - 1].name}</Link> : <span />}{tabIndex >= 0 && tabIndex < 3 && <Link href={`/assessments/${assessment.id}/${TABS[tabIndex + 1].id}`} className={buttonClass}>{TABS[tabIndex + 1].name}<ArrowRight size={13} /></Link>}{tab === "audit" && <Button onClick={() => open({ type: "assistant", assessmentId: assessment.id })}><Sparkles size={14} />Ask about this assessment</Button>}</div>
  </>;
}

function ScopePanel({ assessment }: { assessment: Assessment }) {
  return <Card><CardTitle title="Registered scope" description="A synthetic scope record. Recording a reference does not verify permission." action={<Badge>Synthetic</Badge>} /><DetailList items={[["Target hostname", assessment.target], ["IPv4 asset", assessment.ip], ["Allowed TCP ports", assessment.ports.join(", ")], ["Rate / deadline", `${assessment.rate} / ${assessment.deadline} per action`], ["Permission reference", assessment.permissionRef], ["Exclusions", assessment.exclusions], ["Recorded at", displayTime(assessment.createdAt)]]} /><div className="mt-6"><Notice>Live scope verification and enforcement are In development. This preview cannot send traffic to the target.</Notice></div></Card>;
}

export function PlanPanel({ assessment }: { assessment: Assessment }) {
  const { state, open, updateAssessment, notify } = usePreview();
  const [message, setMessage] = useState("");
  function generate() {
    const request = `Discover services on ${assessment.target}`;
    const result = proposeAction(assessment, request, timestamp());
    if (result.action && !state.preferences.tools[result.action.tool]) { setMessage(`${result.action.tool} is turned off in preview preferences.`); return; }
    setMessage(result.message);
    if (!result.action) return;
    updateAssessment(assessment.id, (current) => {
      const latest = proposeAction(current, request, timestamp());
      return latest.action ? { ...current, actions: [...current.actions, latest.action], audit: [...current.audit, { id: makeId("EV"), at: timestamp(), title: "Deterministic proposal generated", detail: `${latest.action.tool} added as Pending. No model or scanner called.` }] } : current;
    });
    notify("Preview proposal added. Approval and execution remain separate.");
  }
  return <div className="grid gap-4"><Card><CardTitle title="Assessment request" description="The analyst's goal for this registered scope." action={<Badge>Demo / deterministic</Badge>} /><p className="max-w-[80ch] text-[13px] leading-relaxed">{assessment.request}</p><div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-soft p-3"><div className="flex items-center gap-2.5"><span className="grid size-8 place-items-center rounded-xl bg-lime text-[#141a14]"><Sparkles size={15} /></span><div><b className="text-xs">Assessment assistant</b><p className="text-[10px] text-muted">Model not connected / AI planning In development</p></div></div><Button small onClick={() => open({ type: "assistant", assessmentId: assessment.id })}>Open conversation<ArrowUpRight size={12} /></Button></div></Card>
    <Card><CardTitle title="Plan & runs" description="Review why each step exists, its source, and its actual state." action={<Button small onClick={() => open({ type: "import", assessmentId: assessment.id })}><Upload size={13} />Attach results</Button>} />
      {!assessment.actions.length && <EmptyState title="Start with a scoped proposal" description="Generate a deterministic discovery proposal. This adds a Pending step, without calling a model or starting a scan."><Button variant="lime" onClick={generate}><Sparkles size={14} />Generate preview proposal</Button></EmptyState>}
      {assessment.actions.map((action, i) => <button key={action.id} onClick={() => open({ type: "action", assessmentId: assessment.id, actionId: action.id })} className="flex w-full items-start gap-3 border-t border-line py-4 text-left hover:rounded-xl hover:bg-soft sm:px-2"><span className={`mt-0.5 grid size-7 shrink-0 place-items-center rounded-full text-[11px] font-bold ${action.state === "Done" ? "bg-[#e6f0d8] text-[#365a1d]" : "bg-soft text-muted"}`}>{action.state === "Done" ? <Check size={13} /> : i + 1}</span><div className="min-w-0 flex-1"><b className="block text-[13px]">{action.title}</b><p className="mt-1 text-[11px] text-muted">{action.tool} / {action.kind === "Import" ? "Recorded fixture import" : action.kind}{action.retryOf ? ` / New proposal for ${action.retryOf}` : ""}</p><p className="mt-2 max-w-[75ch] text-[11px] leading-relaxed text-muted">{action.why}</p></div><StateBadge state={action.state} /><ChevronRight size={15} className="mt-1 hidden text-muted sm:block" /></button>)}
      {message && <p className="mt-3 text-xs text-forest" role="status">{message}</p>}
      <div className="mt-4"><Notice>Done and Failed entries are synthetic fixture history. Approving a new proposal records a decision only. Scanner execution is In development.</Notice></div>
    </Card>
    {assessment.attachments.length > 0 && <Card><CardTitle title="Preview attachments" description="Read locally, hashed, and retained for this session. No native parsing or findings extraction." />{assessment.attachments.map((attachment) => <div key={attachment.id} className="border-t border-line py-3"><b className="break-all text-xs">{attachment.name}</b><p className="mt-1 text-[10px] text-muted">{attachment.tool} / {attachment.size} / {displayTime(attachment.attachedAt)}</p><p className="mt-2 break-all font-mono text-[10px] text-muted">SHA-256 {attachment.sha256}</p><details className="mt-2 text-xs"><summary className="cursor-pointer text-forest">View escaped excerpt</summary><pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-soft p-3 text-[11px]">{attachment.excerpt}</pre></details></div>)}</Card>}
  </div>;
}

function ReportPanel({ assessment }: { assessment: Assessment }) {
  const { state, setState, open, notify } = usePreview();
  const [acknowledged, setAcknowledged] = useState(false);
  const snapshots = state.reports.filter((report) => report.assessment.id === assessment.id);
  const pending = assessment.actions.filter((action) => action.state === "Pending").length;
  function generate() {
    if (!acknowledged || pending > 0) return;
    const id = makeId("RPT");
    const now = timestamp();
    const report = createReportSnapshot(assessment, state.preferences, id, now);
    setState((current) => ({ ...current, reports: [report, ...current.reports], assessments: current.assessments.map((item) => item.id === assessment.id ? { ...item, audit: [...item.audit, { id: makeId("EV"), at: now, title: "Sample report snapshot created", detail: `${id}. Frozen synthetic draft; not a client-ready release.` }] } : item) }));
    open({ type: "report", reportId: id });
    notify("Sample report snapshot saved for this session.");
  }
  return <div className="grid gap-4"><Card><CardTitle title="Report readiness" description="Freeze a sample report with current evidence, decisions, and limitations." action={<Badge>Draft only</Badge>} />
    {[["Scope recorded as a demo", true], ["Pending proposals resolved", pending === 0], ["Source uncertainty retained", true], ["Failed attempts and limitations included", true]].map(([label, ready]) => <div key={String(label)} className="flex items-center gap-3 border-t border-line py-3 text-xs"><Badge tone={ready ? "success" : "warning"}>{ready ? "Ready" : "Open"}</Badge><span>{String(label)}</span></div>)}
    {pending > 0 && <div className="mt-4"><Notice tone="warning">Resolve {pending} pending proposal{pending === 1 ? "" : "s"} before creating a sample draft. Unsupported validation can be declined with a rationale.</Notice></div>}
    <label className="mt-5 flex items-start gap-2.5 text-xs leading-relaxed"><input type="checkbox" className="mt-0.5" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)} />I understand this is a synthetic draft with incomplete coverage, not a client-ready assessment.</label>
    <div className="mt-5 flex flex-wrap gap-2"><Button variant="dark" disabled={pending > 0 || !acknowledged} onClick={generate}><FileText size={14} />Generate sample draft</Button><Button disabled title="Backend PDF rendering is In development">Generate final PDF</Button></div><p className="mt-3 text-[10px] text-muted">Backend PDF generation: In development. Sample printing uses your browser's Save as PDF.</p>
    </Card><Card><CardTitle title="Frozen sample reports" description="Each snapshot keeps its own evidence and report preferences." />{snapshots.map((report) => <div key={report.id} className="flex flex-wrap items-center justify-between gap-3 border-t border-line py-3"><div><b className="text-xs">{report.id}</b><p className="mt-1 text-[10px] text-muted">{displayTime(report.createdAt)} / {report.assessment.findings.length} recorded candidates</p></div><Button small onClick={() => open({ type: "report", reportId: report.id })}>Preview sample<ArrowUpRight size={12} /></Button></div>)}{!snapshots.length && <EmptyState title="No sample report yet" description="Review the open decisions and acknowledge the limitations to create a frozen draft." />}</Card></div>;
}

function AuditPanel({ assessment }: { assessment: Assessment }) {
  return <Card><CardTitle title="Audit trail" description="Synthetic history followed by actions taken during this preview session." />{[...assessment.audit].reverse().map((event) => <div key={event.id} className="flex gap-3 border-t border-line py-4"><span className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-soft text-forest"><History size={14} /></span><div><b className="text-[13px]">{event.title}</b><p className="mt-1 max-w-[80ch] text-xs leading-relaxed text-muted">{event.detail}</p><p className="mt-2 text-[10px] text-muted">{displayTime(event.at)}</p></div></div>)}</Card>;
}
