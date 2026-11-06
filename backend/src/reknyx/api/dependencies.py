import hmac

from reknyx.infrastructure.auth import token_digest
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.models import AuthSession
from reknyx.shared.time import now


def get_session(db, token):
    if not token or len(token) > 128:
        raise DomainError(401, "unauthenticated")
    session = db.get(AuthSession, token_digest(token))
    if session is None or session.revoked or session.expires_at <= now():
        raise DomainError(401, "unauthenticated")
    return session


def require_origin(settings, origin):
    if origin not in settings.allowed_origins:
        raise DomainError(403, "forbidden", "An exact configured Origin is required")


def require_csrf(settings, session, headers):
    require_origin(settings, headers.get("origin"))
    supplied = headers.get("x-csrf-token", "")
    if not supplied.isascii() or not hmac.compare_digest(supplied, session.csrf_token):
        raise DomainError(403, "forbidden", "A valid CSRF token is required")
