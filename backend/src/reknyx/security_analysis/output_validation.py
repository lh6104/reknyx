"""A model selects evidence review topics, never source facts or authority."""
from jsonschema import Draft202012Validator
from reknyx.contracts import parse_json
from .review_policy import requirements

VERSION = 'evidence-review-v3'
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


class ReviewValidationError(ValueError):
    """Only application-owned reason codes; never provider response text."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_output(raw, context):
    value = parse_json(raw) if isinstance(raw, bytes) else raw
    if not Draft202012Validator(SCHEMA).is_valid(value):
        raise ReviewValidationError('invalid_model_output')
    allowed = {o['id'] for o in context['observations']}
    if not set(value['basis_observation_ids']) <= allowed:
        raise ReviewValidationError('invalid_evidence_reference')
    if allowed and not value['basis_observation_ids']:
        raise ReviewValidationError('missing_evidence_reference')
    if not allowed and set(value['topics']) - {'supply_evidence', 'confirm_scope'}:
        raise ReviewValidationError('unsupported_review_topic')
    cited=[o for o in context['observations'] if o['id'] in value['basis_observation_ids']]
    if 'review_remediation' in value['topics'] and not any(o.get('kind')=='vulnerability' for o in cited):
        raise ReviewValidationError('unsupported_remediation_review')
    required, witnesses = requirements(context['observations'])
    if not set(required) <= set(value['topics']):
        raise ReviewValidationError('missing_required_review_topic')
    if any(not group.intersection(value['basis_observation_ids']) for group in witnesses):
        raise ReviewValidationError('missing_required_review_reference')
    return value
