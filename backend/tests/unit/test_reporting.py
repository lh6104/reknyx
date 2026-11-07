"""Synthetic frozen-snapshot renderer checks; no scanner or provider traffic."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from reknyx.reporting.renderer import render_pdf, RenderError


def snapshot():
    cases = json.loads((Path(__file__).resolve().parents[3] / 'contracts/examples/schema-cases.json').read_text())
    if isinstance(cases, dict):
        cases = cases['cases']
    return copy.deepcopy(next(case['payload'] for case in cases if case['id'] == 'valid-ReportSnapshot'))


def text_of(pdf, tmp_path):
    source = tmp_path / 'report.pdf'
    source.write_bytes(pdf)
    return subprocess.check_output(['pdftotext', str(source), '-'], text=True)


def test_frozen_snapshot_renders_six_sections_and_traceability(tmp_path):
    value = snapshot()
    before = copy.deepcopy(value)
    pdf = render_pdf(value)
    assert pdf.startswith(b'%PDF-')
    assert pdf == render_pdf(value)
    assert value == before
    text = text_of(pdf, tmp_path)
    for title in ['Executive scope', 'Methodology and rules of engagement', 'Severity and priorities', 'Findings and source evidence', 'Impact and remediation', 'Limitations and audit']:
        assert title in text
    assert value['provenance_notice'] in text
    assert value['findings'][0]['title'] in text
    assert value['artifacts'][0]['sha256'] in text.replace('\n', '').replace(' ', '')


def test_html_is_literal_text_and_external_resources_are_not_loaded(tmp_path):
    value = snapshot()
    value['executive_summary'] = '<img src="https://outside.invalid/a"> & <script>unsafe()</script>'
    text = text_of(render_pdf(value), tmp_path)
    assert '<img src="https://outside.invalid/a">' in text
    assert '<script>unsafe()</script>' in text


def test_invalid_snapshot_and_unsupported_glyphs_fail():
    with pytest.raises(ValueError):
        render_pdf({})
    value = snapshot()
    value['executive_summary'] = '\U0001f9ea'
    with pytest.raises(RenderError, match='glyph'):
        render_pdf(value)


def test_foreign_assessment_evidence_cannot_be_rendered():
    value = snapshot()
    value['observations'][0]['assessment_id'] = '00000000-0000-4000-8000-000000000099'
    with pytest.raises(RenderError, match='assessment'):
        render_pdf(value)


def test_missing_source_artifact_cannot_be_rendered():
    value = snapshot()
    value['artifacts'] = []
    with pytest.raises(RenderError, match='artifact'):
        render_pdf(value)


def test_missing_finding_observation_cannot_be_rendered():
    value = snapshot()
    value['observations'] = []
    with pytest.raises(RenderError, match='observation'):
        render_pdf(value)
