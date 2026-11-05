"use client";

import { ChevronRight, ShieldCheck, TriangleAlert } from "lucide-react";
import { usePreview } from "@/lib/preview-context";
import { pendingActions } from "@/lib/model";
import { Badge, Button, Card, CardTitle, EmptyState, Heading, Notice } from "./ui";

export function ApprovalsPage() {
  const { state, open } = usePreview();
  const queue = pendingActions(state.assessments);
  const failed = state.assessments.flatMap((assessment) => assessment.actions.filter((action) => action.state === "Failed").map((action) => ({ assessment, action })));
  return <><Heading title="Approvals" description="Review the exact proposal and its limits. Approval records a decision; it never starts a scan." /><div className="grid gap-4"><Card><CardTitle title="Awaiting your decision" description={`${queue.length} pending proposal${queue.length === 1 ? "" : "s"}`} />{queue.map(({ assessment, action }) => <div key={`${assessment.id}-${action.id}`} className="flex flex-wrap items-center gap-3 border-t border-line py-4"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#f8f2ce] text-[#695a11]"><ShieldCheck size={18} /></span><div className="min-w-0 flex-1"><b className="text-[13px]">{action.title}</b><p className="mt-1 text-xs text-muted">{assessment.name} / {action.tool}</p></div><Badge tone="warning">{action.kind === "Active" ? "In development" : "Pending"}</Badge><Button small onClick={() => open({ type: "action", assessmentId: assessment.id, actionId: action.id })}>Review<ChevronRight size={13} /></Button></div>)}{!queue.length && <EmptyState title="No decisions waiting" description="New proposals appear here after an explicit preview plan request." />}</Card>
    {failed.length > 0 && <Card><CardTitle title="Failed fixture attempts" description="Failures are history, not pending approvals. A retry proposal requires a fresh decision." />{failed.map(({ assessment, action }) => <div key={`${assessment.id}-${action.id}`} className="flex flex-wrap items-center gap-3 border-t border-line py-4"><TriangleAlert size={17} className="text-[#b1603f]" /><div className="min-w-0 flex-1"><b className="text-[13px]">{action.title}</b><p className="mt-1 text-xs text-muted">{assessment.name} / {action.tool}</p></div><Badge tone="danger">Failed</Badge><Button small onClick={() => open({ type: "action", assessmentId: assessment.id, actionId: action.id })}>View attempt</Button></div>)}</Card>}
    <Notice>Active validation is In development. The synthetic Metasploit proposal can be reviewed or declined; approval and execution remain unavailable.</Notice>
    </div></>;
}
