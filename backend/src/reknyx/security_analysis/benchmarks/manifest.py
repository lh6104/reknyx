"""Frozen experiment identity and dataset lineage validation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from reknyx.contracts import canonical_request

SCHEMA = json.loads(Path(__file__).with_name('manifest.schema.json').read_text())


def validate_manifest(value: dict) -> dict:
    if not Draft202012Validator(SCHEMA).is_valid(value):
        raise ValueError('invalid_manifest')
    if type(value['repetitions']) is not int or any(type(value['limits'][k]) is not int for k in ('max_calls','max_output_tokens')):
        raise ValueError('integer_limits_required')
    return deepcopy(value)


def manifest_digest(value: dict) -> str:
    return hashlib.sha256(canonical_request(validate_manifest(value))).hexdigest()


def validate_split_families(cases: list[dict]) -> None:
    seen, families = set(), {}
    if not isinstance(cases, list) or not cases:
        raise ValueError('empty_dataset')
    for case in cases:
        identifier, family, split = (case.get(k) for k in ('id','family_id','split'))
        if not all(isinstance(v,str) and v for v in (identifier,family,split)) or identifier in seen:
            raise ValueError('invalid_case_identity')
        if split not in ('development','validation','holdout'):
            raise ValueError('invalid_split')
        if family in families and families[family] != split:
            raise ValueError('family_split_leakage')
        seen.add(identifier)
        families[family] = split


def validate_cases(cases: list[dict]) -> None:
    validate_split_families(cases)
    schema = json.loads(Path(__file__).with_name('case.schema.json').read_text())
    validator = Draft202012Validator(schema)
    for case in cases:
        if not validator.is_valid(case):
            raise ValueError('invalid_case')
        identifiers = [o['id'] for o in case['pack']['observations']]
        expected = case['expected']
        if len(identifiers) != len(set(identifiers)):
            raise ValueError('duplicate_observation')
        if not set(expected['required_evidence']) <= set(identifiers):
            raise ValueError('invalid_gold_reference')
        if not set(expected['required_claims']) <= set(expected['supported_claims']):
            raise ValueError('invalid_gold_claim')
        if set(expected['forbidden_claims']).intersection(expected['supported_claims']):
            raise ValueError('conflicting_gold_claim')
        if any(not set(refs) <= set(identifiers) for refs in expected['supported_claims'].values()):
            raise ValueError('invalid_gold_reference')
