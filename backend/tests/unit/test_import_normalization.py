"""Synthetic parser-to-contract checks, without network or persistence."""
import json
from uuid import uuid4

import pytest

from reknyx.evidence.imports import normalize


def test_zap_observation_and_finding_keep_source_identity():
    raw = json.dumps({'@programName': 'ZAP', '@version': 'synthetic', 'site': [
        {'@name': 'https://lab.example', 'alerts': [
            {'pluginid': '1', 'alert': 'Synthetic alert', 'riskcode': '2',
             'confidence': '3', 'count': '1', 'solution': 'Review configuration',
             'instances': [{'uri': 'https://lab.example/login', 'method': 'GET'}]}]}]}).encode()
    source = {'assessment_id': str(uuid4()), 'artifact_id': str(uuid4()),
              'observed_at': None, 'ingested_at': '2026-11-07T00:00:00Z'}
    batch = normalize('zap_json', raw, source)
    observation, finding = batch['observations'][0], batch['findings'][0]
    assert observation['artifact_id'] == source['artifact_id']
    assert observation['asset']['authorized_asset_id'] is None
    assert observation['raw_confidence'] == '3'
    assert finding['observation_ids'] == [observation['id']]
    assert finding['validation_status'] == 'suspected'
    assert finding['analyst_disposition'] == 'needs_review'
    assert finding['priority'] == 'review_next'
    assert finding['cvss'] is None


def test_unsupported_kind_is_explicit():
    with pytest.raises(ValueError, match='unsupported_format'):
        normalize('greenbone_xml', b'<x/>', {})


def test_isolated_parser_returns_rejection_without_network_or_storage():
    from reknyx.orchestration.import_worker import isolated_parse
    result = isolated_parse('zap_json', b'{"invalid":true}', {})
    assert result == {'failure_code': 'parser_rejected'}


def test_historical_ipv6_udp_observation_never_becomes_live_scope_or_finding():
    raw = b'<nmaprun scanner="nmap" version="synthetic"><host><address addr="2001:db8::1" addrtype="ipv6"/><ports><port protocol="udp" portid="53"><state state="open"/></port></ports></host><runstats><finished exit="success"/></runstats></nmaprun>'
    source = {'assessment_id': str(uuid4()), 'artifact_id': str(uuid4()),
              'observed_at': None, 'ingested_at': '2026-11-07T00:00:00Z'}
    batch = normalize('nmap_xml', raw, source)
    assert batch['findings'] == []
    observation = batch['observations'][0]
    assert observation['asset']['address_family'] == 'ipv6'
    assert observation['asset']['authorized_asset_id'] is None
    assert observation['service']['transport'] == 'udp'
    assert observation['raw_severity'] is None
