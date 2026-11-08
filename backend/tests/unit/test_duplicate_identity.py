"""Exact native-capture identity, not probabilistic issue similarity."""
from copy import deepcopy

import pytest

from reknyx.findings.duplicate_identity import capture_fingerprint, link_duplicate, DuplicatePublicationError


def source():
    return ({'assessment_id':'assessment','id':'observation','artifact_id':'artifact',
             'raw_locator':'/results/result[1]','source_tool':'greenbone','observed_at':None,
             'asset':{'address_family':'ipv4','canonical_identity':'192.0.2.10'},
             'service':{'transport':'tcp','port':443,'scheme':None,'observation_ids':['observation']},
             'location':None},
            {'rule_id':'greenbone:fixture'},
            {'sha256':'a'*64,'provenance':'synthetic_fixture','historical':True},
            'synthetic-parser-v1')


def test_repeat_capture_ignores_generated_ids_ingestion_labels_and_service_citation_ids():
    a=source();b=deepcopy(a)
    b[0].update(id='new',artifact_id='new',ingested_at='later',source_label='other')
    b[0]['service']['observation_ids']=['new']
    assert capture_fingerprint(*a)==capture_fingerprint(*b)


@pytest.mark.parametrize('part,key,value',[
    (0,'assessment_id','foreign'),(0,'raw_locator','/results/result[2]'),
    (0,'source_tool','zap'),(0,'observed_at','2026-11-08T00:00:00Z'),
    (1,'rule_id','greenbone:other'),(2,'sha256','b'*64),
    (2,'provenance','public_format_reference'),(2,'historical',False),
])
def test_distinct_capture_identity_does_not_collapse(part,key,value):
    a=source();b=deepcopy(a);b[part][key]=value
    assert capture_fingerprint(*a)!=capture_fingerprint(*b)


def test_parser_version_and_full_location_affect_identity():
    a=source();b=deepcopy(a)
    assert capture_fingerprint(*a)!=capture_fingerprint(*b[:3],'different-parser')
    b[0]['location']={'raw_url':'https://192.0.2.10/?q=different'}
    assert capture_fingerprint(*a)!=capture_fingerprint(*b)


def test_equivalent_known_time_is_canonicalized_without_rounding():
    a=source();b=deepcopy(a)
    a[0]['observed_at']='2026-11-08T00:00:00.001Z'
    b[0]['observed_at']='2026-11-08T07:00:00.001+07:00'
    assert capture_fingerprint(*a)==capture_fingerprint(*b)
    b[0]['observed_at']='2026-11-08T07:00:00.002+07:00'
    assert capture_fingerprint(*a)!=capture_fingerprint(*b)


def test_duplicate_membership_preserves_reviewed_fields_and_has_a_bound():
    finding={'revision':4,'observation_ids':['old'],'correlation_reason':'Original source retained.',
             'severity':'high','analyst_disposition':'accepted','validation_status':'suspected'}
    original=deepcopy(finding)
    linked=link_duplicate(finding,'new')
    assert linked['revision']==5 and linked['observation_ids']==['old','new']
    assert linked['analyst_disposition']=='accepted' and linked['validation_status']=='suspected'
    assert finding==original
    finding['observation_ids']=[str(i) for i in range(10000)]
    with pytest.raises(DuplicatePublicationError,match='finding_membership_limit'):
        link_duplicate(finding,'new')
