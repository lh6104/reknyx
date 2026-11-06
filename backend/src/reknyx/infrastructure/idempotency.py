"""Short PostgreSQL transactions serialize replay before revision checks."""
import hashlib
import re
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from reknyx.contracts import canonical_request
from .errors import DomainError
from .models import IdempotencyRecord


def begin_operation(session, actor_id, assessment_id, operation, path, key, value):
    if not key or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", key):
        raise DomainError(422, "validation_error", "A bounded Idempotency-Key is required")
    namespace = hashlib.sha256(canonical_request([actor_id, assessment_id, operation, path, key])).hexdigest()
    digest = hashlib.sha256(canonical_request(value)).hexdigest()
    operation_identity = str(uuid5(NAMESPACE_URL, "reknyx:operation:" + namespace))
    # The reservation transaction contains no domain mutation. Committing this
    # identity first lets concurrent requests read the bound digest and report a
    # real durable operation while its creator runs the short domain transaction.
    statement = insert(IdempotencyRecord).values(namespace=namespace, actor_id=actor_id, assessment_id=assessment_id, operation=operation, resource_path=path, key=key, digest=digest, status=0, body={"operation_id": operation_identity}, location=None).on_conflict_do_nothing(index_elements=[IdempotencyRecord.namespace]).returning(IdempotencyRecord.namespace)
    created = session.scalar(statement) is not None
    session.commit()
    query = select(IdempotencyRecord).where(IdempotencyRecord.namespace == namespace)
    record = session.scalar(query.with_for_update() if created else query)
    if record.digest != digest:
        raise DomainError(409, "idempotency_conflict")
    if not created and record.status == 0:
        raise DomainError(409, "operation_in_progress", "The durable operation is pending; retry the same key", details=[{"field": None, "reason": "durable_operation_id", "resource_id": operation_identity}], retry_after=1)
    # A pending reservation left by a crash is deliberately never reclaimed here.
    # Trusted reconciliation must prove no side effect before allowing another run.
    return record, not created or record.status != 0


def finalize_known_database_failure(session, namespace, body):
    """Record failure only after rollback and an exclusive pending-row check.

    Only callers whose entire side effect and completion live in one database
    transaction may use this seam. A live transaction holding this row prevents
    reconciliation. External IO operations must retain an unknown/pending outcome.
    """
    session.rollback()
    record = session.scalar(select(IdempotencyRecord).where(IdempotencyRecord.namespace == namespace).with_for_update(nowait=True))
    if record is None:
        raise DomainError(503, "dependency_unavailable")
    if record.status == 0:
        record.status, record.body, record.location = 503, body, None
    session.commit()
    return record
