"""Frozen snapshot creation, durable report state and isolated PDF publication."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from reknyx.assessments.service import require_membership
from reknyx.contracts import validate
from reknyx.evidence.service import ArtifactService
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.models import (Artifact, AuditEvent, FindingRecord, ImportRecord, ObservationRecord,
                                          ReportRecord, ReviewRecord, ScopeRevision, SnapshotRecord)
from reknyx.shared.time import now, timestamp


def build_snapshot(identifier, assessment, scope, actor, instant, findings, observations,
                   artifacts, reviews, failures, include_suspected, tool_summary=None):
    # Findings retained here include rejected observations for the audit appendix;
    # suspected findings are explicitly identified rather than relabelled confirmed.
    selected = [f for f in findings if include_suspected or f['validation_status'] != 'suspected'
                or f['analyst_disposition'] == 'rejected']
    severities = {key: 0 for key in ('critical', 'high', 'medium', 'low', 'informational', 'unknown')}
    for finding in selected:
        severities[finding['severity']] += 1
    counts = {'observations': len(observations), 'canonical_findings': len(selected),
              'accepted_findings': sum(f['analyst_disposition'] == 'accepted' for f in selected),
              'rejected_findings': sum(f['analyst_disposition'] == 'rejected' for f in selected),
              'unresolved_findings': sum(f['analyst_disposition'] not in ('accepted', 'rejected') for f in selected)}
    result = {'id': identifier, 'assessment_id': assessment['id'],
              'state_revision': assessment['state_revision'], 'scope_version': assessment['scope_version'],
              'created_at': instant, 'created_by': actor, 'scope': scope,
              'executive_summary': f"Imported evidence review: {len(selected)} canonical findings included. Draft for analyst review.",
              'methodology': 'Offline import of retained immutable evidence; source observations reviewed independently of technical validation.',
              'rules_of_engagement': 'Imported identities do not authorize live traffic. Scope and authorization references are retained as recorded.',
              'tool_summary': tool_summary if tool_summary is not None else sorted({o['source_tool'] for o in observations}),
              'severity_distribution': severities, 'counts': counts, 'findings': selected,
              'observations': observations, 'artifacts': artifacts, 'reviews': reviews,
              'approvals': [], 'failures': failures,
              'limitations': ['No live scanner execution, provider analysis or offensive validation was performed by this import workflow.',
                              'Technical validation and analyst disposition are independent; this report remains a draft.',
                              f"Suspected findings {'included' if include_suspected else 'excluded except rejected audit entries'}; counts describe included findings."],
              'assumptions': ['Source timestamps and evidence claims are retained without independent verification.'],
              'assessment_started_at': assessment['created_at'], 'assessment_finished_at': None,
              'provenance_notice': 'Provenance is retained per source artifact; synthetic fixtures are not native scanner captures.',
              'release_status': 'draft'}
    validate('ReportSnapshot', result)
    if len(json.dumps(result).encode()) > 10 * 1024 * 1024:
        raise DomainError(413, 'request_too_large', 'Snapshot exceeds 10 MiB')
    return deepcopy(result)


def render_isolated(snapshot):
    validate('ReportSnapshot', snapshot)
    raw = json.dumps(snapshot).encode()
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError('Snapshot exceeds 10 MiB')
    # The fixed child has no user-selected executable, flags or code. Apply limits
    # before importing the renderer; no database transaction spans this process.
    code = '''import resource,sys,json
resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024,512*1024*1024))
resource.setrlimit(resource.RLIMIT_CPU, (30,30))
from reknyx.reporting.renderer import render_pdf
sys.stdout.buffer.write(render_pdf(json.load(sys.stdin)))
'''
    env = {key: value for key, value in os.environ.items() if key in ('PATH', 'LANG', 'LC_ALL')}
    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[2])
    result = subprocess.run([sys.executable, '-c', code], input=raw, capture_output=True,
                            timeout=30, env=env)
    if result.returncode or not result.stdout.startswith(b'%PDF-') or len(result.stdout) > 20 * 1024 * 1024:
        raise ValueError('Bounded PDF renderer failed')
    return result.stdout


class ReportService:
    def __init__(self, session, store, actor_id):
        self.session, self.store, self.actor_id = session, store, actor_id

    def create(self, assessment_id, value):
        validate('ReportCreate', value)
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        if assessment.data['state_revision'] != value['expected_revision']:
            raise DomainError(409, 'stale_revision')
        def data(model):
            return list(self.session.scalars(select(model.data).where(model.assessment_id == assessment_id).order_by(model.created_at, model.id)))
        identifier, snapshot_id, instant = str(uuid4()), str(uuid4()), now()
        scope = self.session.get(ScopeRevision, (assessment_id, assessment.data['scope_version']))
        imports = list(self.session.scalars(select(ImportRecord).where(ImportRecord.assessment_id == assessment_id)
                                            .order_by(ImportRecord.created_at, ImportRecord.id)))
        artifacts = data(Artifact)
        artifact_by_id = {item['id']: item for item in artifacts}
        failures = [f"Import {row.id}: {row.data.get('failure_code') or 'failed'}"
                    for row in imports if row.data.get('state') == 'failed']
        tools = [f"Import {row.id}; kind={row.data['kind']}; parser={row.data.get('parser_version') or 'unknown'}; "
                 f"source_label={row.source_label}; artifact={row.data['artifact_id']}; "
                 f"provenance={artifact_by_id[row.data['artifact_id']]['provenance']}; state={row.data['state']}"
                 for row in imports]
        snapshot = build_snapshot(snapshot_id, assessment.data, scope.data, self.actor_id,
                                  timestamp(instant), data(FindingRecord), data(ObservationRecord),
                                  artifacts, data(ReviewRecord), failures, value['include_suspected'], tools)
        report = validate('Report', {'id': identifier, 'assessment_id': assessment_id,
                         'snapshot_id': snapshot_id, 'created_at': timestamp(instant), 'state': 'pending',
                         'artifact_id': None, 'failure_code': None, 'release_status': 'draft', 'release_review_id': None})
        self.session.add(SnapshotRecord(id=snapshot_id, assessment_id=assessment_id, created_at=instant, data=snapshot))
        self.session.add(ReportRecord(id=identifier, assessment_id=assessment_id, created_at=instant, data=report))
        append_event(self.session, self.actor_id, assessment_id, 'report.queued', identifier, 'Immutable assessment snapshot frozen for draft PDF')
        return validate('AsyncAccepted', {'job_id': identifier, 'resource_id': identifier,
                        'status_url': f'/api/v1/assessments/{assessment_id}/reports/{identifier}'})

    def get(self, assessment_id, report_id):
        require_membership(self.session, self.actor_id, assessment_id)
        record = self.session.get(ReportRecord, report_id)
        if record is None or record.assessment_id != assessment_id:
            raise DomainError(404, 'not_found')
        return record.data

    def get_snapshot(self, assessment_id, report_id):
        report = self.get(assessment_id, report_id)
        snapshot = self.session.get(SnapshotRecord, report['snapshot_id'])
        if snapshot is None or snapshot.assessment_id != assessment_id:
            raise DomainError(503, 'integrity_error')
        return snapshot.data

    def download(self, assessment_id, report_id):
        report = self.get(assessment_id, report_id)
        if report['state'] != 'ready':
            raise DomainError(409, 'report_not_ready')
        return ArtifactService(self.session, self.store, self.actor_id).read_bytes(assessment_id, report['artifact_id'])


def _worker_event(db, assessment_id, report_id, kind, reason, outcome='succeeded'):
    data = validate('TimelineEvent', {'id': str(uuid4()), 'assessment_id': assessment_id,
                    'at': timestamp(now()), 'actor_type': 'worker', 'actor_id': None,
                    'kind': kind, 'resource_id': report_id, 'reason': reason, 'outcome': outcome})
    db.add(AuditEvent(id=data['id'], assessment_id=assessment_id, created_at=now(), data=data))


def process_one(session_factory, store, *, assessment_id=None):
    """Claim once, render outside transactions, publish bytes before ready state.

    Interrupted rendering stays visible as rendering until trusted recovery; it
    is never silently marked ready or automatically requeued.
    """
    with session_factory() as db:
        query = select(ReportRecord).where(ReportRecord.data['state'].astext == 'pending')
        if assessment_id is not None:
            query = query.where(ReportRecord.assessment_id == assessment_id)
        record = db.scalar(query.order_by(ReportRecord.created_at, ReportRecord.id).with_for_update(skip_locked=True).limit(1))
        if record is None:
            return False
        identifier, assessment_id = record.id, record.assessment_id
        snapshot = deepcopy(db.get(SnapshotRecord, record.data['snapshot_id']).data)
        record.data = {**record.data, 'state': 'rendering'}
        db.commit()
    try:
        pdf = render_isolated(snapshot)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        with session_factory() as db:
            record = db.scalar(select(ReportRecord).where(ReportRecord.id == identifier).with_for_update())
            record.data = validate('Report', {**record.data, 'state': 'failed', 'failure_code': 'render_failed'})
            _worker_event(db, assessment_id, identifier, 'report.failed', 'PDF rendering failed; immutable snapshot retained', 'failed')
            db.commit()
        return True
    try:
        with session_factory() as db:
            record = db.scalar(select(ReportRecord).where(ReportRecord.id == identifier).with_for_update())
            artifact = ArtifactService(db, store, snapshot['created_by']).put_bytes(assessment_id, pdf,
                       {'source': 'report', 'content_type': 'application/pdf', 'observed_at': None,
                        'provenance': 'derived', 'historical': False}, actor_type='worker')
            record.data = validate('Report', {**record.data, 'state': 'ready', 'artifact_id': artifact['id']})
            _worker_event(db, assessment_id, identifier, 'report.ready', 'Stored draft PDF bound to immutable snapshot')
            db.commit()
    except (DomainError, OSError, SQLAlchemyError):
        # Resolve a possibly committed transaction from canonical state before
        # recording failure. Filesystem publication gaps remain in store receipts.
        # If the DB itself remains unavailable, leave rendering unresolved.
        with session_factory() as db:
            record = db.scalar(select(ReportRecord).where(ReportRecord.id == identifier).with_for_update())
            if record.data['state'] != 'ready':
                record.data = validate('Report', {**record.data, 'state': 'failed', 'failure_code': 'publication_failed'})
                _worker_event(db, assessment_id, identifier, 'report.failed', 'PDF publication failed; snapshot and reconciliation receipts retained', 'failed')
                db.commit()
    return True
