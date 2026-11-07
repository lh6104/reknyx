"""Synthetic Nmap XML cases; these do not establish native capture acceptance."""
import hashlib

import pytest

from reknyx.scanner_integrations import nmap


SAMPLE = b'''<?xml version="1.0"?><!DOCTYPE nmaprun><nmaprun scanner="nmap" version="synthetic"><host><status state="up"/><address addr="192.0.2.1" addrtype="ipv4"/><ports><port protocol="tcp" portid="443"><state state="open"/><service name="https" product="Example"/></port><port protocol="udp" portid="53"><state state="closed"/></port></ports></host><runstats><finished exit="success"/></runstats></nmaprun>'''


def test_service_observation_retains_source_and_is_not_a_finding():
    batch = nmap.parse(SAMPLE)
    assert batch.sha256 == hashlib.sha256(SAMPLE).hexdigest()
    assert batch.producer_version == 'synthetic'
    assert len(batch.observations) == 1
    observation = batch.observations[0]
    assert (observation.address, observation.address_type) == ('192.0.2.1', 'ipv4')
    assert (observation.protocol, observation.port, observation.state) == ('tcp', 443, 'open')
    assert observation.service_name == 'https'
    assert observation.product == 'Example'
    assert observation.raw_locator == '/nmaprun/host[1]/ports/port[1]'
    assert observation.kind == 'service'


@pytest.mark.parametrize('raw', [b'<bad/>', b'<nmaprun>', b'<!DOCTYPE nmaprun SYSTEM "file:///etc/passwd"><nmaprun/>', b'<!DOCTYPE nmaprun [<!ENTITY x "test">]><nmaprun>&x;</nmaprun>'])
def test_rejects_malformed_unsupported_and_entity_documents(raw):
    with pytest.raises(nmap.ParseError):
        nmap.parse(raw)


def test_empty_or_incomplete_results_do_not_claim_success():
    with pytest.raises(nmap.ParseError):
        nmap.parse(b'<nmaprun scanner="nmap" version="synthetic"/>')


def test_document_size_and_depth_limits():
    with pytest.raises(nmap.ParseError, match='resource_limit'):
        nmap.parse(b' ' * (20 * 1024 * 1024 + 1))
    with pytest.raises(nmap.ParseError, match='resource_limit'):
        nmap.parse(b'<nmaprun scanner="nmap" version="x">' + b'<a>' * 65 + b'</a>' * 65 + b'</nmaprun>')


def test_invalid_address_is_a_parse_error():
    with pytest.raises(nmap.ParseError, match='invalid IP address'):
        nmap.parse(SAMPLE.replace(b'addr="192.0.2.1" ', b''))
