"use client";

import { Printer } from "lucide-react";
import { usePreview } from "@/lib/preview-context";
import { NewAssessmentDialog, ActionDialog, FindingDialog } from "./assessment-dialogs";
import { AssistantDialog } from "./assistant-dialog";
import { ImportDialog } from "./import-dialog";
import { ReportDocument } from "./report-document";
import { Button, Dialog, Notice } from "./ui";

export function OverlayHost() {
  const { state, overlay, close } = usePreview();
  if (!overlay) return null;
  if (overlay.type === "new") return <NewAssessmentDialog />;
  if (overlay.type === "assistant") return <AssistantDialog assessmentId={overlay.assessmentId} />;
  if (overlay.type === "report") {
    const report = state.reports.find((item) => item.id === overlay.reportId);
    if (!report) return null;
    return <Dialog title="Sample report preview" description="Frozen synthetic draft. Browser printing is separate from backend PDF generation." onClose={close} wide printable>
      <ReportDocument report={report} />
      <div className="mt-6 space-y-4 border-t border-line pt-5 print:hidden"><Notice>Save sample PDF opens your browser's print dialog. Choose Save as PDF. Backend PDF generation is In development.</Notice><div className="flex flex-wrap justify-end gap-2"><Button onClick={close}>Close</Button><Button variant="dark" onClick={() => window.print()}><Printer size={14} />Save sample PDF</Button></div></div>
    </Dialog>;
  }
  const assessment = state.assessments.find((item) => item.id === overlay.assessmentId);
  if (!assessment) return null;
  if (overlay.type === "action" && assessment.actions.some((action) => action.id === overlay.actionId)) return <ActionDialog key={`${assessment.id}-${overlay.actionId}`} assessment={assessment} actionId={overlay.actionId} />;
  if (overlay.type === "finding" && assessment.findings.some((finding) => finding.id === overlay.findingId)) return <FindingDialog key={`${assessment.id}-${overlay.findingId}`} assessment={assessment} findingId={overlay.findingId} />;
  if (overlay.type === "import") return <ImportDialog assessment={assessment} />;
  return null;
}
