"""Explicit deterministic review and fact-safe rendering; no model calls implied."""
from .output_validation import TOPICS, validate_output
from .review_policy import requirements
from .evidence_interpretation import interpret_evidence, render_interpretation

def local_review(context):
    observations=context['observations']
    topics,_=requirements(observations)
    return validate_output({'outcome':'ask','basis_observation_ids':[o['id'] for o in observations], 'topics':topics},context)

def render_review(value, context):
    count=len(value['basis_observation_ids'])
    interpretation = interpret_evidence(context, value['basis_observation_ids'])
    return (f'Evidence review cites {count} recorded observation(s). ' + render_interpretation(interpretation)
            + ' ' + ' '.join(TOPICS[t] for t in value['topics']))


def review_unknowns(value, context):
    """Use the same cited projection for persisted unknowns and analyst prose."""
    return interpret_evidence(context, value['basis_observation_ids'])['unknowns']
