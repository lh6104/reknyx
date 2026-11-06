"""Opaque authenticated keyset cursors tied to session, filters and watermark."""
import base64
import hashlib
import hmac
import json

from sqlalchemy import select, tuple_

from reknyx.contracts import canonical_request
from .errors import DomainError


def page(session, model, statement, limit, cursor, binding, session_secret):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise DomainError(422, "validation_error", "Limit must be between 1 and 100")
    query_hash = hashlib.sha256(canonical_request(binding)).hexdigest()[:24]
    if cursor:
        try:
            if len(cursor) > 512:
                raise ValueError()
            encoded, signature = cursor.split(".")
            expected = hmac.new(session_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError()
            state = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if state["q"] != query_hash:
                raise ValueError()
            from datetime import datetime
            watermark = (datetime.fromisoformat(state["w"][0]), state["w"][1])
            after = (datetime.fromisoformat(state["a"][0]), state["a"][1])
        except (ValueError, KeyError, TypeError):
            raise DomainError(422, "validation_error", "Cursor is invalid for this session or query")
    else:
        row = session.execute(statement.with_only_columns(model.created_at, model.id).order_by(model.created_at.desc(), model.id.desc()).limit(1)).first()
        if row is None:
            return {"items": [], "next_cursor": None}
        watermark, after = (row[0], row[1]), None
    query = statement.where(tuple_(model.created_at, model.id) <= watermark)
    if after:
        query = query.where(tuple_(model.created_at, model.id) > after)
    rows = list(session.scalars(query.order_by(model.created_at, model.id).limit(limit + 1)))
    token = None
    if len(rows) > limit:
        last = rows[limit - 1]
        state = {"q": query_hash, "w": [watermark[0].isoformat(), watermark[1]], "a": [last.created_at.isoformat(), last.id]}
        encoded = base64.urlsafe_b64encode(canonical_request(state)).decode().rstrip("=")
        token = encoded + "." + hmac.new(session_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return {"items": [row.data for row in rows[:limit]], "next_cursor": token}
