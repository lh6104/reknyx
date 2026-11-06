"""Runtime validation against the single repository OpenAPI schema authority.

Deployments must ship contracts/openapi.yaml and scripts/contract_hashes.py with
the package. REKNYX_REPOSITORY_ROOT may identify that source bundle explicitly.
"""
import importlib.util
import json
import math
import os
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
import yaml


def _root():
    configured = os.getenv("REKNYX_REPOSITORY_ROOT")
    candidates = [Path(configured)] if configured else list(Path(__file__).resolve().parents)
    for path in candidates:
        if (path / "contracts/openapi.yaml").is_file():
            return path
    raise RuntimeError("Executable contract source bundle is missing")


ROOT = _root()
CONTRACT = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text())
SCHEMAS = CONTRACT["components"]["schemas"]
_spec = importlib.util.spec_from_file_location("reknyx_contract_hash_authority", ROOT / "scripts/contract_hashes.py")
HASH_AUTHORITY = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HASH_AUTHORITY)


def validate(schema_name, value):
    schema = {"$ref": f"#/components/schemas/{schema_name}", "components": CONTRACT["components"]}
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    if errors:
        raise ValueError("Input does not match the executable contract")
    return value


def validate_schema(schema, value):
    document = {**schema, "components": CONTRACT["components"]}
    if not Draft202012Validator(document, format_checker=FormatChecker()).is_valid(value):
        raise ValueError("Input does not match the executable contract")
    return value


def parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON member")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("Nonfinite JSON number")
    def finite_float(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError("Nonfinite JSON number")
        return value
    def scalars(value):
        if isinstance(value, str):
            # Escaped lone UTF-16 surrogates are not UTF-8 scalar values.
            value.encode("utf-8")
        elif isinstance(value, dict):
            for key, member in value.items():
                scalars(key)
                scalars(member)
        elif isinstance(value, list):
            for member in value:
                scalars(member)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)
        scalars(value)
        return value
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid UTF-8 JSON") from exc


def canonical_request(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
