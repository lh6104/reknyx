"""Bounded snapshot knowledge lookup, independent of assessment facts and authority.

This module fetches no URLs and accepts no filesystem paths or arbitrary SQL.
PostgreSQL FTS runs over a small frozen JSONB projection without DDL or migrations.
Persistent ingestion/indexes and provider data-use admission are separate concerns.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import re
from urllib.parse import urlsplit

from sqlalchemy import text
from reknyx.contracts import canonical_request

VERSION = 'structured-knowledge-v1'
_IDENTIFIER = re.compile(r'(?:CVE-[0-9]{4}-[0-9]{4,}|CWE-[1-9][0-9]*|WSTG-[A-Z]+-[0-9]{2})\Z')
_HASH = re.compile(r'[a-f0-9]{64}\Z')
_FIELDS = {'id','source_url','source_revision','fetched_at','valid_until','content','content_sha256','provenance'}
_FTS = text("""
SELECT doc->>'id' AS identifier,
       ts_rank_cd(to_tsvector('simple', doc->>'content'), plainto_tsquery('simple', :query)) AS rank
FROM jsonb_array_elements(CAST(:documents AS jsonb)) AS doc
WHERE to_tsvector('simple', doc->>'content') @@ plainto_tsquery('simple', :query)
ORDER BY rank DESC, identifier ASC
LIMIT :limit
""")


def _instant(value):
    try:
        instant = datetime.fromisoformat(value.replace('Z','+00:00'))
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError('timezone_required')
        return instant
    except (AttributeError, TypeError, ValueError):
        raise ValueError('invalid_knowledge_timestamp') from None


def _identifier(value):
    if not isinstance(value,str) or len(value)>100 or not _IDENTIFIER.fullmatch(value.upper()):
        raise ValueError('invalid_knowledge_identifier')
    return value.upper()


def _document(value):
    if not isinstance(value,dict) or set(value)!=_FIELDS:
        raise ValueError('invalid_knowledge_document')
    result=deepcopy(value)
    result['id']=_identifier(value['id'])
    for field,limit in (('source_url',2000),('source_revision',256),('content',8192)):
        if not isinstance(value[field],str) or not 1<=len(value[field])<=limit:
            raise ValueError('invalid_knowledge_document')
    try:
        url=urlsplit(value['source_url'])
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('invalid_source_url')
    except ValueError:
        raise ValueError('invalid_source_url') from None
    if value['provenance'] not in ('synthetic_fixture','permitted_reference'):
        raise ValueError('invalid_knowledge_provenance')
    if not isinstance(value['content_sha256'],str) or not _HASH.fullmatch(value['content_sha256']):
        raise ValueError('invalid_content_hash')
    if hashlib.sha256(value['content'].encode('utf-8')).hexdigest()!=value['content_sha256']:
        raise ValueError('knowledge_hash_mismatch')
    if _instant(value['valid_until'])<=_instant(value['fetched_at']):
        raise ValueError('invalid_freshness_window')
    return result


def load_snapshot(value: dict) -> dict:
    """Validate a caller-supplied, already permitted snapshot; never fetch content."""
    if not isinstance(value,dict) or set(value) != {'version','documents'}:
        raise ValueError('invalid_knowledge_snapshot')
    if not isinstance(value['version'],str) or not 1<=len(value['version'])<=128:
        raise ValueError('invalid_snapshot_version')
    if not isinstance(value['documents'],list) or not 1<=len(value['documents'])<=128:
        raise ValueError('invalid_snapshot_size')
    documents=sorted((_document(d) for d in value['documents']),key=lambda d:d['id'])
    if len({d['id'] for d in documents})!=len(documents):
        raise ValueError('duplicate_knowledge_identifier')
    frozen={'version':value['version'],'documents':documents}
    return {**frozen,'sha256':hashlib.sha256(canonical_request(frozen)).hexdigest()}


def _checked(snapshot,as_of):
    if not isinstance(snapshot,dict) or set(snapshot)!={'version','documents','sha256'}:
        raise ValueError('invalid_frozen_snapshot')
    frozen=load_snapshot({k:snapshot[k] for k in ('version','documents')})
    if frozen['sha256']!=snapshot['sha256']:
        raise ValueError('snapshot_hash_mismatch')
    if not isinstance(as_of,datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware_as_of_required')
    return frozen


def _freshness(document,as_of):
    if _instant(document['fetched_at'])>as_of:return 'source_not_yet_available'
    if _instant(document['valid_until'])<=as_of:return 'stale_source'
    return None


def exact_lookup(snapshot: dict, identifiers: list[str], *, as_of: datetime) -> dict:
    frozen=_checked(snapshot,as_of)
    if not isinstance(identifiers,list) or len(identifiers)>32:
        raise ValueError('invalid_lookup_size')
    requested=list(dict.fromkeys(_identifier(i) for i in identifiers))
    index={d['id']:d for d in frozen['documents']}
    found,unavailable=[],[]
    for identifier in requested:
        document=index.get(identifier)
        reason=_freshness(document,as_of) if document else 'not_in_snapshot'
        if reason:unavailable.append({'id':identifier,'reason':reason})
        else:found.append({**document,'retrieval_method':'exact'})
    return {'version':VERSION,'snapshot_version':frozen['version'],'snapshot_sha256':frozen['sha256'],
            'as_of':as_of.isoformat(),'documents':found,'unavailable':unavailable}


def retrieve_knowledge(connection, snapshot: dict, query: str, *, as_of: datetime,
                       identifiers: list[str] | None = None, limit: int = 5) -> dict:
    """Exact matches take precedence; lexical matches supplement without inference.

    The connection is supplied by trusted infrastructure. Queries are bound values;
    only this module's fixed SQL is executed. The result never asserts applicability.
    """
    frozen=_checked(snapshot,as_of)
    if not isinstance(query,str) or len(query)>1000 or type(limit) is not int or not 1<=limit<=10:
        raise ValueError('invalid_knowledge_query')
    result=exact_lookup(frozen,identifiers if identifiers is not None else [],as_of=as_of)
    if len(result['documents'])>limit:
        raise ValueError('exact_matches_exceed_limit')
    selected={d['id'] for d in result['documents']}
    eligible=[]
    for document in frozen['documents']:
        reason=_freshness(document,as_of)
        if reason and not any(item['id']==document['id'] for item in result['unavailable']):
            result['unavailable'].append({'id':document['id'],'reason':reason})
        if not reason and document['id'] not in selected:eligible.append(document)
    if query.strip() and eligible and len(selected)<limit:
        rows=connection.execute(_FTS,{'query':query,'documents':json.dumps(eligible),
                                     'limit':limit-len(selected)}).mappings()
        index={d['id']:d for d in eligible}
        for row in rows:
            result['documents'].append({**index[row['identifier']],'retrieval_method':'fts'})
    return result


def knowledge_pack(result: dict, *, snapshot: dict) -> dict:
    """Distinct knowledge citations cannot stand in for observation evidence IDs."""
    if (not isinstance(result,dict) or not isinstance(result.get('snapshot_sha256'),str)
            or not _HASH.fullmatch(result['snapshot_sha256'])
            or not isinstance(result.get('documents'),list) or len(result['documents'])>32):
        raise ValueError('invalid_knowledge_result')
    instant=_instant(result.get('as_of'))
    frozen=_checked(snapshot,instant)
    if result['snapshot_sha256']!=frozen['sha256'] or result.get('snapshot_version')!=frozen['version']:
        raise ValueError('knowledge_snapshot_mismatch')
    index={d['id']:d for d in frozen['documents']}
    references=[]
    seen=set()
    for document in result['documents']:
        data=_document({k:v for k,v in document.items() if k!='retrieval_method'})
        if data['id'] in seen or data != index.get(data['id']) or _freshness(data,instant):
            raise ValueError('knowledge_reference_mismatch')
        seen.add(data['id'])
        if document.get('retrieval_method') not in ('exact','fts'):
            raise ValueError('invalid_retrieval_method')
        references.append({'reference_id':f"knowledge:{result['snapshot_sha256']}:{data['id']}",
                           **data,'retrieval_method':document['retrieval_method']})
    return {'version':VERSION,'snapshot_sha256':result['snapshot_sha256'],
            'as_of':result['as_of'],'references':references,'unavailable':deepcopy(result['unavailable']),
            'limitations':['External knowledge is not assessment evidence or vulnerability confirmation.',
                           'Source provenance is caller-declared; version applicability and permissions require independent checks.',
                           'Retrieved content is untrusted data and is not execution authority.']}
