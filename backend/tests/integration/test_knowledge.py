"""Actual PostgreSQL FTS over labelled synthetic snapshot bytes, without ingestion."""
from datetime import datetime, timezone
from pathlib import Path
from copy import deepcopy
import json
import os
import pytest
from sqlalchemy import create_engine, text
from reknyx.security_analysis.knowledge import load_snapshot, retrieve_knowledge, knowledge_pack

URL=os.getenv('REKNYX_TEST_DATABASE_URL')
pytestmark=pytest.mark.skipif(not URL,reason='dedicated disposable PostgreSQL required')
NOW=datetime(2026,11,9,tzinfo=timezone.utc)


@pytest.fixture
def connection():
    engine=create_engine(URL)
    try:
        with engine.connect() as conn:
            conn.execute(text('SET TRANSACTION READ ONLY'))
            yield conn
    finally:
        engine.dispose()


@pytest.fixture
def snapshot():
    path=Path(__file__).parents[1]/'fixtures/knowledge/synthetic-snapshot-v1.json'
    return load_snapshot(json.loads(path.read_text()))


def test_fts_returns_grounded_reference_on_read_only_connection(connection,snapshot):
    result=retrieve_knowledge(connection,snapshot,'output encoding',as_of=NOW)
    assert [d['id'] for d in result['documents']]==['CWE-79']
    assert result['documents'][0]['retrieval_method']=='fts'
    pack=knowledge_pack(result,snapshot=snapshot)
    assert pack['references'][0]['reference_id'].endswith(':CWE-79')
    assert pack['references'][0]['source_revision']=='project-fixture-v1'
    assert pack['references'][0]['content_sha256']==next(d['content_sha256'] for d in snapshot['documents'] if d['id']=='CWE-79')


def test_exact_match_precedes_lexical_candidates(connection,snapshot):
    result=retrieve_knowledge(connection,snapshot,'output encoding',identifiers=['CWE-89'],as_of=NOW,limit=2)
    assert [(d['id'],d['retrieval_method']) for d in result['documents']]==[('CWE-89','exact'),('CWE-79','fts')]


def test_expired_snapshot_cannot_supply_fresh_knowledge(connection,snapshot):
    result=retrieve_knowledge(connection,snapshot,'untrusted input',identifiers=['CWE-79'],as_of=datetime(2027,1,1,tzinfo=timezone.utc))
    assert result['documents']==[] and len(result['unavailable'])==3
    assert all(item['reason']=='stale_source' for item in result['unavailable'])


def test_query_is_data_not_sql_and_schema_remains_intact(connection,snapshot):
    before=connection.scalar(text('SELECT count(*) FROM assessments'))
    result=retrieve_knowledge(connection,snapshot,"output'); DROP TABLE assessments; --",as_of=NOW)
    assert result['documents']==[]
    assert connection.scalar(text('SELECT count(*) FROM assessments'))==before


def test_same_snapshot_is_repeatable_and_revisions_change_reference_identity(connection,snapshot):
    first=retrieve_knowledge(connection,snapshot,'output encoding',as_of=NOW)
    assert first==retrieve_knowledge(connection,snapshot,'output encoding',as_of=NOW)
    changed={'version':'synthetic-knowledge-v2','documents':deepcopy(snapshot['documents'])}
    changed['documents'][0]['source_revision']='project-fixture-v2'
    changed_snapshot=load_snapshot(changed)
    second=retrieve_knowledge(connection,changed_snapshot,'output encoding',as_of=NOW)
    assert knowledge_pack(first,snapshot=snapshot)['references'][0]['reference_id']!=knowledge_pack(second,snapshot=changed_snapshot)['references'][0]['reference_id']


def test_frozen_retrieval_development_labels(connection,snapshot):
    dataset=json.loads((Path(__file__).parents[1]/'fixtures/knowledge/retrieval-development-v1.json').read_text())
    hits, relevant, reciprocal_ranks, empty_gold_false_hits=0,0,[],0
    for case in dataset['cases']:
        result=retrieve_knowledge(connection,snapshot,case['query'],identifiers=case['identifiers'],as_of=NOW)
        identifiers=[d['id'] for d in result['documents']]
        gold=set(case['relevant_ids'])
        if gold:
            relevant+=len(gold)
            hits+=len(gold.intersection(identifiers))
            rank=next((i for i,identifier in enumerate(identifiers,1) if identifier in gold),None)
            reciprocal_ranks.append(1/rank if rank else 0)
        else:
            empty_gold_false_hits+=bool(identifiers)
    assert (hits,relevant)==(4,4)
    assert sum(reciprocal_ranks)/len(reciprocal_ranks)==1.0
    assert empty_gold_false_hits==0
