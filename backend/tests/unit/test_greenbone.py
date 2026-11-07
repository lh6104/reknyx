"""Synthetic GMP-shaped cases; no scanner run or native-capture acceptance."""
from pathlib import Path
import hashlib
from uuid import uuid4
import pytest

RAW = (Path(__file__).parents[1] / 'fixtures/greenbone/synthetic-report.xml').read_bytes()


def test_result_identity_and_native_attributes_survive():
    from reknyx.scanner_integrations.greenbone import parse
    batch = parse(RAW)
    assert batch.sha256 == hashlib.sha256(RAW).hexdigest()
    item = batch.observations[0]
    assert item.native_id == 'synthetic-result-1'
    assert item.raw_locator == '/report/results/result[1]'
    assert item.address == '192.0.2.10'
    assert (item.port, item.protocol) == (443, 'tcp')
    assert item.raw_confidence == '80' and item.qod_type == 'remote_banner'
    assert item.severity == 'high' and item.raw_severity == '7.5'
    assert item.cve_ids == ('CVE-2099-12345',)
    assert batch.outcome == 'succeeded'


def test_wrapper_and_empty_report():
    from reknyx.scanner_integrations.greenbone import parse
    wrapped = b'<get_reports_response status="200"><report extension="xml">'+RAW+b'</report></get_reports_response>'
    assert parse(wrapped).observations[0].raw_locator == '/get_reports_response/report/report/results/result[1]'
    empty = RAW[:RAW.index(b'<results>')] + b'<results/></report>'
    assert parse(empty).observations == ()


@pytest.mark.parametrize('raw', [b'<wrong/>', b'<report/>', RAW.replace(b'Done', b'Running'), RAW.replace(b'443/tcp', b'99999/tcp'), RAW.replace(b'7.5',b'NaN'), b'<!DOCTYPE report [<!ENTITY x SYSTEM "file:///etc/passwd">]><report>&x;</report>', b'<!DOCTYPE report SYSTEM "https://example.invalid/x"><report/>', RAW+RAW])
def test_reject_unsafe_incomplete_or_malformed_input(raw):
    from reknyx.scanner_integrations.greenbone import parse, ParseError
    with pytest.raises(ParseError): parse(raw)


def test_information_and_partial_exports_do_not_invent_vulnerabilities():
    from reknyx.scanner_integrations.greenbone import parse
    raw = RAW.replace(b'<severity>7.5</severity>', b'<severity>0.0</severity>').replace(b'<threat>High</threat>',b'<threat>Log</threat>')
    assert parse(raw).observations[0].kind == 'informational'
    limited = RAW.replace(b'<results>', b'<result_count><filtered>2</filtered></result_count><results>')
    assert parse(limited).outcome == 'partial'


def test_normalized_source_fields_are_attributed_and_validation_stays_suspected():
    from reknyx.evidence.imports import normalize
    source={'assessment_id':str(uuid4()),'artifact_id':str(uuid4()),'observed_at':None,'ingested_at':'2026-11-08T00:00:00Z'}
    result=normalize('greenbone_xml',RAW,source)
    o,f=result['observations'][0],result['findings'][0]
    assert o['source_tool']=='greenbone' and o['asset']['authorized_asset_id'] is None
    assert o['raw_confidence']=='80' and o['raw_severity']=='7.5'
    assert f['validation_status']=='suspected' and f['analyst_disposition']=='needs_review'
    assert f['cve_ids']==['CVE-2099-12345']
    assert f['cvss']==7.5 and f['cvss_version']=='3.1'
    assert 'QoD' in f['confidence_method']
    assert f['observation_ids']==[o['id']]


def test_resource_limits_and_missing_cvss_pair(monkeypatch):
    from reknyx.scanner_integrations import greenbone
    with pytest.raises(greenbone.ParseError, match='resource_limit'):
        greenbone.parse(b'<' + b'x' * greenbone.MAX_BYTES)
    with pytest.raises(greenbone.ParseError, match='resource_limit'):
        greenbone.parse(b'<r>'*65+b'</r>'*65)
    monkeypatch.setattr(greenbone,'MAX_RECORDS',0)
    with pytest.raises(greenbone.ParseError,match='resource_limit'): greenbone.parse(RAW)
    monkeypatch.setattr(greenbone,'MAX_RECORDS',10000)
    item=greenbone.parse(RAW.replace(b'<score>7.5</score>',b'')).observations[0]
    assert item.cvss is item.cvss_vector is item.cvss_version is None
    assert 'CVSS:3.1' in item.native_nvt_xml


def test_informational_results_normalize_without_findings():
    from reknyx.evidence.imports import normalize
    source={'assessment_id':str(uuid4()),'artifact_id':str(uuid4()),'observed_at':None,'ingested_at':'2026-11-08T00:00:00Z'}
    batch=normalize('greenbone_xml',RAW.replace(b'<severity>7.5</severity>',b'<severity>0.0</severity>'),source)
    assert batch['observations'][0]['kind']=='informational'
    assert batch['findings']==[]


def test_negative_result_and_general_udp_preserve_native_data_without_findings():
    from reknyx.evidence.imports import normalize
    source={'assessment_id':str(uuid4()),'artifact_id':str(uuid4()),'observed_at':None,'ingested_at':'2026-11-08T00:00:00Z'}
    raw=RAW.replace(b'<severity>7.5</severity>',b'<severity>-1.0</severity>').replace(b'443/tcp',b'general/udp').replace(b'192.0.2.10',b'2001:db8::10')
    result=normalize('greenbone_xml',raw,source)
    assert result['outcome']=='partial' and result['findings']==[]
    o=result['observations'][0]
    assert o['service']['port'] is None and o['service']['transport']=='udp'
    assert o['asset']['address_family']=='ipv6'
    assert '<severity>-1.0</severity>' in result['native'][0]['native_result_xml']


def test_native_cvss_origin_and_qod_validation():
    from reknyx.scanner_integrations.greenbone import parse,ParseError
    raw=RAW.replace(b'<score>7.5</score>',b'<score>7.5</score><origin>synthetic source</origin>')
    assert 'synthetic source' in parse(raw).observations[0].cvss_source
    with pytest.raises(ParseError):parse(RAW.replace(b'<value>80</value>',b'<value>101</value>'))
    # UTF-16 declarations must receive the same entity rejection as UTF-8.
    with pytest.raises(ParseError):parse('<!DOCTYPE report [<!ENTITY e "bad">]><report>&e;</report>'.encode('utf-16'))
