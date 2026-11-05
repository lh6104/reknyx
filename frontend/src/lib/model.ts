import type {
  Action, Assessment, Finding, NewAssessmentInput, Preferences, ReportSnapshot, Severity,
} from './types';

const SEVERITIES: Severity[] = ['Critical', 'High', 'Medium', 'Low'];

function parsePorts(value: string): number[] | undefined {
  const input = value.trim();
  if (!/^\d+(?:(?:\s*,\s*|\s+)\d+)*$/.test(input)) return undefined;
  const ports = input.split(/[\s,]+/).map(Number);
  if (ports.some((port) => !Number.isInteger(port) || port < 1 || port > 65535)) return undefined;
  return [...new Set(ports)].sort((a, b) => a - b);
}

function validIPv4Scope(value: string): boolean {
  if (!/^(?:\d{1,3}\.){3}\d{1,3}\/32$/.test(value)) return false;
  return value.slice(0, -3).split('.').every((octet) => Number(octet) <= 255 && String(Number(octet)) === octet);
}

function validHostname(value: string): boolean {
  return value.length <= 253 && !/^[\d.]+$/.test(value) && value.split('.').length >= 2
    && value.split('.').every((label) => label.length <= 63 && /^[a-z\d](?:[a-z\d-]*[a-z\d])?$/i.test(label));
}

export function validateNewAssessment(input: NewAssessmentInput): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!input.name.trim()) errors.name = 'Add an assessment name.';
  if (!input.request.trim()) errors.request = 'Describe the assessment request.';
  if (!validHostname(input.target.trim())) errors.target = 'Enter one hostname, for example web.lab.example.';
  if (!validIPv4Scope(input.ip.trim())) errors.ip = 'Enter one valid IPv4 address with /32.';
  if (!parsePorts(input.ports)) errors.ports = 'Enter integer TCP ports from 1 to 65535, separated by commas or spaces.';
  if (!input.permissionRef.trim()) errors.permissionRef = 'Add a permission reference. This preview does not verify authorization.';
  if (!input.acknowledged) errors.acknowledged = 'Acknowledge the synthetic preview and scope.';
  return errors;
}

export function createAssessment(input: NewAssessmentInput, preferences: Preferences, id: string, now: string): Assessment {
  const errors = validateNewAssessment(input);
  if (Object.keys(errors).length) throw new Error(Object.values(errors).join(' '));
  return {
    id, name: input.name.trim(), request: input.request.trim(), target: input.target.trim().toLowerCase(),
    ip: input.ip.trim(), ports: parsePorts(input.ports)!, rate: preferences.rate, deadline: preferences.deadline,
    permissionRef: input.permissionRef.trim(), exclusions: 'Only this host and the registered TCP ports. No denial-of-service checks.',
    createdAt: now, actions: [], findings: [], messages: [], attachments: [],
    audit: [{ id: 'EV1', at: now, title: 'Preview assessment created', detail: `Permission reference ${input.permissionRef.trim()} recorded without verification. No plan generated and nothing executed.` }],
  };
}

function nextActionId(assessment: Assessment): string {
  let number = 1;
  while (assessment.actions.some((action) => action.id === `A${number}`)) number++;
  return `A${number}`;
}

function appendAudit(assessment: Assessment, title: string, detail: string, now: string): void {
  let number = assessment.audit.length + 1;
  while (assessment.audit.some((event) => event.id === `EV${number}`)) number++;
  assessment.audit.push({ id: `EV${number}`, at: now, title, detail });
}

export function proposeAction(assessment: Assessment, request: string, _now: string): { action?: Action; message: string } {
  const normalized = request.toLowerCase().trim();
  if (!normalized) return { message: 'Describe a request and include the exact registered hostname or IPv4 address.' };
  const identities = normalized.match(/\b(?:[a-z\d](?:[a-z\d-]*[a-z\d])?\.)+[a-z\d](?:[a-z\d-]*[a-z\d])?(?:\/\d{1,3})?/g) ?? [];
  const allowed = [assessment.target.toLowerCase(), assessment.ip, assessment.ip.replace(/\/32$/, '')];
  const foreign = identities.filter((identity) => !allowed.includes(identity));
  if (foreign.length || /\blocalhost\b|(?:[a-f\d]{0,4}:){2,}[a-f\d:.]*/i.test(normalized)) {
    return { message: 'Request rejected: it includes a target outside this assessment. Use only the exact registered hostname or IPv4 /32.' };
  }
  if (!identities.length) return { message: `Scope is unknown. Include ${assessment.target} or ${assessment.ip} explicitly.` };
  const withoutTargets = identities.reduce((text, identity) => text.replaceAll(identity, ''), normalized);
  if (/\b(?:udp|icmp|sctp|ipv6|subnets?|ranges?)\b|\ball\s+ports\b/.test(withoutTargets)) {
    return { message: 'Request rejected: only the registered TCP ports are supported. Protocol changes, port ranges and all-port scans are unavailable.' };
  }
  const requestedPorts: number[] = [];
  const remainingParameters = withoutTargets
    .replace(/\bports?\s+(\d+(?:\s*,\s*\d+)*)/g, (_match, ports: string) => {
      requestedPorts.push(...ports.split(/\s*,\s*/).map(Number));
      return '';
    })
    .replace(/:(\d+)\b/g, (_match, port: string) => { requestedPorts.push(Number(port)); return ''; });
  if (/\d/.test(remainingParameters)) {
    return { message: 'Request rejected: unrecognized numeric parameters. Use an exact target and a comma-separated TCP port list; ranges and ambiguous port syntax are unsupported.' };
  }
  if (requestedPorts.some((port) => !assessment.ports.includes(port))) {
    return { message: 'Request rejected: a requested TCP port is outside the registered scope.' };
  }
  if (/\b(?:exploit|metasploit|active|attack|brute|dos|denial-of-service)\b/.test(normalized)) {
    return { message: 'Active validation is In development. No approval or execution is available for this request.' };
  }
  const baseline = /\b(?:web|https?|headers?|cookies?|zap|app|site|baseline)\b/.test(withoutTargets);
  const tool = baseline ? 'OWASP ZAP' : 'Nmap';
  const duplicate = assessment.actions.find((action) => action.tool === tool && !['Failed', 'Declined'].includes(action.state));
  if (duplicate) return { message: `${tool} work is already recorded as ${duplicate.id} (${duplicate.state}). No duplicate proposal added.` };
  if (baseline) {
    const observedWebPorts = assessment.actions
      .filter((action) => action.tool === 'Nmap' && action.state === 'Done')
      .flatMap((action) => Array.from((action.output ?? '').matchAll(/\b(\d+)\/tcp\s+open\s+(?:ssl\/)?https?\b/gi)).map((match) => Number(match[1])));
    if (!observedWebPorts.some((port) => assessment.ports.includes(port))) {
      return { message: 'A web baseline needs an observed web service on a registered port. Propose service discovery first.' };
    }
  }
  return {
    action: {
      id: nextActionId(assessment), tool, title: `${baseline ? 'Web baseline' : 'Service discovery'} on ${assessment.target}`,
      kind: baseline ? 'Baseline' : 'Discovery', state: 'Pending',
      why: baseline ? 'A recorded web service supports a baseline proposal. Origin-wide authorization must be verified before any future live execution.' : 'Discovery can establish which services exist on the registered TCP ports before selecting further tools.',
    },
    message: 'Deterministic preview proposal generated. Analyst approval is separate; no scanner or model is connected.',
  };
}

export function approveAction(assessment: Assessment, actionId: string, decision: 'Approved' | 'Declined', rationale: string, now: string): Assessment {
  const action = assessment.actions.find((item) => item.id === actionId);
  if (!action || action.state !== 'Pending') throw new Error('Only a pending action can receive an approval decision.');
  if (!rationale.trim()) throw new Error('Add a rationale for the analyst decision.');
  if (decision === 'Approved' && action.kind === 'Active') throw new Error('Active validation is unsupported and In development.');
  const result = structuredClone(assessment);
  result.actions.find((item) => item.id === actionId)!.state = decision;
  appendAudit(result, `${action.tool} ${decision.toLowerCase()}`, `${rationale.trim()} No execution occurred in this preview.`, now);
  return result;
}

export function retryAction(assessment: Assessment, actionId: string, now: string): Assessment {
  const failed = assessment.actions.find((action) => action.id === actionId);
  if (!failed || failed.state !== 'Failed') throw new Error('Only a failed historical action can receive a retry proposal.');
  if (assessment.actions.some((action) => action.retryOf === actionId && !['Failed', 'Declined'].includes(action.state))) {
    throw new Error('A retry proposal already exists for this failed action.');
  }
  if (assessment.actions.some((action) => action.tool === failed.tool && action.kind === failed.kind && !['Failed', 'Declined'].includes(action.state))) {
    throw new Error('Equivalent work already exists for this tool and scope. Review the existing proposal instead of adding a duplicate retry.');
  }
  const result = structuredClone(assessment);
  result.actions.push({
    id: nextActionId(assessment), tool: failed.tool, title: `Retry proposal: ${failed.title}`, kind: failed.kind,
    state: 'Pending', retryOf: actionId, why: 'A new analyst decision is required. The failed historical attempt is preserved. No retry is executed in this preview.',
  });
  appendAudit(result, `${failed.tool} retry proposed`, `New pending proposal for ${actionId}; historical failure retained. No execution occurred.`, now);
  return result;
}

export function createReportSnapshot(assessment: Assessment, preferences: Preferences, id: string, now: string): ReportSnapshot {
  return { id, createdAt: now, analyst: preferences.analyst, assessment: structuredClone(assessment), includeSuspected: preferences.includeSuspected, includeAudit: preferences.includeAudit };
}

export function allFindings(assessments: Assessment[]): Array<Finding & { assessmentId: string; assessmentName: string }> {
  return assessments.flatMap((assessment) => assessment.findings.map((finding) => ({ ...finding, assessmentId: assessment.id, assessmentName: assessment.name })))
    .sort((a, b) => SEVERITIES.indexOf(a.severity) - SEVERITIES.indexOf(b.severity));
}

export function pendingActions(assessments: Assessment[]): Array<{ assessment: Assessment; action: Action }> {
  return assessments.flatMap((assessment) => assessment.actions.filter((action) => action.state === 'Pending').map((action) => ({ assessment, action })));
}

export function assessmentStatus(assessment: Assessment): string {
  if (!assessment.actions.length) return 'Draft';
  const pending = assessment.actions.filter((action) => action.state === 'Pending').length;
  if (pending) return `${pending} to approve`;
  if (assessment.actions.some((action) => action.state === 'Approved')) return 'Approved · execution unavailable';
  if (assessment.actions.some((action) => action.state === 'Failed')) return 'Run failed';
  return 'Ready to review';
}

export function severityCounts(findings: Finding[]): Record<Severity, number> {
  const counts: Record<Severity, number> = { Critical: 0, High: 0, Medium: 0, Low: 0 };
  for (const finding of findings) counts[finding.severity]++;
  return counts;
}
