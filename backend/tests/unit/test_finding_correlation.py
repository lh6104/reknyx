"""Compatibility uses source context, never title/CVE similarity alone."""
from copy import deepcopy

import pytest

from reknyx.findings.correlation import compatibility_reason


def source():
    return {'observation': {'id': 'one', 'assessment_id': 'assessment', 'kind': 'vulnerability',
        'source_tool': 'zap', 'artifact_id': 'capture', 'observed_at': None,
        'asset': {'address_family': 'ipv4', 'canonical_identity': '192.0.2.10'},
        'service': {'transport': 'tcp', 'port': 80, 'scheme': 'http', 'observation_ids': ['one']},
        'location': {'scheme': 'http', 'host': '192.0.2.10', 'port': 80, 'path': '/',
                     'raw_url': 'http://192.0.2.10/?a=1', 'method': 'GET', 'parameter': None, 'redacted': False}},
        'native': {'rule_id': 'zap:fixture', 'severity': 'medium'},
        'artifact': {'assessment_id': 'assessment', 'sha256': 'a'*64,
                     'provenance': 'synthetic_fixture', 'historical': True}}


def test_matching_source_instances_ignore_service_membership_ids():
    a = source(); b = deepcopy(a)
    b['observation']['id'] = 'two'
    b['observation']['service']['observation_ids'] = ['two']
    assert compatibility_reason(a, b) is None


@pytest.mark.parametrize('section,key,value', [
    ('observation', 'assessment_id', 'foreign'),
    ('observation', 'kind', 'service'),
    ('observation', 'source_tool', 'greenbone'),
    ('native', 'rule_id', 'zap:different'),
    ('native', 'rule_id', None),
    ('artifact', 'assessment_id', 'foreign'),
    ('artifact', 'provenance', 'authorized_native_capture'),
])
def test_incompatible_or_unknown_source_is_rejected(section, key, value):
    a = source(); b = deepcopy(a); b[section][key] = value
    assert compatibility_reason(a, b) is not None


@pytest.mark.parametrize('section,key,value', [
    ('asset', 'canonical_identity', '192.0.2.11'),
    ('service', 'port', 443), ('service', 'transport', 'unknown'),
    ('service', 'port', None), ('location', 'path', '/other'),
    ('location', 'parameter', 'other'), ('location', 'method', 'POST'),
    ('location', 'raw_url', 'http://192.0.2.10/?a=2'),
    ('location', 'redacted', True),
])
def test_asset_service_and_full_request_location_must_match(section, key, value):
    a = source(); b = deepcopy(a); b['observation'][section][key] = value
    assert compatibility_reason(a, b) is not None


def test_separate_capture_requires_equal_known_observation_time():
    a = source(); b = deepcopy(a)
    b['observation']['artifact_id'] = 'other'
    b['artifact']['sha256'] = 'b'*64
    assert compatibility_reason(a, b) is not None
    a['observation']['observed_at'] = '2026-11-08T00:00:00Z'
    b['observation']['observed_at'] = '2026-11-08T07:00:00+07:00'
    assert compatibility_reason(a, b) is None
    b['observation']['observed_at'] = '2026-11-08T00:00:01Z'
    assert compatibility_reason(a, b) is not None
