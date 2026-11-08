"""Attributed evidence links; no source deletion, automatic merge or model authority."""
from copy import deepcopy
from uuid import uuid4

from sqlalchemy import select

from reknyx.assessments.service import require_membership
from reknyx.contracts import validate
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.models import Artifact, FindingRecord, ObservationRecord, ReviewRecord
from reknyx.shared.time import now, timestamp
from .correlation import compatibility_reason, asset_identity, service_identity
from .priority import prioritize, SEVERITIES


def _with_source_priority(finding, sources):
    result = deepcopy(finding)
    severities = {row['native'].get('severity', 'unknown') for row in sources}
    severities = {s if s in SEVERITIES else 'unknown' for s in severities}
    result['severity'] = min(severities, key=SEVERITIES.index)
    # This bounded summary cites strongest sources; full memberships remain on the finding.
    severity_ids = [row['observation']['id'] for row in sources
                    if row['native'].get('severity') == result['severity']][:32]
    inputs = [entry for entry in result['risk_input_sources'] if entry['field'] != 'severity']
    if result['severity'] != 'unknown':
        inputs.insert(0, {'field':'severity', 'observation_ids':severity_ids, 'analyst':None})
    if result['cvss'] is not None and not any(entry['field']=='cvss' for entry in inputs):
        fields = ('cvss', 'cvss_vector', 'cvss_version', 'cvss_source')
        cvss_ids = [row['observation']['id'] for row in sources
                    if row['observation']['id'] in finding['observation_ids']
                    and all(row['native'].get(field)==finding[field] for field in fields)][:32]
        if not cvss_ids:
            raise DomainError(503, 'integrity_error', 'Primary CVSS source attribution is unavailable')
        inputs.append({'field':'cvss', 'observation_ids':cvss_ids, 'analyst':None})
    result['risk_input_sources'] = inputs
    notes = []
    if len(severities) > 1:
        notes.append('Linked observations disagree on source severity; highest supported severity is used only for review ordering.')
    if 'unknown' in severities:
        notes.append('At least one linked observation has unknown source severity.')
    if len(sources) > 1:
        notes.append('Primary CVSS, confidence and remediation retain the original source values; inspect every linked source for differences.')
    result['unknowns'] = list(dict.fromkeys(result['unknowns'] + notes))
    if len(result['unknowns']) > 32:
        raise DomainError(413, 'request_too_large', 'Correlation uncertainty exceeds the supported finding limit')
    result.update(prioritize(result))
    return result


class CorrelationService:
    def __init__(self, session, actor_id):
        self.session, self.actor_id = session, actor_id

    def review(self, assessment_id, value):
        validate('CorrelationReview', value)
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        finding = self.session.scalar(select(FindingRecord).where(
            FindingRecord.id == value['finding_id'], FindingRecord.assessment_id == assessment_id).with_for_update())
        if finding is None:
            raise DomainError(404, 'not_found')
        previous = finding.data['revision']
        if value['expected_revision'] != previous:
            raise DomainError(409, 'stale_revision')
        old_ids = finding.data['observation_ids']
        all_ids = list(dict.fromkeys(old_ids + value['observation_ids']))
        if len(all_ids) > 10000:
            raise DomainError(413, 'request_too_large', 'Correlation exceeds the supported membership limit')
        rows = {row.id:row for row in self.session.scalars(select(ObservationRecord).where(
            ObservationRecord.assessment_id == assessment_id, ObservationRecord.id.in_(all_ids)))}
        if any(identifier not in rows for identifier in value['observation_ids']):
            raise DomainError(404, 'not_found')
        if any(identifier not in rows for identifier in old_ids):
            raise DomainError(503, 'integrity_error', 'Finding evidence is unavailable')
        updated = deepcopy(finding.data)
        new_ids = set(value['observation_ids']) - set(old_ids)
        if value['decision'] == 'link':
            artifact_ids = {row.data['artifact_id'] for row in rows.values()}
            artifacts = {row.id:row for row in self.session.scalars(select(Artifact).where(
                Artifact.assessment_id == assessment_id, Artifact.id.in_(artifact_ids)))}
            if set(artifacts) != artifact_ids:
                raise DomainError(503, 'integrity_error', 'Source manifest is unavailable')
            sources = [{'observation':rows[i].data, 'native':rows[i].source_data,
                        'artifact':artifacts[rows[i].data['artifact_id']].data} for i in all_ids]
            anchor = sources[0]
            if (asset_identity(finding.data) != asset_identity(anchor['observation'])
                    or service_identity(finding.data) != service_identity(anchor['observation'])
                    or finding.data['location'] != anchor['observation']['location']):
                raise DomainError(503, 'integrity_error', 'Finding identity differs from its source')
            for candidate in sources:
                reason = compatibility_reason(anchor, candidate)
                if reason:
                    raise DomainError(422, 'validation_error', 'Evidence is not compatible for a supported correlation',
                                      details=[{'field':'observation_ids', 'reason':reason, 'resource_id':candidate['observation']['id']}])
            updated = _with_source_priority(updated, sources)
            updated['observation_ids'] = all_ids
            updated['correlation_reason'] = ('Analyst-linked same-tool/native-rule evidence with matching asset, service, '
                'request location and capture context. All memberships retained; source findings are not deleted.')
            if new_ids:
                updated['analyst_disposition'] = 'needs_review'
        elif not new_ids or set(value['observation_ids']) & set(old_ids):
            raise DomainError(422, 'validation_error', 'Keep-separate cannot unlink existing finding evidence')
        instant, identifier = now(), str(uuid4())
        updated['revision'] = previous + 1
        finding.data = validate('Finding', updated)
        review = validate('ReviewRecord', {'id':identifier, 'assessment_id':assessment_id,
            'finding_id':finding.id, 'actor_id':self.actor_id, 'rationale':value['rationale'],
            'evidence_ids':value['observation_ids'], 'at':timestamp(instant), 'previous_revision':previous,
            'resulting_revision':previous+1, 'disposition':updated['analyst_disposition'],
            'correlation_decision':value['decision']})
        self.session.add(ReviewRecord(id=identifier, assessment_id=assessment_id, created_at=instant, data=review))
        assessment.data = {**assessment.data, 'state_revision':assessment.data['state_revision']+1}
        append_event(self.session, self.actor_id, assessment_id, 'finding.correlation_reviewed', finding.id,
                     value['rationale'])
        return review
