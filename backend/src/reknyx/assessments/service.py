from uuid import uuid4

from sqlalchemy import select

from reknyx.contracts import HASH_AUTHORITY, validate
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.models import Assessment, Membership, ScopeRevision, RequestRevision, Message
from reknyx.shared.time import now, timestamp


def require_membership(session, actor_id, assessment_id, *, lock=False):
    statement = select(Assessment).join(Membership, Membership.assessment_id == Assessment.id).where(Assessment.id == assessment_id, Membership.actor_id == actor_id)
    if lock:
        statement = statement.with_for_update(of=Assessment)
    assessment = session.scalar(statement)
    if assessment is None:
        raise DomainError(404, "not_found")
    return assessment


def make_scope(assessment_id, version, value):
    try:
        scope = HASH_AUTHORITY.normalize("scope", {**value, "assessment_id": assessment_id, "version": version})
    except ValueError as exc:
        raise DomainError(422, "validation_error", "Scope authority contains invalid or duplicate normalized values") from exc
    if scope["valid_until"] <= scope["valid_from"]:
        raise DomainError(422, "validation_error", "Scope validity must end after its start")
    if scope["authorization_ref_id"] != scope["asset"]["authorization_ref_id"]:
        raise DomainError(422, "validation_error", "Scope and asset authorization references must match")
    # This draft reference is retained, never registered as live execution authority.
    scope["hash"] = HASH_AUTHORITY.authority_hash("scope", scope)
    return validate("Scope", scope)


class AssessmentService:
    def __init__(self, session, actor_id):
        self.session, self.actor_id = session, actor_id

    def detail(self, assessment_id):
        assessment = require_membership(self.session, self.actor_id, assessment_id)
        scope = self.session.get(ScopeRevision, (assessment_id, assessment.data["scope_version"]))
        return {"assessment": assessment.data, "scope": scope.data}

    def create(self, value):
        validate("AssessmentCreate", value)
        identifier, instant = str(uuid4()), now()
        scope = make_scope(identifier, 1, value["scope"])
        data = {"id": identifier, "name": value["name"], "request": value["request"], "scope_version": 1, "state_revision": 1, "status": "draft", "created_at": timestamp(instant)}
        self.session.add(Assessment(id=identifier, created_at=instant, data=data))
        self.session.flush()
        self.session.add(Membership(assessment_id=identifier, actor_id=self.actor_id))
        self.session.add(ScopeRevision(assessment_id=identifier, version=1, data=scope))
        self.session.add(RequestRevision(assessment_id=identifier, revision=1, content=value["request"]))
        append_event(self.session, self.actor_id, identifier, "assessment.created", identifier, "Draft created; submitted authorization reference is unverified")
        return {"assessment": data, "scope": scope}

    def replace_scope(self, assessment_id, value):
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        if value["expected_version"] != assessment.data["scope_version"]:
            raise DomainError(409, "stale_scope")
        version = assessment.data["scope_version"] + 1
        scope = make_scope(assessment_id, version, value["scope"])
        self.session.add(ScopeRevision(assessment_id=assessment_id, version=version, data=scope))
        assessment.data = {**assessment.data, "scope_version": version, "state_revision": assessment.data["state_revision"] + 1}
        append_event(self.session, self.actor_id, assessment_id, "scope.replaced", assessment_id, "Scope revision appended; execution remains unavailable")
        return {"assessment": assessment.data, "scope": scope}

    def replace_request(self, assessment_id, value):
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        if value["expected_revision"] != assessment.data["state_revision"]:
            raise DomainError(409, "stale_revision")
        revision = assessment.data["state_revision"] + 1
        assessment.data = {**assessment.data, "request": value["request"], "state_revision": revision}
        self.session.add(RequestRevision(assessment_id=assessment_id, revision=revision, content=value["request"]))
        append_event(self.session, self.actor_id, assessment_id, "request.replaced", assessment_id, "Analyst request revised without changing scope")
        return assessment.data

    def append_message(self, assessment_id, value):
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        if value["expected_revision"] != assessment.data["state_revision"]:
            raise DomainError(409, "stale_revision")
        revision, instant, identifier = assessment.data["state_revision"] + 1, now(), str(uuid4())
        data = {"id": identifier, "assessment_id": assessment_id, "role": "analyst", "content": value["content"], "created_at": timestamp(instant), "actor_id": self.actor_id, "state_revision": revision, "basis_observation_ids": [], "proposal_ids": [], "source": "analyst", "limitations": []}
        validate("ConversationMessage", data)
        self.session.add(Message(id=identifier, assessment_id=assessment_id, created_at=instant, data=data))
        assessment.data = {**assessment.data, "state_revision": revision}
        append_event(self.session, self.actor_id, assessment_id, "message.appended", identifier, "Analyst message appended; no inference invoked")
        return data
