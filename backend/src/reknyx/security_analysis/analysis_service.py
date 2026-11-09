"""Internal read-only assessment-bound analysis seam; caller owns transactions.

No public endpoint, provider payload or mutation is added. Hold the assessment row
lock only for pack assembly/revalidation, never across an external provider request.
Knowledge snapshots are operator-approved inputs, not user-selected paths.
"""
import hashlib

from reknyx.assessments.service import require_membership
from reknyx.contracts import canonical_request
from reknyx.infrastructure.errors import DomainError
from .analysis_pack import assemble_pack, check_pack, validate_review
from .evidence_context import build_context
from .knowledge import retrieve_knowledge, knowledge_pack


def prepare_analysis_pack(db, actor_id, assessment_id, *, snapshot, query, as_of,
                          expected_revision, identifiers=None, limit=5):
    assessment=require_membership(db,actor_id,assessment_id,lock=True)
    # FOR UPDATE does not refresh SQLAlchemy identity-map state by itself.
    db.refresh(assessment)
    if assessment.data['state_revision']!=expected_revision:
        raise DomainError(409,'stale_revision')
    context=build_context(db,assessment)
    retrieval=retrieve_knowledge(db,snapshot,query,as_of=as_of,identifiers=identifiers,limit=limit)
    knowledge=knowledge_pack(retrieval,snapshot=snapshot)
    return assemble_pack(actor_id=actor_id,assessment_id=assessment_id,
        state_revision=assessment.data['state_revision'],scope_version=assessment.data['scope_version'],
        context=context,knowledge=knowledge,query=query)


def accept_analysis_review(db, actor_id, assessment_id, *, pack, output):
    """Recheck current membership/state against a trusted server-owned frozen pack.

    Digest checks detect accidents, not forged client input. Do not expose this
    interface with client-supplied packs without a durable server pack identity.
    """
    assessment=require_membership(db,actor_id,assessment_id,lock=True)
    # FOR UPDATE does not refresh SQLAlchemy identity-map state by itself.
    db.refresh(assessment)
    check_pack(pack)
    if pack['actor_id']!=actor_id or pack['assessment_id']!=assessment_id:
        raise DomainError(404,'not_found')
    if (pack['state_revision']!=assessment.data['state_revision']
            or pack['scope_version']!=assessment.data['scope_version']):
        raise DomainError(409,'stale_revision')
    context=build_context(db,assessment)
    digest=hashlib.sha256(canonical_request(context)).hexdigest()
    if digest!=pack['context_sha256']:
        raise DomainError(409,'stale_revision')
    return validate_review(pack,output)
