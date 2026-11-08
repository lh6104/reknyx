"""Independent topic coverage checks; no provider or scanner requests."""
import pytest

from reknyx.security_analysis.output_validation import validate_output


def observation(identifier, kind, severity='unknown'):
    return {'id': identifier, 'kind': kind, 'source_tool': 'fixture',
            'facts': {'severity': severity}}


@pytest.mark.parametrize('records,topics,refs,reason', [
    ([], ['confirm_scope'], [], 'missing_required_review_topic'),
    ([], ['supply_evidence', 'confirm_scope', 'review_source'], [], 'unsupported_review_topic'),
    ([observation('service', 'service')], ['supply_evidence', 'confirm_scope'],
     ['service'], 'missing_required_review_topic'),
    ([observation('vuln', 'vulnerability', 'medium')], ['review_source'],
     ['vuln'], 'missing_required_review_topic'),
    ([observation('vuln', 'vulnerability')], ['review_source', 'review_remediation'],
     ['vuln'], 'missing_required_review_topic'),
    ([observation('service', 'service'), observation('vuln', 'vulnerability', 'high')],
     ['review_source', 'review_remediation'], ['service'], 'unsupported_remediation_review'),
    ([observation('known', 'vulnerability', 'high'), observation('unknown', 'vulnerability')],
     ['review_source', 'review_remediation', 'resolve_uncertainty'],
     ['known'], 'missing_required_review_reference'),
])
def test_review_cannot_omit_required_topics_or_their_support(records, topics, refs, reason):
    with pytest.raises(ValueError, match=reason):
        validate_output({'outcome': 'ask', 'topics': topics, 'basis_observation_ids': refs},
                        {'observations': records})


def test_review_can_select_a_supported_subset_without_hiding_unknown_severity():
    records = [observation('service', 'service'), observation('known', 'vulnerability', 'high'),
               observation('unknown', 'vulnerability')]
    value = {'outcome': 'inconclusive',
             'topics': ['review_source', 'review_remediation', 'resolve_uncertainty'],
             'basis_observation_ids': ['unknown']}
    assert validate_output(value, {'observations': records}) == value
