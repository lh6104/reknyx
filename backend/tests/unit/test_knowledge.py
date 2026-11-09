"""Bounded source-grounded knowledge is distinct from assessment evidence."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import pytest
from reknyx.security_analysis.knowledge import load_snapshot, exact_lookup, knowledge_pack

NOW=datetime(2026,11,9,tzinfo=timezone.utc)


def document(identifier='CWE-79', **changes):
    content='Project-authored synthetic note about output encoding and untrusted input.'
    return {'id':identifier,'source_url':'https://cwe.mitre.org/data/definitions/79.html',
        'source_revision':'fixture-v1','fetched_at':'2026-11-08T00:00:00Z',
        'valid_until':'2026-12-01T00:00:00Z','content':content,
        'content_sha256':hashlib.sha256(content.encode()).hexdigest(),
        'provenance':'synthetic_fixture', **changes}


def snapshot(*docs):
    return {'version':'synthetic-knowledge-v1','documents':list(docs or [document()])}


def test_snapshot_hash_and_copy_are_stable():
    value=snapshot();frozen=load_snapshot(value)
    value['documents'][0]['content']='changed'
    assert frozen['documents'][0]['content']!='changed'
    assert frozen['sha256']==load_snapshot(snapshot())['sha256']
    assert load_snapshot(snapshot(document(source_revision='v2')))['sha256']!=frozen['sha256']


@pytest.mark.parametrize('change',[{'content_sha256':'0'*64},{'source_url':'file:///etc/passwd'},
    {'source_url':'https://user:secret@example.org/private'}, {'source_url':'https://example.org/?token=secret'},
    {'fetched_at':'2026-11-08'},{'provenance':'unverified'},{'id':'run shell'},
    {'valid_until':'2026-10-01T00:00:00Z'}])
def test_invalid_document_is_rejected(change):
    with pytest.raises(ValueError):load_snapshot(snapshot(document(**change)))


def test_duplicate_and_unbounded_documents_are_rejected():
    with pytest.raises(ValueError):load_snapshot(snapshot(document(),document()))
    with pytest.raises(ValueError):load_snapshot({'version':'v1','documents':[document()]*129})


def test_lookup_exact_ids_and_freshness_are_explicit():
    frozen=load_snapshot(snapshot())
    result=exact_lookup(frozen,['cwe-79','CVE-2026-1234'],as_of=NOW)
    assert [d['id'] for d in result['documents']]==['CWE-79']
    assert result['unavailable']==[{'id':'CVE-2026-1234','reason':'not_in_snapshot'}]
    stale=exact_lookup(frozen,['CWE-79'],as_of=datetime(2027,1,1,tzinfo=timezone.utc))
    assert stale['documents']==[] and stale['unavailable'][0]['reason']=='stale_source'
    future=exact_lookup(frozen,['CWE-79'],as_of=datetime(2026,1,1,tzinfo=timezone.utc))
    assert future['unavailable'][0]['reason']=='source_not_yet_available'


def test_knowledge_refs_do_not_claim_vulnerability_or_authority():
    frozen=load_snapshot(snapshot())
    result=exact_lookup(frozen,['CWE-79'],as_of=NOW)
    pack=knowledge_pack(result,snapshot=frozen)
    assert pack['references'][0]['reference_id'].startswith('knowledge:')
    assert pack['references'][0]['provenance']=='synthetic_fixture'
    assert pack['references'][0]['content_sha256']==document()['content_sha256']
    assert 'observations' not in pack and 'scope' not in pack
    assert 'not assessment evidence' in pack['limitations'][0]


def test_digest_tampering_and_naive_clock_are_rejected():
    frozen=load_snapshot(snapshot());frozen['documents'][0]['source_revision']='tampered'
    with pytest.raises(ValueError):exact_lookup(frozen,['CWE-79'],as_of=NOW)
    with pytest.raises(ValueError):exact_lookup(load_snapshot(snapshot()),['CWE-79'],as_of=datetime(2026,11,9))


def test_knowledge_pack_rejects_content_rewritten_under_existing_snapshot_reference():
    frozen=load_snapshot(snapshot())
    result=exact_lookup(frozen,['CWE-79'],as_of=NOW)
    result['documents'][0]['content']='Replacement content'
    result['documents'][0]['content_sha256']=hashlib.sha256(b'Replacement content').hexdigest()
    with pytest.raises(ValueError):knowledge_pack(result,snapshot=frozen)
