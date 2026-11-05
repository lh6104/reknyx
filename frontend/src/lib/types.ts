export type Severity = 'Critical' | 'High' | 'Medium' | 'Low';
export type ActionState = 'Pending' | 'Approved' | 'Done' | 'Declined' | 'Failed';
export type ToolName = string;

export interface Action {
  id: string; tool: ToolName; title: string;
  kind: 'Discovery' | 'Baseline' | 'Import' | 'Active';
  state: ActionState; why: string; output?: string; retryOf?: string;
}
export interface Evidence {
  tool: string; actionId: string; rawRef: string; excerpt: string; observedAt: string;
  provenance: 'Synthetic fixture' | 'Preview attachment'; sha256?: string;
}
export interface Finding {
  id: string; title: string; severity: Severity; asset: string;
  status: 'Confirmed' | 'Suspected'; confidence: 'High' | 'Medium' | 'Low';
  reference: string; observation: string; inference: string; remediation: string;
  evidence: Evidence[]; falsePositiveNote?: string; correlationNote?: string;
  disposition: 'Needs review' | 'Accepted' | 'False positive'; reviewNote?: string;
}
export interface AuditEvent { id: string; at: string; title: string; detail: string }
export interface Message { id: string; role: 'analyst' | 'assistant'; text: string; at: string }
export interface Attachment {
  id: string; name: string; tool: string; size: string; sha256: string;
  excerpt: string; attachedAt: string;
}
export interface Assessment {
  id: string; name: string; request: string; target: string; ip: string; ports: number[];
  rate: string; deadline: string; permissionRef: string; exclusions: string;
  actions: Action[]; findings: Finding[]; audit: AuditEvent[]; messages: Message[];
  attachments: Attachment[]; createdAt: string;
}
export interface Preferences {
  analyst: string; collapsed: boolean; theme: 'system' | 'light' | 'dark';
  rate: string; deadline: string; ports: string; includeSuspected: boolean;
  includeAudit: boolean; tools: Record<string, boolean>;
}
export interface ReportSnapshot {
  id: string; createdAt: string; analyst: string; assessment: Assessment;
  includeSuspected: boolean; includeAudit: boolean;
}
export interface NewAssessmentInput {
  name: string; request: string; target: string; ip: string; ports: string;
  permissionRef: string; acknowledged: boolean;
}
export interface PreviewState {
  assessments: Assessment[]; reports: ReportSnapshot[]; preferences: Preferences;
}
