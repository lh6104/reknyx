"use client";

import { useState } from "react";
import { ArrowUpRight, Files, Search } from "lucide-react";
import { usePreview } from "@/lib/preview-context";
import { allFindings } from "@/lib/model";
import { Badge, Card, EmptyState, Heading } from "./ui";
import { SEVERITIES } from "./dashboard";

export function FindingRegister({ assessmentId }: { assessmentId?: string }) {
  const { state, open } = usePreview();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("All severities");
  const [status, setStatus] = useState("All validation states");
  const findings = allFindings(state.assessments).filter((finding) => (!assessmentId || finding.assessmentId === assessmentId) && (severity === "All severities" || finding.severity === severity) && (status === "All validation states" || finding.status === status) && `${finding.title} ${finding.id} ${finding.asset}`.toLowerCase().includes(query.toLowerCase()));
  return <Card>
    <div className="mb-5 flex flex-wrap gap-3"><div className="relative min-w-[180px] flex-1"><Search size={15} className="absolute left-3 top-3.5 text-muted" /><input aria-label="Filter findings" placeholder="Search findings…" value={query} onChange={(event) => setQuery(event.target.value)} className="!pl-9" /></div><select aria-label="Filter by severity" className="!w-auto" value={severity} onChange={(event) => setSeverity(event.target.value)}><option>All severities</option>{SEVERITIES.map((item) => <option key={item}>{item}</option>)}</select><select aria-label="Filter by validation" className="!w-auto" value={status} onChange={(event) => setStatus(event.target.value)}><option>All validation states</option><option>Confirmed</option><option>Suspected</option></select></div>
    <div className="mb-2 hidden grid-cols-[85px_minmax(0,1fr)_110px_100px_20px] gap-3 px-3 text-[10px] font-semibold text-muted lg:grid"><span>Severity</span><span>Finding / affected asset</span><span>Validation</span><span>Review</span><span /></div>
    {findings.map((finding) => <button key={`${finding.assessmentId}-${finding.id}`} onClick={() => open({ type: "finding", assessmentId: finding.assessmentId, findingId: finding.id })} className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-t border-line px-1 py-4 text-left hover:rounded-xl hover:bg-soft sm:px-3 lg:grid-cols-[85px_minmax(0,1fr)_110px_100px_20px]">
      <span className="col-span-2 flex items-center justify-between lg:col-span-1"><Badge tone={finding.severity}>{finding.severity}</Badge><span className="text-[10px] text-muted lg:hidden">{finding.id}</span></span><div className="min-w-0"><b className="block text-[13px]">{finding.title}</b><span className="mt-1 block break-all text-[11px] text-muted">{finding.asset}</span><span className="mt-2 flex items-center gap-1.5 text-[10px] text-muted"><Files size={12} />{finding.evidence.length} source{finding.evidence.length === 1 ? "" : "s"}{finding.correlationNote ? " / correlated" : ""}{!assessmentId && ` / ${finding.assessmentName}`}</span></div><Badge tone={finding.status === "Confirmed" ? "success" : "warning"}>{finding.status}</Badge><span className="text-[10px] text-muted">{finding.disposition}</span><ArrowUpRight size={15} className="hidden text-muted lg:block" />
    </button>)}
    {!findings.length && <EmptyState title="No findings match" description="New assessments start without findings. Clear the filters or view the synthetic customer portal assessment." />}
    <p className="mt-4 border-t border-line pt-4 text-[10px] text-muted">{findings.length} candidate{findings.length === 1 ? "" : "s"} / Source severity ordering. CVSS unknown. Analyst acceptance does not confirm a vulnerability.</p>
  </Card>;
}

export function FindingsPage() {
  return <><Heading title="Findings" description="Review source evidence and uncertainty across your assessments." /><FindingRegister /></>;
}
