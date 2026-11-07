import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { mapAssessment, mapExecution, mapFinding, mapMessage, mapObservation } from '../src/api/mappers';
import type { components } from '../../contracts/generated/api';

type Schemas = components['schemas'];
const cases = JSON.parse(readFileSync(resolve(process.cwd(), '../contracts/examples/schema-cases.json'), 'utf8')).cases;
function fixture<T>(id: string): T {
  const found = cases.find((item: {id: string}) => item.id === id);
  assert.ok(found, `Missing contract fixture ${id}`);
  return structuredClone(found.payload) as T;
}

test('assessment projection keeps UUID, revisions, nullable hostname and typed scope', () => {
  const input = fixture<Schemas['AssessmentDetail']>('valid-AssessmentDetail');
  input.scope.asset.hostname = null;
  const result = mapAssessment(input);
  assert.equal(result.id, input.assessment.id);
  assert.equal(result.stateRevision, input.assessment.state_revision);
  assert.equal(result.scope.version, input.scope.version);
  assert.equal(result.scope.asset.hostname, null);
  assert.deepEqual(result.scope.allowed_ports, input.scope.allowed_ports);
  assert.equal(result.scope.hash, input.scope.hash);
  input.scope.allowed_ports.push(9999);
  assert.notDeepEqual(result.scope.allowed_ports, input.scope.allowed_ports);
});

test('assessment projection rejects mismatched scope identity or revision', () => {
  const input = fixture<Schemas['AssessmentDetail']>('valid-AssessmentDetail');
  input.scope.assessment_id = '00000000-0000-4000-8000-000000000099';
  assert.throws(() => mapAssessment(input), /same revision/);
  input.scope.assessment_id = input.assessment.id;
  input.scope.version += 1;
  assert.throws(() => mapAssessment(input), /same revision/);
});

test('finding projection preserves every severity, validation state and independent disposition', () => {
  const input = fixture<Schemas['Finding']>('valid-Finding');
  for (const severity of ['critical', 'high', 'medium', 'low', 'informational', 'unknown'] as const) {
    for (const validation of ['observed', 'suspected', 'confirmed', 'rejected', 'needs_review'] as const) {
      for (const disposition of ['needs_review', 'accepted', 'rejected'] as const) {
        const result = mapFinding({ ...input, severity, validation_status: validation, analyst_disposition: disposition, cvss: null, confidence_value: null });
        assert.equal(result.severity, severity);
        assert.equal(result.validationStatus, validation);
        assert.equal(result.analystDisposition, disposition);
        assert.equal(result.cvss, null);
        assert.equal(result.confidenceValue, null);
        assert.deepEqual(result.observationIds, input.observation_ids);
        assert.equal(result.confidenceMethod, input.confidence_method);
      }
    }
  }
});

test('historical observations retain raw and canonical identities, timestamps and provenance references', () => {
  const input = fixture<Schemas['Observation']>('valid-historical-ipv6-udp');
  const result = mapObservation(input);
  assert.equal(result.asset.address_family, 'ipv6');
  assert.equal(result.asset.authorized_asset_id, null);
  assert.equal(result.service?.transport, 'udp');
  assert.equal(result.observedAt, input.observed_at);
  assert.equal(result.ingestedAt, input.ingested_at);
  assert.equal(result.artifactId, input.artifact_id);
  assert.equal(result.rawLocator, input.raw_locator);
});

test('messages keep actor, role, source, revision and evidence links separate', () => {
  const input = fixture<Schemas['ConversationMessage']>('valid-ConversationMessage');
  const result = mapMessage({ ...input, role: 'system', actor_id: null, source: 'system', limitations: ['Synthetic example'] });
  assert.equal(result.role, 'system');
  assert.equal(result.actorId, null);
  assert.equal(result.source, 'system');
  assert.equal(result.stateRevision, input.state_revision);
  assert.deepEqual(result.limitations, ['Synthetic example']);
  assert.deepEqual(result.basisObservationIds, input.basis_observation_ids);
});

test('execution state remains distinct, including uncertainty and partial outcomes', () => {
  for (const state of ['queued', 'running', 'succeeded', 'partial', 'failed', 'timed_out', 'cancelled', 'execution_unknown'] as const) {
    const input = fixture<Schemas['Execution']>(`valid-execution-${state}`);
    const result = mapExecution(input);
    assert.equal(result.state, state);
    assert.equal(result.attemptFence, input.attempt_fence);
    assert.equal(result.receiptId, input.receipt_id);
    assert.deepEqual(result.artifactIds, input.artifact_ids);
  }
});
