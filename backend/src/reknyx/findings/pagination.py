"""Finding keyset pages ordered by ordinal priority, source severity, and UUID."""
import base64
import binascii
from datetime import datetime
import hashlib
import hmac
import json
from uuid import UUID

from sqlalchemy import case, tuple_

from reknyx.contracts import canonical_request
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.models import FindingRecord

PRIORITIES = ('review_first', 'review_next', 'routine')
SEVERITIES = ('critical', 'high', 'medium', 'low', 'informational', 'unknown')


def page_findings(db, model, query, limit, cursor, binding, session_secret):
    """The caller scopes/filters query and binds every filter plus authenticated session.

    New rows above the first page's created_at/UUID watermark are excluded. This
    remains a live keyset view, not an immutable report snapshot.
    """
    if type(limit) is not int or not 1 <= limit <= 100:
        raise DomainError(422, 'validation_error', 'Limit must be between 1 and 100')
    if model is not FindingRecord:
        raise ValueError('Finding pagination requires FindingRecord')
    priority = case({name: rank for rank, name in enumerate(PRIORITIES)}, value=model.data['priority'].astext, else_=3)
    severity = case({name: rank for rank, name in enumerate(SEVERITIES)}, value=model.data['severity'].astext, else_=6)
    query_hash = hashlib.sha256(canonical_request(binding)).hexdigest()[:24]
    after = None
    if cursor:
        try:
            if not isinstance(cursor, str) or len(cursor) > 512:
                raise ValueError()
            encoded, signature = cursor.split('.')
            expected = hmac.new(session_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError()
            state = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
            if state['q'] != query_hash:
                raise ValueError()
            watermark = (datetime.fromisoformat(state['w'][0]), str(UUID(state['w'][1])))
            after = (state['a'][0], state['a'][1], str(UUID(state['a'][2])))
            if watermark[0].tzinfo is None or type(after[0]) is not int or type(after[1]) is not int or not 0 <= after[0] <= 3 or not 0 <= after[1] <= 6:
                raise ValueError()
        except (ValueError, KeyError, TypeError, IndexError, binascii.Error, UnicodeError):
            raise DomainError(422, 'validation_error', 'Cursor is invalid for this session or query')
    else:
        row = db.execute(query.with_only_columns(model.created_at, model.id).order_by(None)
                         .order_by(model.created_at.desc(), model.id.desc()).limit(1)).first()
        if row is None:
            return {'items': [], 'next_cursor': None}
        watermark = (row[0], row[1])
    statement = query.where(tuple_(model.created_at, model.id) <= watermark)
    if after:
        statement = statement.where(tuple_(priority, severity, model.id) > after)
    rows = list(db.scalars(statement.order_by(None).order_by(priority, severity, model.id).limit(limit + 1)))
    token = None
    if len(rows) > limit:
        last = rows[limit - 1]
        state = {'q': query_hash, 'w': [watermark[0].isoformat(), watermark[1]],
                 'a': [PRIORITIES.index(last.data['priority']), SEVERITIES.index(last.data['severity']), last.id]}
        encoded = base64.urlsafe_b64encode(canonical_request(state)).decode().rstrip('=')
        token = encoded + '.' + hmac.new(session_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return {'items': [row.data for row in rows[:limit]], 'next_cursor': token}
