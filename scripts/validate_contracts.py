#!/usr/bin/env python3
"""Validate the local P1-01 contract candidate without contacting any service."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import OpenAPIV31SpecValidator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
import yaml

from contract_semantics import review_priority, semantic_errors
from contract_hashes import authority_hash, canonical_bytes, normalize

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
ROOT = Path(__file__).resolve().parents[1]
CONTRACT_URI = "urn:reknyx:contract:0.1.0"


class ContractError(ValueError):
    """Invalid contract, examples or acceptance coverage."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently replacing authority."""


def _mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ContractError(f"Duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_contract(root=ROOT):
    return yaml.load((root / "contracts/openapi.yaml").read_text(), Loader=UniqueKeyLoader)


def _nodes(value, path="$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _nodes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _nodes(child, f"{path}[{index}]")


def _resolve(spec, reference):
    if not reference.startswith("#/"):
        raise ContractError(f"External reference forbidden in offline contract: {reference}")
    value = spec
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def operations(spec):
    return {operation["operationId"]: (path, method, operation)
            for path, item in spec["paths"].items()
            for method, operation in item.items() if method in HTTP_METHODS}


def audit_spec(spec):
    """Extra project rules beyond OpenAPI structural validity."""
    errors = []
    identifiers = []
    for path, node in _nodes(spec):
        if "$ref" in node:
            try:
                _resolve(spec, node["$ref"])
            except (KeyError, TypeError, ContractError) as error:
                errors.append(f"{path}: reference: {error}")
    for path, node in _nodes(spec["components"]["schemas"]):
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            errors.append(f"{path}: additionalProperties must be false")
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method not in HTTP_METHODS:
                continue
            name = operation.get("operationId")
            identifiers.append(name)
            public = path in {"/health/live", "/health/ready", "/auth/login"}
            if operation.get("security") != ([] if public else [{"cookieSession": []}]):
                errors.append(f"{name}: security must match public/session boundary")
            parameters = [_resolve(spec, value["$ref"]) if "$ref" in value else value
                          for value in operation.get("parameters", [])]
            headers = {value["name"] for value in parameters
                       if value["in"] == "header" and value.get("required")}
            if method != "get":
                if "Origin" not in headers or (not public and "X-CSRF-Token" not in headers):
                    errors.append(f"{name}: security requires Origin and authenticated CSRF")
                if not public and path != "/auth/logout" and ("Idempotency-Key" not in headers or "x-idempotency" not in operation):
                    errors.append(f"{name}: mutation requires reviewed idempotency rules")
            if not public and not {"401", "403", "404", "409", "422", "501", "503"} <= operation["responses"].keys():
                errors.append(f"{name}: incomplete typed error surface")
            if operation.get("x-runtime-status") != "not_implemented":
                errors.append(f"{name}: contract candidate cannot assert runtime implementation")
    if len(identifiers) != len(set(identifiers)):
        errors.append("Duplicate operationId")
    return errors


def validate_payload(spec, schema, payload):
    resource = Resource.from_contents(spec, default_specification=DRAFT202012)
    registry = Registry().with_resource(CONTRACT_URI, resource)
    validator = Draft202012Validator(
        {"$ref": f"{CONTRACT_URI}#/components/schemas/{schema}"},
        registry=registry, format_checker=FormatChecker(),
    )
    return [f"{error.json_path}: {error.validator}: {error.message}"
            for error in validator.iter_errors(payload)]


def _read(root, relative):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ContractError(f"Duplicate JSON member: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ContractError(f"Nonfinite JSON number: {value}")

    return json.loads((root / "contracts" / relative).read_text(),
                      object_pairs_hook=pairs, parse_constant=invalid_constant)


def load_semantic_cases(root=ROOT):
    document = _read(root, "examples/semantic-cases.json")
    contexts = document["contexts"]
    resolved = {}

    def context(name, seen=()):
        if name in seen:
            raise ContractError(f"Cyclic semantic context: {name}")
        if name not in resolved:
            value = contexts[name]
            if "extends" in value:
                value = {**context(value["extends"], (*seen, name)), **value["overrides"]}
            resolved[name] = value
        return resolved[name]

    return [{**case, "context": context(case["context"])} for case in document["cases"]]


def check_hash_vectors(root, spec):
    vectors = _read(root, "examples/hash-vectors.json")
    golden = {case["id"]: case for case in vectors["golden"]}
    for case in vectors["golden"] + vectors["equivalent"]:
        base = case if "kind" in case else golden[case["base"]]
        encoded = canonical_bytes(base["kind"], case["payload"])
        if encoded.decode() != base["canonical_utf8"] or authority_hash(base["kind"], case["payload"]) != base["sha256"]:
            raise ContractError(f"{case['id']}: canonical bytes/hash mismatch")
        schema = "ScopeAuthority" if base["kind"] == "scope" else "ActionAuthority"
        if validate_payload(spec, schema, normalize(base["kind"], case["payload"])):
            raise ContractError(f"{case['id']}: normalized authority violates wire schema")
    for group in ("mutations", "invalid"):
        for case in vectors[group]:
            base = golden[case["base"]]
            value = deepcopy(base["payload"])
            cursor = value
            parts = case["path"].split(".")
            for part in parts[:-1]:
                cursor = cursor[part]
            if case.get("remove"):
                del cursor[parts[-1]]
            else:
                cursor[parts[-1]] = case["value"]
            try:
                digest = authority_hash(base["kind"], value)
            except ValueError:
                if group == "mutations":
                    raise ContractError(f"{case['id']}: valid hash mutation rejected")
            else:
                if group == "invalid" or digest == base["sha256"]:
                    raise ContractError(f"{case['id']}: malformed/unchanged hash mutation accepted")
    result = subprocess.run(
        ["node", str(ROOT / "scripts/check_contract_hashes.mjs"),
         str(root / "contracts/examples/hash-vectors.json")],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode:
        raise ContractError(f"Independent JavaScript hash check failed: {result.stderr}")
    return {name: len(vectors[name]) for name in
            ("golden", "equivalent", "mutations", "invalid", "invalid_json")}


def validate_contracts(root=ROOT):
    spec = load_contract(root)
    errors = audit_spec(spec)
    if errors:
        raise ContractError("\n".join(errors))
    # Only local references are permitted before invoking the OpenAPI validator.
    spec_errors = list(OpenAPIV31SpecValidator(spec).iter_errors())
    if spec_errors:
        raise ContractError("\n".join(str(error) for error in spec_errors))
    for schema in spec["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)
    cases = _read(root, "examples/schema-cases.json")["cases"]
    ids = set()
    covered_schemas = set()
    for case in cases:
        if case["id"] in ids:
            raise ContractError(f"Duplicate schema case: {case['id']}")
        ids.add(case["id"])
        result = validate_payload(spec, case["schema"], case["payload"])
        if bool(result) != (not case["valid"]):
            raise ContractError(f"{case['id']}: unexpected schema result: {result}")
        if case["valid"]:
            covered_schemas.add(case["schema"])
        elif not any(case["error_keyword"] in error for error in result):
            raise ContractError(f"{case['id']}: failed for wrong reason: {result}")
    missing = spec["components"]["schemas"].keys() - covered_schemas
    if missing:
        raise ContractError(f"Schemas without valid examples: {sorted(missing)}")
    semantics = load_semantic_cases(root)
    for case in semantics:
        result = validate_payload(spec, case["schema"], case["payload"])
        if result:
            raise ContractError(f"{case['id']}: semantic case is structurally invalid: {result}")
        result = semantic_errors(case["kind"], case["payload"], case["context"])
        if sorted(result) != sorted(case["expected_errors"]):
            raise ContractError(f"{case['id']}: {result} != {case['expected_errors']}")
    ops = operations(spec)
    mapping = _read(root, "route-map.json")
    mapped = mapping["operations"]
    if len(mapped) != len(ops) or {row["operation_id"] for row in mapped} != ops.keys():
        raise ContractError("Route mapping does not cover every operation exactly once")
    for row in mapped:
        path, method, _ = ops[row["operation_id"]]
        if row["path"] != path or row["method"].lower() != method or not row["browser_views"]:
            raise ContractError(f"Invalid route-to-view mapping: {row['operation_id']}")
    http_cases = _read(root, "examples/http-cases.json")["cases"]
    if {case["operation_id"] for case in http_cases} != ops.keys():
        raise ContractError("HTTP examples do not cover every operation")
    for case in http_cases:
        _, _, operation = ops[case["operation_id"]]
        response = operation["responses"][str(case["status"])]
        if "$ref" in response:
            response = _resolve(spec, response["$ref"])
        if "request" in case:
            request = case["request"]
            schema = operation["requestBody"]["content"][request["media_type"]]["schema"]["$ref"].split("/")[-1]
            result = validate_payload(spec, schema, request["payload"])
            if result:
                raise ContractError(f"{case['id']}: request invalid: {result}")
        if case["media_type"] is None:
            if "content" in response or case["payload"] is not None:
                raise ContractError(f"{case['id']}: invalid bodyless response")
        elif case.get("binary"):
            if response["content"][case["media_type"]]["schema"].get("format") != "binary":
                raise ContractError(f"{case['id']}: not a binary download")
        else:
            schema = response["content"][case["media_type"]]["schema"]["$ref"].split("/")[-1]
            result = validate_payload(spec, schema, case["payload"])
            if result:
                raise ContractError(f"{case['id']}: response invalid: {result}")
    priorities = _read(root, "examples/priority-cases.json")["cases"]
    for case in priorities:
        result = validate_payload(spec, "Finding", case["finding"])
        if result or review_priority(case["finding"]) != case["expected_priority"]:
            raise ContractError(f"{case['id']}: priority example invalid: {result}")
    review = _read(root, "review-status.json")
    if review["contract_version"] != spec["info"]["version"]:
        raise ContractError("Review record contract version mismatch")
    digest = hashlib.sha256((root / "contracts/openapi.yaml").read_bytes()).hexdigest()
    if review["openapi_sha256"] != digest:
        raise ContractError("Review record does not identify current OpenAPI bytes")
    owners_approved = True
    for role in ("frontend_owner", "backend_owner"):
        owner = review[role]
        if owner["status"] == "approved":
            if not owner.get("reviewer") or not owner.get("reviewed_at") or owner.get("openapi_sha256") != digest:
                raise ContractError(f"{role}: approval must identify reviewer, time and current contract hash")
        else:
            owners_approved = False
    hashes = check_hash_vectors(root, spec)
    return {"openapi": spec["openapi"], "contract_version": spec["info"]["version"],
            "paths": len(spec["paths"]), "operations": len(ops),
            "schemas": len(spec["components"]["schemas"]), "schema_cases": len(cases),
            "semantic_cases": len(semantics), "http_cases": len(http_cases),
            "priority_cases": len(priorities),
            "hash_vectors": hashes, "openapi_sha256": digest,
            "g0": "pending_gate_verification" if owners_approved else "pending_owner_review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_contracts(args.root), indent=2))
    except (ContractError, KeyError, ValueError, OSError, yaml.YAMLError, subprocess.TimeoutExpired) as error:
        print(f"Contract validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
