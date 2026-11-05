"use client";

import Link from "next/link";
import { ArrowDownToLine, ArrowUpRight, CheckCheck, ChevronRight, FileText, ListFilter, Plus, ScanLine, ShieldCheck } from "lucide-react";
import { usePreview, displayTime } from "@/lib/preview-context";
import { allFindings, pendingActions } from "@/lib/model";
import { TOOLS } from "@/lib/fixtures";
import { Badge, Button, Card, CardTitle, Heading, Progress, buttonClass, severityColors } from "./ui";
import type { Assessment, Severity } from "@/lib/types";

export const SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low"];
export function planProgress(assessment: Assessment) {
  return assessment.actions.length ? Math.round(100 * assessment.actions.filter((action) => action.state === "Done").length / assessment.actions.length) : 0;
}

export function Dashboard() {
  const { state, open } = usePreview();
  const findings = allFindings(state.assessments).filter((finding) => finding.disposition !== "False positive");
  const pending = pendingActions(state.assessments);
  const unsupported = pending.filter(({ action }) => action.kind === "Active").length;
  const failed = state.assessments.flatMap((assessment) => assessment.actions.filter((action) => action.state === "Failed" && !assessment.actions.some((retry) => retry.retryOf === action.id && retry.state === "Done")));
  const current = state.assessments.find((assessment) => assessment.actions.some((action) => action.state === "Pending")) || state.assessments[0];
  const confirmed = findings.filter((finding) => finding.status === "Confirmed").length;
  const percent = findings.length ? Math.round(100 * confirmed / findings.length) : 0;
  const sourceCounts = findings.reduce<Record<string, number>>((counts, finding) => {
    finding.evidence.forEach((evidence) => { counts[evidence.tool] = (counts[evidence.tool] || 0) + 1; });
    return counts;
  }, {});
  const totalEvidence = Object.values(sourceCounts).reduce((sum, count) => sum + count, 0);
  const recent = state.assessments.flatMap((assessment) => assessment.audit.map((event) => ({ ...event, assessment }))).sort((a, b) => b.at.localeCompare(a.at)).slice(0, 5);
  const next = pending[0];

  return <>
    <Heading title="Dashboard" description="A clear view of your evidence, decisions, and next steps." action={<Button variant="dark" onClick={() => open({ type: "new" })}><Plus size={15} />New assessment</Button>} />
    <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_290px] 2xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="grid min-w-0 gap-4">
        <Card><div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_150px]">
          <div className="min-w-0"><CardTitle title="Finding priorities" description="Source severity per candidate; highest severity first" action={<Badge>Synthetic</Badge>} />
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><p className="text-[32px] font-extrabold leading-none tracking-[-.05em]">{findings.length}<span className="ml-2 text-xs font-medium tracking-normal text-muted">candidate findings</span></p><div className="flex flex-wrap gap-3">{SEVERITIES.map((severity) => <span key={severity} className="flex items-center gap-1 text-[9px] text-muted"><i className="size-2 rounded-[2px]" style={{ backgroundColor: severityColors[severity] }} />{severity}</span>)}</div></div>
            <div className="flex h-[240px] gap-3" role="group" aria-label="Findings ordered by source severity">
              <div className="grid w-10 shrink-0 grid-rows-4 pb-7 text-[9px] text-muted"><span>Critical</span><span>High</span><span>Medium</span><span>Low</span></div>
              <div className="flex min-w-0 flex-1 gap-3 sm:gap-5">{findings.map((finding) => <button key={`${finding.assessmentId}-${finding.id}`} aria-label={`${finding.id}: ${finding.title}, ${finding.severity} severity`} onClick={() => open({ type: "finding", assessmentId: finding.assessmentId, findingId: finding.id })} className="group flex min-w-0 flex-1 flex-col gap-2 rounded-xl text-center">
                <div className="relative flex w-full flex-1 flex-col justify-end overflow-hidden rounded-xl bg-soft"><span className="hatched block w-full rounded-xl transition-[filter] group-hover:brightness-95" style={{ height: `${(4 - SEVERITIES.indexOf(finding.severity)) * 25}%`, backgroundColor: severityColors[finding.severity] }} /><span className="absolute left-0 right-0 top-3 text-[10px] font-bold text-muted">{finding.severity}</span></div><span className="text-[10px] font-bold text-muted">{finding.id}</span>
              </button>)}</div>
            </div>
            <p className="mt-3 text-[10px] text-muted">Severity is source-reported. CVSS is unknown; no numeric risk score is inferred.</p>
          </div>
          <div className="grid grid-cols-2 gap-4 border-t border-line pt-5 lg:grid-cols-1 lg:gap-3 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
            {[{ label: "Awaiting decision", count: pending.length, detail: `${unsupported} unsupported fixture proposal${unsupported === 1 ? "" : "s"}`, id: "pending-count" }, { label: "Run issues", count: failed.length, detail: "Unresolved fixture failures", id: "failed-count" }, { label: "Confirmed", count: confirmed, detail: `of ${findings.length} fixture findings` }, { label: "Suspected", count: findings.length - confirmed, detail: "Validation still needed" }].map((stat) => <div key={stat.label} className="lg:border-b lg:border-line lg:pb-3 lg:last:border-b-0 lg:last:pb-0"><p className="text-[11px] text-muted">{stat.label}</p><p data-testid={stat.id} className="my-1 text-[29px] font-extrabold leading-tight tracking-[-.04em]">{stat.count}</p><p className="text-[9px] text-muted">{stat.detail}</p></div>)}
          </div>
        </div></Card>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card><CardTitle title="Plan progress" description={current.name} action={<Link href={`/assessments/${current.id}/plan`} className={`${buttonClass} !min-h-7 !px-3 !py-1 !text-[10px]`}>Open plan<ArrowUpRight size={12} /></Link>} /><Progress value={planProgress(current)} warning label="Synthetic plan steps completed" /><p className="mt-3 text-[10px] text-muted">{current.actions.filter((action) => action.state === "Done").length} of {current.actions.length} fixture steps complete / {current.rate}, {current.deadline}</p></Card>
          <Card><CardTitle title={next ? "Your next decision" : "No decisions waiting"} description={next ? next.action.kind === "Active" ? "Active validation is not available in this preview. Review or decline the fixture proposal." : next.action.why : "Review the evidence or create a sample report."} />{next && <button onClick={() => open({ type: "action", assessmentId: next.assessment.id, actionId: next.action.id })} className="flex items-center gap-1 text-xs font-bold text-forest">Review proposal<ChevronRight size={14} /></button>}</Card>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <Card><CardTitle title="Evidence by source" description={`${totalEvidence} synthetic source memberships`} /><div className="my-5 flex h-4 gap-1 overflow-hidden rounded-full">{Object.entries(sourceCounts).map(([name, count]) => <span key={name} className="hatched" style={{ width: `${100 * count / totalEvidence}%`, backgroundColor: TOOLS.find((tool) => tool.name === name)?.color }} />)}</div>{Object.entries(sourceCounts).map(([name, count]) => <div className="mt-3 flex items-center gap-2 text-[11px]" key={name}><i className="size-2 rounded-sm" style={{ backgroundColor: TOOLS.find((tool) => tool.name === name)?.color }} /><span>{name}</span><span className="ml-auto text-muted">{count}/{totalEvidence}</span></div>)}</Card>
          <Card><CardTitle title="Validation status" description="Confirmed fixture findings" /><div className="relative mx-auto mt-6 max-w-[185px]"><svg viewBox="0 0 200 120" role="img" aria-label={`${confirmed} of ${findings.length} fixture findings confirmed`}><path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--soft)" strokeWidth="22" strokeLinecap="round" /><path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#9fd04f" strokeWidth="22" strokeLinecap="round" pathLength="100" strokeDasharray={`${percent} 100`} /></svg><p className="absolute bottom-1 left-0 right-0 text-center text-3xl font-extrabold tracking-[-.05em]">{percent}%</p></div><p className="mt-3 text-center text-[10px] leading-relaxed text-muted">{confirmed}/{findings.length} confirmed in the fixture.<br />Suspected findings stay labeled.</p></Card>
          <Card><CardTitle title="Assessments" description="Recorded plan completion" />{state.assessments.slice(0, 3).map((assessment) => <Link key={assessment.id} href={`/assessments/${assessment.id}/plan`} className="mb-4 block rounded-lg last:mb-0"><div className="mb-2 flex gap-2 text-[11px]"><b className="truncate">{assessment.name}</b><span className="ml-auto text-muted">{planProgress(assessment)}%</span></div><Progress value={planProgress(assessment)} warning={assessment.actions.some((action) => action.state !== "Done")} label={`${assessment.name} fixture plan completion`} /><p className="mt-1.5 truncate text-[10px] text-muted">{assessment.target}</p></Link>)}</Card>
        </div>
      </div>
      <div className="grid min-w-0 gap-4">
        <Card><CardTitle title="Active scope" description="Registered demo target" action={<Link href={`/assessments/${current.id}/scope`} className="mt-0.5 text-[11px] font-bold text-muted hover:text-ink">View<ArrowUpRight className="ml-1 inline" size={12} /></Link>} />
          <div className="scope-art relative flex min-h-[175px] flex-col overflow-hidden rounded-2xl bg-lime p-4 text-[#141a14]"><div className="flex items-center gap-1.5 text-[10px] font-bold"><ShieldCheck size={13} />Synthetic lab scope</div><div className="relative z-10 mt-auto min-w-0"><p className="break-all text-[17px] font-extrabold tracking-[-.03em]">{current.target}</p><p className="mt-1 text-[10px]">{current.ip} / TCP {current.ports.join(", ")}</p><p className="mt-2 text-[10px] font-semibold">{current.permissionRef}</p></div></div>
          <div className="mt-4 grid grid-cols-5 gap-1.5">{[{ label: "Review", icon: CheckCheck, run: () => next && open({ type: "action", assessmentId: next.assessment.id, actionId: next.action.id }) }, { label: "Plan", icon: ScanLine, href: `/assessments/${current.id}/plan` }, { label: "Attach", icon: ArrowDownToLine, run: () => open({ type: "import", assessmentId: current.id }) }, { label: "Findings", icon: ListFilter, href: `/assessments/${current.id}/findings` }, { label: "Report", icon: FileText, href: `/assessments/${current.id}/report` }].map((item) => {
            const content = <><item.icon size={16} strokeWidth={1.6} /><span className="text-[8px] font-semibold">{item.label}</span></>;
            const classes = "flex aspect-square min-w-0 flex-col items-center justify-center gap-1.5 rounded-xl border border-line hover:bg-soft";
            return item.href ? <Link className={classes} key={item.label} href={item.href}>{content}</Link> : <button className={classes} key={item.label} onClick={item.run} disabled={!next && item.label === "Review"}>{content}</button>;
          })}</div>
          <p className="mb-3 mt-5 text-[10px] text-muted">Integration roadmap</p><div className="flex flex-wrap justify-between gap-2">{TOOLS.slice(0, 6).map((tool) => <Link key={tool.name} href="/settings#integrations" title={`${tool.name}: In development`} className="flex flex-col items-center gap-1.5"><span className="grid size-8 place-items-center rounded-full text-[10px] font-extrabold text-[#141a14]" style={{ backgroundColor: tool.color }}>{tool.initials}</span><span className="text-[8px] text-muted">{tool.name.split(" ")[0].slice(0, 6)}</span></Link>)}</div>
        </Card>
        <Card><CardTitle title="Activity" description="Synthetic records and session changes" action={<Link href={`/assessments/${current.id}/audit`} className="text-[10px] font-bold text-muted">View all</Link>} />{recent.map((event) => <Link href={`/assessments/${event.assessment.id}/audit`} key={`${event.assessment.id}-${event.id}`} className="flex gap-3 border-t border-line py-3 first:border-t-0 last:pb-0"><span className="mt-1 grid size-6 shrink-0 place-items-center rounded-full bg-soft text-forest"><ShieldCheck size={12} /></span><div className="min-w-0"><p className="text-[11px] font-bold">{event.title}</p><p className="mt-0.5 truncate text-[10px] text-muted">{event.assessment.name}</p><p className="mt-1 text-[9px] text-muted">{displayTime(event.at)}</p></div></Link>)}</Card>
      </div>
    </div>
  </>;
}
