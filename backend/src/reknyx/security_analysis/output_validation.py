"""A model selects evidence review topics, never source facts or authority."""
from jsonschema import Draft202012Validator
from reknyx.contracts import parse_json

VERSION = 'evidence-review-v2'
TOPICS = {
 'review_source': 'Inspect the original source bytes and compare the cited observations.',
 'review_remediation': 'Review remediation with an analyst; imported detections remain unconfirmed.',
 'supply_evidence': 'Import relevant source evidence before drawing conclusions.',
 'resolve_uncertainty': 'Review missing or uncertain source severity before assigning priority.',
 'confirm_scope': 'Review recorded scope and evidence applicability; imports do not authorize traffic.',
}
SCHEMA = {'type':'object','additionalProperties':False,
 'required':['outcome','basis_observation_ids','topics'],
 'properties':{'outcome':{'type':'string','enum':['ask','inconclusive']},
 'basis_observation_ids':{'type':'array','items':{'type':'string'},'maxItems':32,'uniqueItems':True},
 'topics':{'type':'array','items':{'type':'string','enum':list(TOPICS)},'minItems':1,'maxItems':4,'uniqueItems':True}}}

def validate_output(raw, context):
    value = parse_json(raw) if isinstance(raw, bytes) else raw
    if not Draft202012Validator(SCHEMA).is_valid(value):
        raise ValueError('invalid_model_output')
    allowed = {o['id'] for o in context['observations']}
    if not set(value['basis_observation_ids']) <= allowed:
        raise ValueError('invalid_evidence_reference')
    if allowed and not value['basis_observation_ids']:
        raise ValueError('missing_evidence_reference')
    cited=[o for o in context['observations'] if o['id'] in value['basis_observation_ids']]
    if 'review_remediation' in value['topics'] and not any(o.get('kind')=='vulnerability' for o in cited):
        raise ValueError('unsupported_remediation_review')
    return value
