"use client";

import Link from "next/link";
import { FileText, LockKeyhole } from "lucide-react";
import { displayTime, usePreview } from "@/lib/preview-context";
import { Badge, Button, Card, CardTitle, EmptyState, Heading, buttonClass } from "./ui";

export function ReportsPage() {
  const { state, open } = usePreview();

  return <>
    <Heading title="Reports" description="Review frozen sample snapshots and prepare reports within each assessment." />
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,1fr)]">
      <Card>
        <CardTitle title="Assessment reports" description="Scope, decisions, evidence, and limitations stay together." />
        {state.assessments.length ? <div className="divide-y divide-line">{state.assessments.map((assessment) => {
          const reports = state.reports.filter((report) => report.assessment.id === assessment.id);
          return <div key={assessment.id} className="flex flex-wrap items-center justify-between gap-3 py-5 first:pt-1 last:pb-0">
            <div className="min-w-0"><h3 className="text-[13px] font-bold">{assessment.name}</h3><p className="mt-1 break-words text-xs text-muted">{assessment.target} · {assessment.id}</p><p className="mt-2 text-xs text-muted">{reports.length ? `${reports.length} frozen snapshot(s)` : "Draft not generated"}</p></div>
            <Link className={`${buttonClass} !min-h-8 !px-3 !text-xs`} href={`/assessments/${assessment.id}/report`}>Open report workspace</Link>
          </div>;
        })}</div> : <EmptyState title="No assessments yet" description="Create an assessment before preparing a report."><Link href="/assessments" className={buttonClass}>Open assessments</Link></EmptyState>}
      </Card>
      <Card className="self-start">
        <div className="mb-4 flex size-11 items-center justify-center rounded-2xl bg-lime text-[#141a14]"><LockKeyhole size={22} aria-hidden="true" /></div>
        <CardTitle title="A record of the review" description="Each draft freezes the assessment and its report preferences at creation." />
        <p className="text-[13px] leading-relaxed text-muted">Later decisions and setting changes do not rewrite saved snapshots. Suspected findings, evidence provenance, failed actions, and pending decisions remain visible according to the frozen report options.</p>
        <div className="mt-5 flex flex-wrap gap-2"><Badge tone="warning">Synthetic sample</Badge><Badge>Backend PDF: In development</Badge></div>
      </Card>
    </div>
    <Card className="mt-5">
      <CardTitle title="Frozen snapshots" description="Snapshots exist only for this preview session and reset on reload." />
      {state.reports.length ? <div className="divide-y divide-line">{state.reports.toReversed().map((report) => <div key={report.id} className="flex flex-wrap items-center gap-3 py-5 first:pt-1 last:pb-0">
        <span className="rounded-xl bg-soft p-3 text-muted"><FileText size={20} aria-hidden="true" /></span>
        <div className="min-w-0 flex-1"><h3 className="text-[13px] font-bold">{report.assessment.name}</h3><p className="mt-1 break-words text-xs text-muted">{report.id} · {displayTime(report.createdAt)} · {report.analyst}</p><p className="mt-1 text-xs text-muted">Suspected findings {report.includeSuspected ? "included" : "excluded"}; audit trail {report.includeAudit ? "included" : "excluded"}</p></div>
        <Button small onClick={() => open({ type: "report", reportId: report.id })}>Preview snapshot</Button>
      </div>)}</div> : <EmptyState title="No frozen snapshots" description="Open an assessment’s report workspace to create a sample draft. Creating a draft does not complete or approve the assessment." />}
    </Card>
  </>;
}
