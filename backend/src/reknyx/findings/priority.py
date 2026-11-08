"""Contract ordinal-v1 review ordering; no numeric risk or confidence calibration."""

SEVERITIES = ('critical', 'high', 'medium', 'low', 'informational', 'unknown')


def prioritize(finding):
    severity = finding['severity']
    reasons = []
    if severity in ('critical', 'high'):
        reasons.append('High or critical source severity requires review first; confidence does not reduce severity.')
    if finding['exploitability']['value'] == 'demonstrated':
        reasons.append('Recorded demonstrated exploitability requires review first.')
    if (severity == 'medium' and finding['exposure']['value'] == 'reachable'
            and finding['asset_impact']['value'] == 'high'):
        reasons.append('Medium source severity on a recorded reachable, high-impact asset requires review first.')
    known_context = all(finding[field]['value'] != 'unknown'
                        for field in ('exposure', 'exploitability', 'asset_impact'))
    if reasons:
        priority = 'review_first'
    elif severity in ('low', 'informational') and known_context:
        priority = 'routine'
        reasons.append('Low or informational source severity with all three context inputs recorded enters routine review.')
    else:
        priority = 'review_next'
        reasons.append('Source severity and recorded context do not meet the review-first or routine rule; unknown context stays unknown.')
    return {'priority': priority, 'priority_reasons': reasons, 'risk_rule_version': 'ordinal-v1'}
