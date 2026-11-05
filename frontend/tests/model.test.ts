import assert from 'node:assert/strict';
import test from 'node:test';
import { DEFAULT_PREFERENCES, createInitialState } from '../src/lib/fixtures';
import {
  validateNewAssessment, createAssessment, proposeAction, approveAction,
  retryAction, createReportSnapshot, allFindings, pendingActions,
  assessmentStatus, severityCounts,
} from '../src/lib/model';
import type { Assessment, NewAssessmentInput } from '../src/lib/types';

const now = '2026-11-05T09:00:00.000Z';
const valid: NewAssessmentInput = {
  name: 'New review', request: 'Inspect the registered web service.',
  target: 'new.lab.example', ip: '192.0.2.40/32', ports: '80, 443',
  permissionRef: 'PREVIEW-0044', acknowledged: true,
};
const draft = (): Assessment => createAssessment(valid, DEFAULT_PREFERENCES, 'AST-003', now);

test('scope rejects malformed octets, networks, hostnames and unbounded TCP ports', () => {
  for (const ip of ['256.0.2.30/32', '192.0.2.30/24', '192.0.2.30', '::1/128', '192.00.2.30/32']) {
    assert.ok(validateNewAssessment({ ...valid, ip }).ip, ip);
  }
  for (const ports of ['', '0', '65536', '80.5', '1e2', '80-443', '-1', '80,,443', '80,']) {
    assert.ok(validateNewAssessment({ ...valid, ports }).ports, ports);
  }
  for (const target of ['https://new.lab.example', '*.lab.example', '-bad.lab.example', '192.0.2.40', 'new.lab.example/path']) {
    assert.ok(validateNewAssessment({ ...valid, target }).target, target);
  }
  assert.deepEqual(validateNewAssessment(valid), {});
});

test('required request, permission reference and preview acknowledgment cannot be omitted', () => {
  for (const field of ['name', 'request', 'permissionRef'] as const) {
    assert.ok(validateNewAssessment({ ...valid, [field]: '  ' })[field]);
  }
  assert.ok(validateNewAssessment({ ...valid, acknowledged: false }).acknowledged);
  assert.throws(() => createAssessment({ ...valid, request: '' }, DEFAULT_PREFERENCES, 'AST-003', now));
});

test('creation starts an isolated empty draft and copies defaults without creating a plan', () => {
  const assessment = draft();
  assert.equal(assessment.target, 'new.lab.example');
  assert.deepEqual(assessment.ports, [80, 443]);
  assert.deepEqual(assessment.actions, []);
  assert.deepEqual(assessment.findings, []);
  assert.deepEqual(assessment.messages, []);
  assert.deepEqual(assessment.attachments, []);
  assert.equal(assessment.audit.length, 1);
  assert.equal(assessment.createdAt, now);
  assert.equal(assessmentStatus(assessment), 'Draft');
});

test('proposals reject unknown, mixed and foreign targets even when another assessment owns them', () => {
  const assessment = draft();
  for (const request of [
    'Discover hosts', 'Scan api.lab.example', 'Scan new.lab.example and api.lab.example',
    'Scan 192.0.2.41', 'Scan 192.0.2.40 and 198.51.100.2',
    'Scan new.lab.example.evil.example', 'Scan https://foreign.example/',
    'Scan 2001:db8::1', 'Scan new.lab.example and localhost',
    'Scan new.lab.example and 192.0.2.0/24',
  ]) {
    assert.equal(proposeAction(assessment, request, now).action, undefined, request);
  }
  assert.equal(assessment.actions.length, 0);
});

test('a current exact target produces only a pending proposal and duplicate work is suppressed', () => {
  const assessment = draft();
  const result = proposeAction(assessment, 'Discover NEW.LAB.EXAMPLE', now);
  assert.equal(result.action?.tool, 'Nmap');
  assert.equal(result.action?.state, 'Pending');
  assert.equal(result.action?.kind, 'Discovery');
  assert.equal(assessment.actions.length, 0);
  const withProposal = { ...assessment, actions: [result.action!] };
  assert.equal(proposeAction(withProposal, 'Discover 192.0.2.40/32', now).action, undefined);
  assert.equal(proposeAction(createInitialState().assessments[0], 'Check web headers on web.lab.example', now).action, undefined);
});

test('web baseline needs an observed web service and never selects an unregistered port', () => {
  assert.equal(proposeAction(draft(), 'Check web headers on new.lab.example', now).action, undefined);
  const assessment = draft();
  assessment.actions.push({ id: 'A1', title: 'Discovery', tool: 'Nmap', kind: 'Discovery', state: 'Done', why: 'Fixture', output: '443/tcp open ssl/http' });
  const result = proposeAction(assessment, 'Check web headers on new.lab.example', now);
  assert.equal(result.action?.tool, 'OWASP ZAP');
  assert.equal(result.action?.kind, 'Baseline');
  assert.equal(proposeAction(assessment, 'Check new.lab.example on port 8443', now).action, undefined);
});

test('unsupported port syntax and protocols cannot silently become TCP discovery', () => {
  const assessment = createInitialState().assessments[1];
  for (const request of [
    'Scan api.lab.example on ports 443 8443',
    'Scan api.lab.example on ports 443-65535',
    'Scan api.lab.example over UDP port 443',
    'Scan api.lab.example on ports 443 and 8443',
    'Scan api.lab.example on port 443.5',
    'Scan api.lab.example on all ports',
  ]) assert.equal(proposeAction(assessment, request, now).action, undefined, request);
  assert.equal(proposeAction(assessment, 'Discover api.lab.example on TCP port 443', now).action?.state, 'Pending');
});

test('approval is immutable, requires rationale and never completes an action or confirms findings', () => {
  const assessment = draft();
  assessment.actions.push(proposeAction(assessment, 'Discover new.lab.example', now).action!);
  assert.throws(() => approveAction(assessment, 'A1', 'Approved', ' ', now));
  const approved = approveAction(assessment, 'A1', 'Approved', 'Review approved for this preview.', now);
  assert.equal(approved.actions[0].state, 'Approved');
  assert.equal(assessment.actions[0].state, 'Pending');
  assert.equal(approved.audit.length, assessment.audit.length + 1);
  assert.match(approved.audit.at(-1)!.detail, /Review approved/);
  assert.throws(() => approveAction(approved, 'A1', 'Approved', 'Again', now));
  assert.deepEqual(approved.findings, []);
});

test('unsupported active validation cannot be approved but can be declined', () => {
  const assessment = createInitialState().assessments[0];
  assert.throws(() => approveAction(assessment, 'A4', 'Approved', 'Try validation', now), /development|unsupported/i);
  const declined = approveAction(assessment, 'A4', 'Declined', 'Unsupported capability', now);
  assert.equal(declined.actions[3].state, 'Declined');
  assert.equal(declined.findings[0].status, 'Suspected');
  assert.equal(assessment.actions[3].state, 'Pending');
});

test('retry creates one fresh pending proposal while keeping the failed attempt and output', () => {
  const assessment = createInitialState().assessments[1];
  const retried = retryAction(assessment, 'A1', now);
  assert.equal(retried.actions.length, 2);
  assert.equal(retried.actions[0].state, 'Failed');
  assert.match(retried.actions[0].output!, /Timed out/);
  assert.equal(retried.actions[1].retryOf, 'A1');
  assert.equal(retried.actions[1].state, 'Pending');
  assert.equal(retried.actions[1].output, undefined);
  assert.notEqual(retried.actions[1].id, 'A1');
  assert.equal(assessment.actions.length, 1);
  assert.throws(() => retryAction(retried, 'A1', now));
  assert.throws(() => retryAction(retried, retried.actions[1].id, now));
});

test('retry cannot duplicate equivalent pending work generated through the assistant', () => {
  const assessment = createInitialState().assessments[1];
  const proposal = proposeAction(assessment, 'Discover services on api.lab.example', now).action!;
  assessment.actions.push(proposal);
  assert.throws(() => retryAction(assessment, 'A1', now), /already|duplicate|existing/i);
  assert.equal(assessment.actions.length, 2);
  assert.equal(assessment.actions[0].state, 'Failed');
});

test('reports preserve assessment evidence and preferences after later mutations', () => {
  const assessment = createInitialState().assessments[0];
  const preferences = { ...DEFAULT_PREFERENCES, includeAudit: false };
  const snapshot = createReportSnapshot(assessment, preferences, 'RPT-001', now);
  assessment.findings[0].evidence[0].excerpt = 'Changed';
  assessment.actions[0].state = 'Declined';
  preferences.analyst = 'Someone else';
  preferences.includeAudit = true;
  assert.equal(snapshot.assessment.findings[0].evidence[0].excerpt, '443/tcp open ssl/http nginx 1.18.0');
  assert.equal(snapshot.assessment.actions[0].state, 'Done');
  assert.equal(snapshot.analyst, 'Long');
  assert.equal(snapshot.includeAudit, false);
  assert.equal(snapshot.createdAt, now);
});

test('global views scope source identities, sort severity and keep failed work out of approvals', () => {
  const { assessments } = createInitialState();
  assessments[0].findings.reverse();
  const findings = allFindings(assessments);
  assert.deepEqual(findings.map((finding) => finding.id), ['F-01', 'F-03', 'F-02', 'F-04']);
  assert.equal(assessments[0].findings[0].id, 'F-04');
  assert.equal(findings[0].assessmentId, 'AST-001');
  assert.deepEqual(severityCounts(findings), { Critical: 0, High: 1, Medium: 2, Low: 1 });
  assert.deepEqual(pendingActions(assessments).map(({ assessment, action }) => [assessment.id, action.id]), [['AST-001', 'A4']]);
  assert.equal(assessmentStatus(assessments[1]), 'Run failed');
  assert.equal(findings[0].evidence[0].provenance, 'Synthetic fixture');
  assert.notEqual(createInitialState().assessments[0], assessments[0]);
});
