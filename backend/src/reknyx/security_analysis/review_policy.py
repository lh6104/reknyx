"""Minimum analyst-review coverage over normalized observations, never a risk score."""

VERSION = 'review-coverage-v1'


def requirements(observations):
    """Return required topics and ID groups that each need at least one citation."""
    if not observations:
        return ['supply_evidence', 'confirm_scope'], []
    topics = ['review_source']
    witnesses = []
    vulnerabilities = [o for o in observations if o.get('kind') == 'vulnerability']
    if vulnerabilities:
        topics.append('review_remediation')
        witnesses.append({o['id'] for o in vulnerabilities})
        unknown = [o for o in vulnerabilities
                   if o.get('facts', {}).get('severity', 'unknown') == 'unknown']
        if unknown:
            topics.append('resolve_uncertainty')
            witnesses.append({o['id'] for o in unknown})
    return topics, witnesses
