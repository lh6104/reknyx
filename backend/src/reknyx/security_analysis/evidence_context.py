"""Bounded, minimal projections. No raw artifacts, messages or target addresses leave here."""
import hashlib
from sqlalchemy import select
from reknyx.contracts import canonical_request
from reknyx.infrastructure.models import ObservationRecord, Artifact

VERSION='bounded-observations-v2'

def build_context(db, assessment):
    rows=list(db.scalars(select(ObservationRecord).where(ObservationRecord.assessment_id==assessment.id)
         .order_by(ObservationRecord.created_at.desc(),ObservationRecord.id).limit(33)))
    observations=[]
    synthetic=True
    for row in rows[:32]:
        artifact=db.get(Artifact,row.data['artifact_id'])
        synthetic = synthetic and artifact is not None and artifact.assessment_id==assessment.id and artifact.data['provenance']=='synthetic_fixture'
        native=row.source_data
        severity=native.get('severity','unknown')
        if severity not in ('critical','high','medium','low','informational','unknown'):severity='unknown'
        service=row.data.get('service') or {}
        observations.append({'id':row.id,'kind':row.data['kind'],'source_tool':row.data['source_tool'],
          'facts':{'severity':severity,'transport':service.get('transport','unknown'),
                   'port':service.get('port'),'historical':artifact.data.get('historical',True) if artifact else True}})
    projection={'version':VERSION,'observations':observations,'truncated':len(rows)>32}
    digest=hashlib.sha256(canonical_request(projection)).hexdigest()
    return {**projection,'sha256':digest,'synthetic_only':bool(observations) and synthetic}
