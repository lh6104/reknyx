"""Actual PostgreSQL ordinal finding pagination on synthetic records."""
from datetime import timedelta
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from reknyx.findings.pagination import page_findings
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.models import Assessment, FindingRecord
from reknyx.shared.time import now

URL = os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='isolated PostgreSQL URL not supplied')


def test_signed_ordinal_pages_and_query_session_isolation():
    engine = create_engine(URL)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection) as db:
            aid, instant = str(uuid4()), now()
            db.add(Assessment(id=aid, created_at=instant, data={}))
            db.flush()
            cases = json.loads((Path(__file__).resolve().parents[3] / 'contracts/examples/schema-cases.json').read_text())['cases']
            base = next(c['payload'] for c in cases if c['id'] == 'valid-Finding')
            ids = [str(uuid4()) for _ in range(5)]
            expected = []
            for index, (priority, severity) in enumerate([('routine', 'low'), ('review_first', 'high'), ('review_next', 'medium'), ('review_first', 'critical')]):
                data = {**base, 'id': ids[index], 'assessment_id': aid, 'priority': priority, 'severity': severity}
                db.add(FindingRecord(id=ids[index], assessment_id=aid, created_at=instant + timedelta(microseconds=index), data=data))
            db.flush()
            query = select(FindingRecord).where(FindingRecord.assessment_id == aid)
            first = page_findings(db, FindingRecord, query, 2, None, ['actor', aid], 'secret')
            assert [row['id'] for row in first['items']] == [ids[3], ids[1]]
            assert first['next_cursor']
            for cursor, binding, secret in [(first['next_cursor'] + 'x', ['actor', aid], 'secret'), (first['next_cursor'], ['other', aid], 'secret'), (first['next_cursor'], ['actor', aid], 'other-session')]:
                with pytest.raises(DomainError):
                    page_findings(db, FindingRecord, query, 2, cursor, binding, secret)
            db.add(FindingRecord(id=ids[4], assessment_id=aid, created_at=instant + timedelta(seconds=1), data={**base, 'id': ids[4], 'assessment_id': aid, 'priority': 'review_next', 'severity': 'high'}))
            db.flush()
            second = page_findings(db, FindingRecord, query, 2, first['next_cursor'], ['actor', aid], 'secret')
            assert [row['id'] for row in second['items']] == [ids[2], ids[0]]
            assert second['next_cursor'] is None
            filtered = page_findings(db, FindingRecord, query.where(FindingRecord.data['priority'].astext == 'review_first'), 100, None, ['actor', aid, 'review_first'], 'secret')
            assert [row['id'] for row in filtered['items']] == [ids[3], ids[1]]
        transaction.rollback()
    engine.dispose()
