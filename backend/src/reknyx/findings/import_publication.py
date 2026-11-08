"""Publish parser findings with an immutable exact-capture index.

Caller holds the assessment lock and owns an atomic publication savepoint.
No legacy backfill, source deletion or cross-tool issue equivalence is performed.
"""
from sqlalchemy import select

from reknyx.contracts import validate
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.models import FindingCaptureKey, FindingRecord, ReviewRecord
from .duplicate_identity import capture_fingerprint, link_duplicate, DuplicatePublicationError


def publish_findings(session, assessment_id, batch, artifact, instant):
    if not batch['findings']:
        return 0
    if artifact['assessment_id'] != assessment_id:
        raise DuplicatePublicationError('source_manifest_unavailable')
    sources = {o['id']:(o,native) for o,native in zip(batch['observations'],batch['native'],strict=True)}
    incoming = []
    for finding in batch['findings']:
        validate('Finding', finding)
        if finding['assessment_id'] != assessment_id or len(finding['observation_ids']) != 1:
            raise DuplicatePublicationError('invalid_parsed_finding')
        identifier = finding['observation_ids'][0]
        observation, native = sources[identifier]
        if observation['assessment_id'] != assessment_id or observation['artifact_id'] != artifact['id']:
            raise DuplicatePublicationError('source_manifest_unavailable')
        fingerprint = capture_fingerprint(observation,native,artifact,batch['parser_version'])
        incoming.append((fingerprint,finding,identifier))
    keys = list(session.scalars(select(FindingCaptureKey).where(
        FindingCaptureKey.assessment_id==assessment_id,
        FindingCaptureKey.fingerprint.in_([row[0] for row in incoming]))))
    finding_ids = {key.finding_id for key in keys}
    originals = {row.id:row for row in session.scalars(select(FindingRecord).where(
        FindingRecord.assessment_id==assessment_id,FindingRecord.id.in_(finding_ids))
        .order_by(FindingRecord.id).with_for_update())}
    if set(originals) != finding_ids:
        raise DuplicatePublicationError('finding_index_integrity')
    targets = {key.fingerprint:originals[key.finding_id] for key in keys}
    # Conservative veto: a prior negative review requires manual attachment to this finding.
    blocked = set(session.scalars(select(ReviewRecord.data['finding_id'].astext).where(
        ReviewRecord.assessment_id==assessment_id,
        ReviewRecord.data['correlation_decision'].astext=='keep_separate')))
    new_keys = []
    duplicates = 0
    for fingerprint, finding, identifier in incoming:
        original = targets.get(fingerprint)
        if original is not None and original.id not in blocked:
            if original.data['assessment_id'] != assessment_id:
                raise DuplicatePublicationError('finding_index_integrity')
            original.data = validate('Finding',link_duplicate(original.data,identifier))
            append_event(session,None,assessment_id,'finding.duplicate_linked',original.id,
                'Another exact native capture observation was linked; original analyst and technical states retained.',
                actor_type='worker')
            duplicates += 1
        else:
            if original is not None:
                finding = {**finding,'correlation_reason':
                    'Repeated capture kept separate because the indexed finding has an analyst keep-separate review.'}
            row = FindingRecord(id=finding['id'],assessment_id=assessment_id,created_at=instant,
                                data=validate('Finding',finding))
            session.add(row)
            if original is None:
                targets[fingerprint] = row
                new_keys.append(FindingCaptureKey(assessment_id=assessment_id,fingerprint=fingerprint,
                                                  finding_id=row.id,created_at=instant))
    session.flush()  # Parent findings exist before their immutable index references are inserted.
    session.add_all(new_keys)
    return duplicates
