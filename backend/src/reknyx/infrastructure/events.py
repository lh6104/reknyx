from uuid import uuid4
from reknyx.contracts import validate
from reknyx.shared.time import now, timestamp
from .models import AuditEvent


def append_event(session, actor_id, assessment_id, kind, resource_id, reason, outcome="succeeded"):
    instant = now()
    event = {"id": str(uuid4()), "assessment_id": assessment_id, "at": timestamp(instant), "actor_type": "analyst", "actor_id": actor_id, "kind": kind, "resource_id": resource_id, "reason": reason, "outcome": outcome}
    validate("TimelineEvent", event)
    session.add(AuditEvent(id=event["id"], assessment_id=assessment_id, created_at=instant, data=event))
    return event
