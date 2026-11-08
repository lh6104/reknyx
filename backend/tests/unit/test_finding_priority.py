"""Frozen contract ordinal comparisons, not a model accuracy benchmark."""
import json
from pathlib import Path

import pytest

from reknyx.findings.priority import prioritize

CASES = json.loads(Path('contracts/examples/priority-cases.json').read_text())['cases']


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['id'])
def test_priority_matches_frozen_contract_rules(case):
    original = json.dumps(case['finding'], sort_keys=True)
    result = prioritize(case['finding'])
    assert result['priority'] == case['expected_priority']
    assert result['risk_rule_version'] == 'ordinal-v1'
    assert result['priority_reasons']
    assert set(result) == {'priority', 'priority_reasons', 'risk_rule_version'}
    assert json.dumps(case['finding'], sort_keys=True) == original
