import { AssessmentPage } from "@/components/assessments";
export default async function Page({ params }: { params: Promise<{ id: string; view?: string[] }> }) {
  const { id, view } = await params;
  return <AssessmentPage assessmentId={id} tab={view?.join("/") || "plan"} />;
}
