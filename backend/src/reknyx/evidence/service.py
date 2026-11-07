from uuid import uuid4

from reknyx.assessments.service import require_membership
from reknyx.contracts import validate
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.models import Artifact
from reknyx.shared.time import now, timestamp
from .storage import IntegrityError


class ArtifactService:
    """Caller owns transaction; injected actor must come from trusted authentication."""
    def __init__(self, session, store, actor_id):
        self.session, self.store, self.actor_id = session, store, actor_id

    def put_bytes(self, assessment_id, content, metadata, *, actor_type="analyst"):
        require_membership(self.session, self.actor_id, assessment_id, lock=True)
        validate("ArtifactInput", metadata)
        blob = self.store.put(content)
        identifier, instant = str(uuid4()), now()
        data = {"id": identifier, "assessment_id": assessment_id, **metadata, "sha256": blob.sha256, "size_bytes": blob.size, "ingested_at": timestamp(instant), "parser_version": None, "download_url": f"/api/v1/assessments/{assessment_id}/artifacts/{identifier}/download"}
        validate("Artifact", data)
        self.session.add(Artifact(id=identifier, assessment_id=assessment_id, created_at=instant, storage_key=blob.storage_key, data=data))
        append_event(self.session, self.actor_id, assessment_id, "artifact.stored", identifier, "Original immutable bytes stored with SHA-256 and source metadata", actor_type=actor_type)
        return data

    def manifest(self, assessment_id, artifact_id):
        require_membership(self.session, self.actor_id, assessment_id)
        artifact = self.session.get(Artifact, artifact_id)
        if artifact is None or artifact.assessment_id != assessment_id:
            raise DomainError(404, "not_found")
        return artifact

    def read_bytes(self, assessment_id, artifact_id):
        artifact = self.manifest(assessment_id, artifact_id)
        try:
            raw = self.store.get(artifact.storage_key, artifact.data["sha256"])
            if len(raw) != artifact.data["size_bytes"]:
                raise IntegrityError("Artifact size mismatch")
            return raw
        except IntegrityError as exc:
            raise DomainError(503, "integrity_error", "Stored artifact failed integrity verification") from exc
