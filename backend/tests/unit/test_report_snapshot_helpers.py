"""Report job helpers use synthetic frozen snapshots, without scanner traffic."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from reknyx.reporting.service import build_snapshot, render_isolated
from reknyx.contracts import validate


def fixture(name):
    root = Path(__file__).resolve().parents[3]
    cases = json.loads((root / 'contracts/examples/schema-cases.json').read_text())['cases']
    return deepcopy(next(c['payload'] for c in cases if c['id'] == 'valid-' + name))


def test_snapshot_counts_and_severity_are_derived_from_frozen_findings():
    source = fixture('ReportSnapshot')
    assessment = {'id': source['assessment_id'], 'state_revision': 4,
                  'scope_version': source['scope_version'], 'created_at': source['created_at']}
    snapshot = build_snapshot(source['id'], assessment, source['scope'], source['created_by'],
                              source['created_at'], source['findings'], source['observations'],
                              source['artifacts'], source['reviews'], [], True)
    validate('ReportSnapshot', snapshot)
    assert sum(snapshot['severity_distribution'].values()) == len(source['findings'])
    assert snapshot['counts']['canonical_findings'] == len(source['findings'])
    source['findings'].clear()
    assert snapshot['findings']


def test_frozen_snapshot_renders_in_limited_child_process():
    pdf = render_isolated(fixture('ReportSnapshot'))
    assert pdf.startswith(b'%PDF-')


def test_invalid_snapshot_is_rejected_before_process_start():
    with pytest.raises(ValueError):
        render_isolated({})
