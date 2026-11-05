import type { Assessment, Evidence, Preferences, PreviewState } from './types';

export const TOOLS: readonly {
  name: string; initials: string; color: string;
  intendedMode: 'Live' | 'Import-only' | 'Planned'; description: string; limitation: string;
}[] = [
  { name: 'Nmap', initials: 'Nm', color: '#9fd04f', intendedMode: 'Live', description: 'Host, port and service discovery', limitation: 'In development. Intended for explicitly registered TCP ports only.' },
  { name: 'OWASP ZAP', initials: 'Z', color: '#f8b46a', intendedMode: 'Live', description: 'Web application baseline', limitation: 'In development. Origin-wide authorization required; no active or authenticated scans.' },
  { name: 'OpenVAS / Greenbone', initials: 'G', color: '#c9dca0', intendedMode: 'Import-only', description: 'Infrastructure report import', limitation: 'In development. Preview attachments are not parsed. No scanner is started.' },
  { name: 'Nikto', initials: 'N', color: '#f1ea5f', intendedMode: 'Import-only', description: 'Recorded web server checks', limitation: 'In development. Conditional import acquisition/contract decision remains open. Matches can be false positives.' },
  { name: 'Nessus', initials: 'Ns', color: '#ef8f6b', intendedMode: 'Import-only', description: 'Infrastructure findings import', limitation: 'In development. Requires a licensed export; no API integration.' },
  { name: 'Burp Suite', initials: 'B', color: '#d8d8d0', intendedMode: 'Planned', description: 'Analyst-assisted validation', limitation: 'In development. Export format has not been chosen.' },
  { name: 'Metasploit', initials: 'M', color: '#d8d8d0', intendedMode: 'Planned', description: 'Approved lab validation', limitation: 'In development. Active validation is unsupported and cannot be approved in this preview.' },
];

export const DEFAULT_PREFERENCES: Preferences = {
  analyst: 'Long', collapsed: false, theme: 'system', rate: '2 req/s', deadline: '120 s',
  ports: '80, 443', includeSuspected: true, includeAudit: true,
  tools: Object.fromEntries(TOOLS.map((tool) => [tool.name, tool.intendedMode !== 'Planned'])),
};

function evidence(tool: string, actionId: string, rawRef: string, excerpt: string, at: string): Evidence {
  return { tool, actionId, rawRef, excerpt, observedAt: `2026-11-02T${at}:00+07:00`, provenance: 'Synthetic fixture' };
}

const ASSESSMENTS: Assessment[] = [
  {
    id: 'AST-001', name: 'Customer portal review', request: 'Review exposed services and common web configuration issues on the registered customer portal.',
    target: 'web.lab.example', ip: '192.0.2.30/32', ports: [80, 443], rate: '2 req/s', deadline: '120 s',
    permissionRef: 'LAB-PERM-0042', exclusions: 'No other hosts or ports. No denial-of-service checks.',
    createdAt: '2026-11-02T09:02:00+07:00', messages: [], attachments: [],
    actions: [
      { id: 'A1', tool: 'Nmap', title: 'Service discovery on allowed ports', kind: 'Discovery', state: 'Done', why: 'Scope lists only ports 80 and 443. Discovery supports tool selection using observed services.', output: 'Synthetic fixture\n80/tcp open http nginx 1.18.0\n443/tcp open ssl/http nginx 1.18.0\nRaw ref: nmap-2026-11-02-0914.xml' },
      { id: 'A2', tool: 'OWASP ZAP', title: 'Web baseline of https://web.lab.example', kind: 'Baseline', state: 'Done', why: 'The synthetic Nmap record contains an HTTPS web service.', output: "Synthetic fixture\nMissing Content-Security-Policy header\nCookie 'sid' without HttpOnly flag\nServer: nginx/1.18.0\nRaw ref: zap-baseline-0921.json" },
      { id: 'A3', tool: 'Nikto', title: 'Recorded Nikto output', kind: 'Import', state: 'Done', why: 'Historical synthetic imported output illustrates source correlation; no tool was executed.', output: 'Synthetic fixture; not executed by Reknyx\n+ Server: nginx/1.18.0\n+ /backup/: Directory indexing found.\nRaw ref: nikto-0925.txt' },
      { id: 'A4', tool: 'Metasploit', title: 'Lab-only validation of outdated nginx 1.18.0', kind: 'Active', state: 'Pending', why: 'Version banner alone does not confirm vulnerability. Active validation is In development and cannot be approved or started.' },
    ],
    findings: [
      {
        id: 'F-01', title: 'Outdated nginx 1.18.0 version banner', severity: 'High', asset: 'web.lab.example:443', status: 'Suspected', confidence: 'Medium', reference: 'Needs analyst lookup', disposition: 'Needs review',
        observation: 'Synthetic source records report nginx 1.18.0 in a service banner and Server headers.',
        inference: 'The version may require review. The vendor backport level is unknown; the banner alone does not confirm a vulnerability.',
        remediation: 'Update nginx or confirm the vendor backport level.',
        correlationNote: 'Three synthetic source records refer to the same asset, service and version. Every source membership is retained.',
        evidence: [evidence('Nmap', 'A1', 'nmap-2026-11-02-0914.xml', '443/tcp open ssl/http nginx 1.18.0', '09:14'), evidence('OWASP ZAP', 'A2', 'zap-baseline-0921.json', 'Server: nginx/1.18.0', '09:21'), evidence('Nikto', 'A3', 'nikto-0925.txt', '+ Server: nginx/1.18.0', '09:25')],
      },
      {
        id: 'F-02', title: 'Missing Content-Security-Policy header', severity: 'Medium', asset: 'web.lab.example:443', status: 'Confirmed', confidence: 'High', reference: 'CWE-693', disposition: 'Needs review',
        observation: 'The synthetic response headers from GET / contain no Content-Security-Policy.',
        inference: 'This can increase XSS impact if an injection point exists. None has been observed.', remediation: 'Add a restrictive CSP and test with report-only first.',
        evidence: [evidence('OWASP ZAP', 'A2', 'zap-baseline-0921.json', 'Missing Content-Security-Policy header', '09:21')],
      },
      {
        id: 'F-03', title: 'Directory listing on /backup/', severity: 'Medium', asset: 'web.lab.example:443', status: 'Suspected', confidence: 'Medium', reference: 'CWE-548', disposition: 'Needs review',
        observation: 'Synthetic recorded Nikto output lists directory indexing on /backup/.', inference: 'Files may be exposed. Contents were not retrieved.', remediation: 'Disable autoindex and restrict the path.',
        falsePositiveNote: 'Nikto matches on response patterns. Check manually before reporting as confirmed.',
        evidence: [evidence('Nikto', 'A3', 'nikto-0925.txt', '+ /backup/: Directory indexing found.', '09:25')],
      },
      {
        id: 'F-04', title: 'Session cookie without HttpOnly', severity: 'Low', asset: 'web.lab.example:443', status: 'Confirmed', confidence: 'High', reference: 'CWE-1004', disposition: 'Needs review',
        observation: 'Synthetic Set-Cookie: sid=… has Secure but no HttpOnly.', inference: 'Script access to the cookie is possible if XSS exists.', remediation: 'Set HttpOnly and SameSite on the session cookie.',
        evidence: [evidence('OWASP ZAP', 'A2', 'zap-baseline-0921.json', "Cookie 'sid' without HttpOnly flag", '09:21')],
      },
    ],
    audit: [
      { id: 'EV1', at: '2026-11-02T09:02:00+07:00', title: 'Assessment created', detail: 'Synthetic fixture. Permission ref LAB-PERM-0042 recorded; this is not live authorization.' },
      { id: 'EV2', at: '2026-11-02T09:14:00+07:00', title: 'Nmap completion fixture', detail: 'Synthetic historical example: two services observed. No scanner connected.' },
      { id: 'EV3', at: '2026-11-02T09:21:00+07:00', title: 'ZAP baseline completion fixture', detail: 'Synthetic historical example: three observations.' },
      { id: 'EV4', at: '2026-11-02T09:26:00+07:00', title: 'Nikto output fixture', detail: 'Synthetic recorded output. Not executed or parsed in this preview.' },
      { id: 'EV5', at: '2026-11-02T09:30:00+07:00', title: 'Active validation proposed', detail: 'Synthetic pending proposal. Unsupported capability; approval and execution disabled.' },
    ],
  },
  {
    id: 'AST-002', name: 'Staging API check', request: 'Review the registered staging API using read-only observations.', target: 'api.lab.example', ip: '192.0.2.31/32', ports: [443], rate: '1 req/s', deadline: '60 s', permissionRef: 'LAB-PERM-0043', exclusions: 'Read-only requests only.', createdAt: '2026-11-02T10:40:00+07:00',
    messages: [], attachments: [], findings: [],
    actions: [{ id: 'A1', tool: 'Nmap', title: 'Service discovery on port 443', kind: 'Discovery', state: 'Failed', why: 'No observations yet. Discovery precedes web or API tool selection.', output: 'Synthetic fixture\nTimed out after 60 s. No partial results kept.\nRetrying needs a new approval; no retry is executed here.' }],
    audit: [
      { id: 'EV1', at: '2026-11-02T10:40:00+07:00', title: 'Assessment created', detail: 'Synthetic fixture. Permission ref LAB-PERM-0043 recorded.' },
      { id: 'EV2', at: '2026-11-02T10:52:00+07:00', title: 'Nmap failure fixture', detail: 'Synthetic timeout after 60 s. Nothing recorded as a finding.' },
    ],
  },
];

export function createInitialState(): PreviewState {
  return structuredClone({ assessments: ASSESSMENTS, reports: [], preferences: DEFAULT_PREFERENCES });
}
