"""Deterministic interpretation of bounded projections, with no execution authority.

These are facts about recorded observations, not assertions that imported detections
are true or currently applicable. Raw evidence, asset identity and product versions
are absent from this projection; correlation and CVE matching are not possible here.
"""
import hashlib

from reknyx.contracts import canonical_request

VERSION = 'evidence-interpretation-v1'
_KINDS = ('service', 'vulnerability', 'informational', 'unknown')
_SEVERITIES = ('critical', 'high', 'medium', 'low', 'informational', 'unknown')


def interpret_evidence(context: dict, basis_observation_ids: list[str] | None = None) -> dict:
    """Interpret all or a cited subset of an already assessment-authorized context.

    The context builder/caller enforces assessment ownership. This pure function
    enforces membership in that projection; it cannot authorize database access.
    No imported text is copied except bounded stable observation identifiers.
    """
    if not isinstance(context, dict) or not isinstance(context.get('observations'), list):
        raise ValueError('invalid_interpretation_context')
    observations = context['observations']
    if len(observations) > 32:
        raise ValueError('unbounded_interpretation_context')
    allowed = set()
    for item in observations:
        identifier = item.get('id') if isinstance(item, dict) else None
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 128 or identifier in allowed:
            raise ValueError('invalid_observation_identity')
        allowed.add(identifier)
    if basis_observation_ids is None:
        selected = allowed
    else:
        if (not isinstance(basis_observation_ids, list)
                or any(not isinstance(item, str) for item in basis_observation_ids)
                or len(set(basis_observation_ids)) != len(basis_observation_ids)
                or not set(basis_observation_ids) <= allowed):
            raise ValueError('invalid_interpretation_reference')
        selected = set(basis_observation_ids)

    facts, hypotheses = [], []
    counts = dict.fromkeys(_KINDS, 0)
    for item in observations:
        if item['id'] not in selected:
            continue
        kind = item.get('kind')
        kind = kind if isinstance(kind, str) and kind in _KINDS else 'unknown'
        source = item.get('source_tool')
        source = source if isinstance(source, str) and source in ('nmap', 'zap', 'greenbone') else 'unknown'
        native = item.get('facts')
        native = native if isinstance(native, dict) else {}
        port = native.get('port')
        port = port if type(port) is int and 1 <= port <= 65535 else None
        transport = native.get('transport')
        transport = transport if isinstance(transport, str) and transport in ('tcp', 'udp') else 'unknown'
        severity = native.get('severity')
        severity = severity if isinstance(severity, str) and severity in _SEVERITIES else 'unknown'
        historical = native.get('historical')
        historical = historical if type(historical) is bool else None
        counts[kind] += 1
        facts.append({'observation_id': item['id'], 'kind': kind, 'source_tool': source,
                      'observed': {'transport': transport, 'port': port, 'source_severity': severity},
                      'historical': historical,
                      'interpretation': {'service': 'recorded_service', 'vulnerability': 'recorded_detection',
                                         'informational': 'recorded_information', 'unknown': 'unknown_observation'}[kind]})
        if kind == 'vulnerability':
            hypotheses.append({'kind': 'unconfirmed_detection', 'basis_observation_ids': [item['id']]})

    unknowns = []
    if not facts:
        unknowns.append('Import relevant source evidence before drawing conclusions.')
    else:
        unknowns.append('Imported observations do not establish technical confirmation or current live applicability.')
        if counts['vulnerability']:
            unknowns.append('Product/version applicability and detection prerequisites have not been established.')
        if any(f['historical'] is None for f in facts):
            unknowns.append('Source time relevance is unknown for some cited observations.')
        if any(f['observed']['port'] is None or f['observed']['transport'] == 'unknown' for f in facts):
            unknowns.append('Service location is incomplete for some cited observations.')
        if any(f['kind'] == 'vulnerability' and f['observed']['source_severity'] == 'unknown' for f in facts):
            unknowns.append('Source severity is unknown for some cited detections.')
    limitations = ['Deterministic interpretation of recorded metadata, not vulnerability confirmation.',
                   'Asset identity, raw locators and version applicability are not present; no correlation or CVE match is inferred.']
    truncated = context.get('truncated') is True
    if truncated:
        limitations.append('Context is limited to the latest 32 observations; it does not establish complete coverage.')
    projection = {'version': VERSION, 'facts': facts, 'hypotheses': hypotheses, 'counts': counts,
                  'unknowns': unknowns, 'limitations': limitations, 'truncated': truncated}
    return {**projection, 'sha256': hashlib.sha256(canonical_request(projection)).hexdigest()}


def render_interpretation(value: dict) -> str:
    """Fixed templates avoid reflecting imported strings into analyst prose."""
    counts = value['counts']
    if not value['facts']:
        return 'No cited observations are available for interpretation.'
    summary = (f"Cited metadata contains {counts['service']} recorded service observation(s), "
               f"{counts['vulnerability']} unconfirmed detection(s), "
               f"{counts['informational']} informational observation(s), and "
               f"{counts['unknown']} observation(s) of unknown kind. ")
    if counts['service']:
        summary += 'An open service does not establish a vulnerability. '
    historical = sum(item['historical'] is True for item in value['facts'])
    if historical:
        summary += f'{historical} cited observation(s) are labelled historical. '
    return summary + 'Imported evidence does not establish current applicability or technical confirmation.'
