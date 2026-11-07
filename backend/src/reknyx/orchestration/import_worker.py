"""Durable import worker. Claimed attempts are never blindly rerun after a crash."""
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from sqlalchemy import select

from reknyx.contracts import validate
from reknyx.evidence.imports import normalize
from reknyx.shared.time import now, timestamp


def _parse_child(kind, raw, source, output):
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    try:
        result = {'result': normalize(kind, raw, source)}
    except (ValueError, TypeError, MemoryError):
        result = {'failure_code': 'parser_rejected'}
    with open(output, 'w', encoding='utf-8') as stream:
        json.dump(result, stream)


def isolated_parse(kind, raw, source):
    """Bound parser wall time and address space; never pass database handles."""
    with tempfile.TemporaryDirectory(prefix='reknyx-parse-') as directory:
        output = str(Path(directory) / 'output.json')
        process = multiprocessing.get_context('spawn').Process(target=_parse_child, args=(kind, raw, source, output))
        process.start()
        process.join(10)
        if process.is_alive():
            process.kill()
            process.join()
            return {'failure_code': 'parser_timeout'}
        if process.exitcode != 0 or not os.path.isfile(output) or os.path.getsize(output) > 40 * 1024 * 1024:
            return {'failure_code': 'parser_resource_failure'}
        with open(output, encoding='utf-8') as stream:
            return json.load(stream)


def process_one(session_factory, store):
    from reknyx.infrastructure.models import ImportRecord, Artifact, Assessment, ObservationRecord, FindingRecord, AuditEvent
    with session_factory() as session:
        record = session.scalar(select(ImportRecord).where(ImportRecord.data['state'].astext == 'queued')
                                .order_by(ImportRecord.created_at, ImportRecord.id).with_for_update(skip_locked=True).limit(1))
        if record is None:
            return False
        identifier, assessment_id, instant = record.id, record.assessment_id, now()
        record.data = {**record.data, 'state': 'parsing', 'job': {**record.data['job'], 'state': 'running',
                       'attempt_id': str(uuid4()), 'started_at': timestamp(instant)}}
        artifact = session.get(Artifact, record.data['artifact_id'])
        source = {'assessment_id': assessment_id, 'artifact_id': artifact.id,
                  'observed_at': artifact.data['observed_at'], 'ingested_at': artifact.data['ingested_at']}
        storage_key, sha256, kind = artifact.storage_key, artifact.data['sha256'], record.data['kind']
        session.commit()
    try:
        raw = store.get(storage_key, sha256)
        result = isolated_parse(kind, raw, source)
    except Exception:
        result = {'failure_code': 'artifact_unavailable'}
    with session_factory() as session:
        # Assessment serializes state publication with review/snapshot creation.
        assessment = session.scalar(select(Assessment).where(Assessment.id == assessment_id).with_for_update())
        record = session.scalar(select(ImportRecord).where(ImportRecord.id == identifier).with_for_update())
        if record.data['state'] != 'parsing':
            return True
        instant = now()
        finished = timestamp(instant)
        if 'failure_code' in result:
            record.data = {**record.data, 'state': 'failed', 'failure_code': result['failure_code'],
                'finished_at': finished, 'job': {**record.data['job'], 'state': 'failed',
                'failure_code': result['failure_code'], 'finished_at': finished}}
        else:
            batch = result['result']
            for observation, native in zip(batch['observations'], batch['native'], strict=True):
                validate('Observation', observation)
                session.add(ObservationRecord(id=observation['id'], assessment_id=assessment_id,
                    created_at=instant, data=observation, source_data=native))
            session.flush()
            for finding in batch['findings']:
                validate('Finding', finding)
                session.add(FindingRecord(id=finding['id'], assessment_id=assessment_id, created_at=instant, data=finding))
            record.data = {**record.data, 'state': batch['outcome'], 'parser_version': batch['parser_version'],
                'warnings': batch['warnings'], 'observation_ids': [o['id'] for o in batch['observations']],
                'finished_at': finished, 'job': {**record.data['job'], 'state': 'succeeded', 'finished_at': finished}}
        validate('Import', record.data)
        event = {'id': str(uuid4()), 'assessment_id': assessment_id, 'at': finished,
                 'actor_type': 'worker', 'actor_id': None, 'kind': 'import.finished',
                 'resource_id': identifier, 'reason': 'Import completed from immutable stored bytes.',
                 'outcome': record.data['state']}
        validate('TimelineEvent', event)
        session.add(AuditEvent(id=event['id'], assessment_id=assessment_id, created_at=instant, data=event))
        assessment.data = {**assessment.data, 'state_revision': assessment.data['state_revision'] + 1}
        session.commit()
    return True
