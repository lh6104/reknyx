"""Explicit deterministic review and fact-safe rendering; no model calls implied."""
from .output_validation import TOPICS, validate_output

def local_review(context):
    observations=context['observations']
    topics=['review_source'] if observations else ['supply_evidence','confirm_scope']
    vulnerabilities=[o for o in observations if o.get('kind')=='vulnerability']
    if vulnerabilities:
        topics.append('review_remediation')
        if any(o.get('facts',{}).get('severity','unknown')=='unknown' for o in vulnerabilities):
            topics.append('resolve_uncertainty')
    return validate_output({'outcome':'ask','basis_observation_ids':[o['id'] for o in observations], 'topics':topics},context)

def render_review(value, context):
    count=len(value['basis_observation_ids'])
    return f'Evidence review cites {count} recorded observation(s). ' + ' '.join(TOPICS[t] for t in value['topics'])
