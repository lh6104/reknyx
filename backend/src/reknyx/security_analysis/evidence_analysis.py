"""Explicit deterministic review and fact-safe rendering; no model calls implied."""
from .output_validation import TOPICS, validate_output
from .review_policy import requirements

def local_review(context):
    observations=context['observations']
    topics,_=requirements(observations)
    return validate_output({'outcome':'ask','basis_observation_ids':[o['id'] for o in observations], 'topics':topics},context)

def render_review(value, context):
    count=len(value['basis_observation_ids'])
    return f'Evidence review cites {count} recorded observation(s). ' + ' '.join(TOPICS[t] for t in value['topics'])
