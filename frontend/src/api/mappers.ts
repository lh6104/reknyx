/** Projections of schema-validated server DTOs. Preview state is a separate model.
 * These pure functions do not validate untrusted HTTP responses or authorize work.
 */
import type { components } from '../../../contracts/generated/api';

type Schemas = components['schemas'];

export function mapAssessment(input: Schemas['AssessmentDetail']) {
  const { assessment, scope } = structuredClone(input);
  if (assessment.id !== scope.assessment_id || assessment.scope_version !== scope.version) {
    throw new Error('Assessment and scope do not reference the same revision.');
  }
  return {
    id: assessment.id,
    name: assessment.name,
    request: assessment.request,
    stateRevision: assessment.state_revision,
    status: assessment.status,
    createdAt: assessment.created_at,
    scope,
  };
}

export function mapFinding(input: Schemas['Finding']) {
  const source = structuredClone(input);
  return {
    id: source.id,
    assessmentId: source.assessment_id,
    revision: source.revision,
    title: source.title,
    severity: source.severity,
    validationStatus: source.validation_status,
    analystDisposition: source.analyst_disposition,
    cvss: source.cvss,
    cvssVector: source.cvss_vector,
    cvssVersion: source.cvss_version,
    cvssSource: source.cvss_source,
    confidenceMethod: source.confidence_method,
    confidenceValue: source.confidence_value,
    observationIds: source.observation_ids,
    priority: source.priority,
    priorityReasons: source.priority_reasons,
    unknowns: source.unknowns,
    source,
  };
}

export function mapObservation(input: Schemas['Observation']) {
  const source = structuredClone(input);
  return {
    id: source.id,
    assessmentId: source.assessment_id,
    artifactId: source.artifact_id,
    rawLocator: source.raw_locator,
    sourceTool: source.source_tool,
    asset: source.asset,
    service: source.service,
    location: source.location,
    rawSeverity: source.raw_severity,
    rawConfidence: source.raw_confidence,
    observedAt: source.observed_at,
    ingestedAt: source.ingested_at,
    source,
  };
}

export function mapMessage(input: Schemas['ConversationMessage']) {
  const source = structuredClone(input);
  return {
    id: source.id,
    assessmentId: source.assessment_id,
    role: source.role,
    content: source.content,
    actorId: source.actor_id,
    source: source.source,
    stateRevision: source.state_revision,
    basisObservationIds: source.basis_observation_ids,
    proposalIds: source.proposal_ids,
    limitations: source.limitations,
    createdAt: source.created_at,
  };
}

export function mapExecution(input: Schemas['Execution']) {
  const source = structuredClone(input);
  return {
    id: source.id,
    assessmentId: source.assessment_id,
    actionId: source.action_id,
    attemptId: source.attempt_id,
    attemptFence: source.attempt_fence,
    state: source.state,
    startedAt: source.started_at,
    finishedAt: source.finished_at,
    receiptId: source.receipt_id,
    artifactIds: source.artifact_ids,
    failureCode: source.failure_code,
    cancellationRequestedAt: source.cancellation_requested_at,
  };
}
