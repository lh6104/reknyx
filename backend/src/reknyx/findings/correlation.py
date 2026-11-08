"""Conservative same-rule evidence compatibility, independent of analyst intent."""
from datetime import datetime


def asset_identity(observation):
    value = observation.get('asset') or {}
    return value.get('address_family'), value.get('canonical_identity')


def service_identity(observation):
    value = observation.get('service') or {}
    return value.get('transport'), value.get('port'), value.get('scheme')


def compatibility_reason(left, right):
    """Return an application-owned deny code, or None for a supported match.

    Each side contains immutable observation/native/manifest data from the server.
    No rule equivalence between different tools has been reviewed for this release.
    """
    a, b = left['observation'], right['observation']
    x, y = left['artifact'], right['artifact']
    if (a['assessment_id'] != b['assessment_id']
            or x['assessment_id'] != a['assessment_id'] or y['assessment_id'] != a['assessment_id']):
        return 'foreign_evidence'
    if a['kind'] != 'vulnerability' or b['kind'] != 'vulnerability':
        return 'vulnerability_basis_required'
    if a['source_tool'] != b['source_tool']:
        return 'unmapped_cross_tool_rule'
    rule = left['native'].get('rule_id')
    if not rule or rule != right['native'].get('rule_id'):
        return 'incompatible_rule'
    identity = asset_identity(a)
    if identity[0] not in ('ipv4', 'ipv6', 'hostname') or not identity[1] or identity != asset_identity(b):
        return 'incompatible_asset'
    service = service_identity(a)
    if service[0] not in ('tcp', 'udp') or service[1] is None or service != service_identity(b):
        return 'incompatible_service'
    if a.get('location') != b.get('location') or (a.get('location') or {}).get('redacted'):
        return 'incompatible_location'
    if (x.get('provenance'), x.get('historical')) != (y.get('provenance'), y.get('historical')):
        return 'incompatible_provenance'
    times = (a.get('observed_at'), b.get('observed_at'))
    if all(times):
        try:
            parsed = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in times]
            if any(t.tzinfo is None for t in parsed) or parsed[0] != parsed[1]:
                return 'incompatible_capture_time'
        except (ValueError, TypeError):
            return 'incompatible_capture_time'
    elif (any(times) or not x.get('sha256') or x.get('sha256') != y.get('sha256')):
        # An unknown capture time cannot be replaced by ingestion time or a tolerance guess.
        return 'unknown_capture_time'
    return None
