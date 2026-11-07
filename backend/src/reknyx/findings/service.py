"""Attributed analyst disposition changes remain separate from technical validation."""
from uuid import uuid4
from sqlalchemy import select

from reknyx.assessments.service import require_membership
from reknyx.contracts import validate
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.events import append_event
from reknyx.shared.time import now, timestamp


class FindingsService:
    def __init__(self, session, actor_id):
        self.session, self.actor_id = session, actor_id

    def get(self, assessment_id, finding_id):
        from reknyx.infrastructure.models import FindingRecord
        require_membership(self.session, self.actor_id, assessment_id)
        record = self.session.get(FindingRecord, finding_id)
        if record is None or record.assessment_id != assessment_id:
            raise DomainError(404, 'not_found')
        return record.data

    def review(self, assessment_id, finding_id, value):
        from reknyx.infrastructure.models import FindingRecord, ObservationRecord, ReviewRecord
        validate('FindingReview', value)
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        finding = self.session.scalar(select(FindingRecord).where(FindingRecord.id == finding_id,
            FindingRecord.assessment_id == assessment_id).with_for_update())
        if finding is None:
            raise DomainError(404, 'not_found')
        previous = finding.data['revision']
        if value['expected_revision'] != previous:
            raise DomainError(409, 'stale_revision')
        for identifier in value['evidence_ids']:
            observation = self.session.get(ObservationRecord, identifier)
            if observation is None or observation.assessment_id != assessment_id or identifier not in finding.data['observation_ids']:
                raise DomainError(422, 'validation_error', 'Review evidence must belong to this finding')
        identifier, instant = str(uuid4()), now()
        data = {'id': identifier, 'assessment_id': assessment_id, 'finding_id': finding_id,
                'actor_id': self.actor_id, 'rationale': value['rationale'], 'evidence_ids': value['evidence_ids'],
                'at': timestamp(instant), 'previous_revision': previous, 'resulting_revision': previous + 1,
                'disposition': value['disposition'], 'correlation_decision': None}
        validate('ReviewRecord', data)
        finding.data = validate('Finding', {**finding.data, 'revision': previous + 1,
                                          'analyst_disposition': value['disposition']})
        self.session.add(ReviewRecord(id=identifier, assessment_id=assessment_id, created_at=instant, data=data))
        assessment.data = {**assessment.data, 'state_revision': assessment.data['state_revision'] + 1}
        append_event(self.session, self.actor_id, assessment_id, 'finding.reviewed', finding_id, value['rationale'])
        return data
