"""Synthetic format cases only; no native scanner acceptance is claimed."""
import copy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend/src'))


def parser():
    assert (ROOT / 'backend/src/reknyx/scanner_integrations/zap.py').exists()
    return importlib.import_module('reknyx.scanner_integrations.zap')


def report():
    return {'@programName': 'ZAP', '@version': 'synthetic', 'site': [
        {'@name': 'http://lab.example:8080', '@host': 'lab.example', '@port': '8080', '@ssl': 'false',
         'alerts': [{'pluginid': '10020', 'alertRef': '10020-1', 'alert': 'Synthetic alert',
                     'riskcode': '2', 'confidence': '4', 'count': '2',
                     'desc': '<script>untrusted()</script>', 'solution': 'Review configuration.',
                     'instances': [{'id': '-1', 'uri': 'http://lab.example:8080/login', 'method': 'GET', 'param': '', 'evidence': '<b>raw</b>'},
                                   {'id': '-1', 'uri': 'http://lab.example:8080/app', 'method': 'POST', 'param': 'input'}]}]}]}


def parse(value):
    return parser().parse(json.dumps(value).encode())


def test_instances_keep_source_identity_and_uncertainty():
    batch = parse(report())
    assert len(batch.observations) == 2
    first, second = batch.observations
    assert first.raw_locator == '/site/0/alerts/0/instances/0'
    assert first.rule_id == 'zap:10020-1'
    assert first.native_id == second.native_id == '-1'
    assert first.parameter is None and second.parameter == 'input'
    assert first.severity == 'medium' and first.raw_confidence == '4'
    assert first.validation_status == 'suspected'
    assert first.description == '<script>untrusted()</script>'
    assert first.evidence == '<b>raw</b>'
    assert batch.observed_at is None
    assert batch.outcome == 'succeeded'


@pytest.mark.parametrize('value', [[{'alert': 'API'}], {'alerts': []}, {'site': 'bad'}, {'site': []}])
def test_rejects_other_formats(value):
    with pytest.raises(parser().ParseError):
        parse(value)


@pytest.mark.parametrize('raw', [b'{', b'{"site":[],"site":[]}', b'{"x":NaN}', b'\xff'])
def test_rejects_malformed_or_ambiguous_json(raw):
    with pytest.raises(parser().ParseError):
        parser().parse(raw)


def test_cross_origin_instance_is_diagnosed_without_disappearing():
    value = report()
    value['site'][0]['alerts'][0]['instances'][0]['uri'] = 'http://outside.example/'
    batch = parse(value)
    assert batch.outcome == 'partial'
    assert len(batch.observations) == 1
    assert any(w.code == 'origin_mismatch' for w in batch.warnings)


def test_unknown_severity_and_count_discrepancy():
    value = report()
    value['site'][0]['alerts'][0].update(riskcode='99', count='3')
    batch = parse(value)
    assert all(o.severity == 'unknown' and o.raw_risk == '99' for o in batch.observations)
    assert {'unknown_risk', 'count_mismatch'} <= {w.code for w in batch.warnings}


def test_empty_alerts_is_empty_not_asset_safe():
    value = report()
    value['site'][0]['alerts'] = []
    assert parse(value).observations == ()


def test_nonempty_alert_without_instances_has_warning():
    value = report()
    value['site'][0]['alerts'][0]['instances'] = []
    assert parse(value).outcome == 'partial'


def test_limits_are_hard_rejections():
    with pytest.raises(parser().ParseError, match='resource_limit'):
        parser().parse(b' ' * (20 * 1024 * 1024 + 1))
    with pytest.raises(parser().ParseError, match='resource_limit'):
        parser().parse(b'[' * 65 + b']' * 65)


def test_source_input_is_not_changed():
    value = report()
    before = copy.deepcopy(value)
    parse(value)
    assert value == before
