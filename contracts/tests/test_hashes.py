"""Offline authority encoding acceptance; golden bytes are independent fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def hashes():
    path = ROOT / "scripts/contract_hashes.py"
    assert path.is_file(), "Python authority encoder is not implemented"
    spec = importlib.util.spec_from_file_location("contract_hashes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vectors():
    return json.loads((ROOT / "contracts/examples/hash-vectors.json").read_text())


def replace(payload, path, value, remove=False):
    result = copy.deepcopy(payload)
    cursor = result
    parts = path.split(".")
    for part in parts[:-1]:
        cursor = cursor[part]
    if remove:
        del cursor[parts[-1]]
    else:
        cursor[parts[-1]] = value
    return result


def test_canonical_encoders_exist():
    assert (ROOT / "scripts/contract_hashes.py").is_file(), "Python encoder missing"
    assert (ROOT / "scripts/check_contract_hashes.mjs").is_file(), "JavaScript encoder missing"


def test_golden_bytes_and_digests(hashes):
    for case in vectors()["golden"]:
        before = copy.deepcopy(case["payload"])
        assert hashes.canonical_bytes(case["kind"], before) == case["canonical_utf8"].encode()
        assert hashes.authority_hash(case["kind"], before) == case["sha256"]
        assert before == case["payload"], "normalization must not mutate its caller"


def test_normalization_equivalences(hashes):
    cases = {case["id"]: case for case in vectors()["golden"]}
    for case in vectors()["equivalent"]:
        base = cases[case["base"]]
        assert hashes.canonical_bytes(base["kind"], case["payload"]) == base["canonical_utf8"].encode()


def test_golden_and_normalized_equivalences_match_canonical_wire_schemas(hashes):
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker

    spec = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text())
    cases = {case["id"]: case for case in vectors()["golden"]}
    for case in vectors()["golden"] + vectors()["equivalent"]:
        kind = case.get("kind") or cases[case["base"]]["kind"]
        schema_name = "ScopeAuthority" if kind == "scope" else "ActionAuthority"
        schema = {"$ref": f"#/components/schemas/{schema_name}", "components": spec["components"]}
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        validator.validate(hashes.normalize(kind, case["payload"]))


def test_every_authority_mutation_changes_hash(hashes):
    cases = {case["id"]: case for case in vectors()["golden"]}
    for case in vectors()["mutations"]:
        base = cases[case["base"]]
        payload = replace(base["payload"], case["path"], case["value"])
        assert hashes.authority_hash(base["kind"], payload) != base["sha256"], case["id"]


def test_malformed_authority_rejected(hashes):
    cases = {case["id"]: case for case in vectors()["golden"]}
    for case in vectors()["invalid"]:
        base = cases[case["base"]]
        payload = replace(base["payload"], case["path"], case.get("value"), case.get("remove", False))
        with pytest.raises(ValueError, match="."):
            hashes.canonical_bytes(base["kind"], payload)


@pytest.mark.parametrize("bad", [1.0, float("nan"), float("inf"), True, 9007199254740992])
def test_python_rejects_float_bool_and_unsafe_integer(hashes, bad):
    scope = vectors()["golden"][0]["payload"]
    with pytest.raises(ValueError):
        hashes.canonical_bytes("scope", replace(scope, "version", bad))


def test_unknown_kind_rejected(hashes):
    with pytest.raises(ValueError):
        hashes.canonical_bytes("grant", {})


def test_maximum_valid_sets_and_safe_integer_are_preserved(hashes):
    payload = copy.deepcopy(vectors()["golden"][0]["payload"])
    payload["version"] = 9007199254740991
    payload["asset"]["aliases"] = [f"host{i:02}.example" for i in reversed(range(16))]
    payload["allowed_ports"] = list(reversed(range(1, 17)))
    payload["excluded_ports"] = list(reversed(range(17, 33)))
    result = json.loads(hashes.canonical_bytes("scope", payload))
    assert result["version"] == 9007199254740991
    assert result["asset"]["aliases"] == [f"host{i:02}.example" for i in range(16)]
    assert result["allowed_ports"] == list(range(1, 17))
    assert result["excluded_ports"] == list(range(17, 33))


def test_zero_budgets_and_empty_optional_sets_remain_explicit(hashes):
    payload = copy.deepcopy(vectors()["golden"][0]["payload"])
    payload["budget"] = dict.fromkeys(payload["budget"], 0)
    payload["excluded_ports"] = []
    payload["allowed_profiles"] = []
    payload["asset"]["aliases"] = []
    payload["asset"]["hostname"] = None
    assert json.loads(hashes.canonical_bytes("scope", payload)) == payload


def test_python_malformed_numeric_json_rejected(hashes):
    for case in vectors()["invalid_json"]:
        with pytest.raises(ValueError):
            hashes.canonical_bytes(case["kind"], json.loads(case["json"]))


def test_javascript_exported_encoder_rejects_non_json_runtime_values():
    script = (ROOT / "scripts/check_contract_hashes.mjs").as_uri()
    data = (ROOT / "contracts/examples/hash-vectors.json").as_posix()
    program = f"""
        import assert from 'node:assert/strict';
        import {{readFileSync}} from 'node:fs';
        import {{normalize,canonicalBytes,authorityHash}} from {json.dumps(script)};
        const vector=JSON.parse(readFileSync({json.dumps(data)},'utf8')).golden[0];
        const original=structuredClone(vector.payload);
        for (const bad of [NaN,Infinity,-Infinity,-0,true,1.5,9007199254740992]) {{
            assert.throws(()=>normalize('scope',{{...original,version:bad}}));
        }}
        assert.throws(()=>canonicalBytes('grant',{{}}));
        assert.equal(authorityHash('scope',original),vector.sha256);
        assert.deepEqual(original,vector.payload);
    """
    result = subprocess.run(["node", "--input-type=module", "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_independent_javascript_vectors_and_tamper_detection(tmp_path):
    script = ROOT / "scripts/check_contract_hashes.mjs"
    result = subprocess.run(["node", str(script)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    data = vectors()
    data["golden"][0]["sha256"] = "0" * 64
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(data))
    result = subprocess.run(["node", str(script), str(tampered)], capture_output=True, text=True)
    assert result.returncode != 0, "checker accepted a corrupted golden digest"
