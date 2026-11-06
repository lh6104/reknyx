"""Acceptance tests for the offline contract boundary, not a running API."""

from copy import deepcopy
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def validator():
    assert (ROOT / "scripts/validate_contracts.py").is_file(), "Contract validator is missing"
    return importlib.import_module("validate_contracts")


def test_contract_suite_runs_offline_and_reports_review_pending():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_contracts.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["openapi"] == "3.1.2"
    assert report["operations"] >= 40
    assert report["g0"] == "pending_owner_review"
    assert report["schema_cases"] >= 50
    assert report["semantic_cases"] >= 20


@pytest.mark.parametrize("schema,payload", [
    ("MessageCreate", {"content": "hello", "expected_revision": 1, "actor_id": "injected"}),
    ("MessageCreate", {"content": "", "expected_revision": 1}),
    ("MessageCreate", {"content": "x" * 4001, "expected_revision": 1}),
    ("ReportCreate", {"expected_revision": 0, "include_suspected": True}),
    ("NmapParameters", {"ports": [80, 80], "deadline_seconds": 120}),
    ("NmapParameters", {"ports": [80], "deadline_seconds": 121}),
    ("ZapParameters", {"scheme": "https", "port": 443, "root_path": "/private", "deadline_seconds": 180}),
    ("AsyncAccepted", {"job_id": "bad", "resource_id": "bad", "status_url": "https://attacker.test"}),
])
def test_boundary_rejects_unsafe_or_unbounded_payloads(schema, payload):
    module = validator()
    spec = module.load_contract(ROOT)
    assert module.validate_payload(spec, schema, payload)


def test_every_operation_has_a_route_mapping_and_validated_response_examples():
    module = validator()
    spec = module.load_contract(ROOT)
    assert module.audit_spec(spec) == []
    mappings = json.loads((ROOT / "contracts/route-map.json").read_text())
    operations = {op["operationId"] for path in spec["paths"].values()
                  for method, op in path.items() if method in module.HTTP_METHODS}
    assert {row["operation_id"] for row in mappings["operations"]} == operations
    covered = {case["operation_id"] for case in json.loads(
        (ROOT / "contracts/examples/http-cases.json").read_text())["cases"]}
    assert covered == operations


def test_spec_audit_detects_authority_and_security_regressions():
    module = validator()
    spec = module.load_contract(ROOT)
    changed = deepcopy(spec)
    operation = changed["paths"]["/assessments/{assessment_id}/messages"]["post"]
    operation["security"] = []
    assert any("security" in issue for issue in module.audit_spec(changed))
    changed = deepcopy(spec)
    changed["components"]["schemas"]["MessageCreate"]["additionalProperties"] = True
    assert any("additionalProperties" in issue for issue in module.audit_spec(changed))


def test_format_enforcement_rejects_bad_uuid_ipv4_and_timestamp():
    module = validator()
    spec = module.load_contract(ROOT)
    for schema, value in [("Id", "not-a-uuid"), ("IPv4", "999.1.1.1"),
                          ("Timestamp", "2026-02-30T00:00:00Z")]:
        assert module.validate_payload(spec, schema, value)


def test_validator_checks_negative_cases_for_the_declared_reason():
    module = validator()
    spec = module.load_contract(ROOT)
    cases = json.loads((ROOT / "contracts/examples/schema-cases.json").read_text())["cases"]
    for case in cases:
        errors = module.validate_payload(spec, case["schema"], case["payload"])
        assert bool(errors) is (not case["valid"]), case["id"]
        if not case["valid"]:
            assert any(case["error_keyword"] in issue for issue in errors), case["id"]


def test_semantic_examples_reject_foreign_missing_stale_and_unsupported_actions():
    assert (ROOT / "scripts/contract_semantics.py").is_file(), "Semantic checks are missing"
    module = importlib.import_module("contract_semantics")
    cases = validator().load_semantic_cases(ROOT)
    observed = set()
    for case in cases:
        errors = module.semantic_errors(case["kind"], case["payload"], case["context"])
        assert sorted(errors) == sorted(case["expected_errors"]), case["id"]
        observed.update(errors)
    assert {"foreign_evidence", "missing_evidence", "stale_revision", "unsupported_profile",
            "http_basis_required", "scope_expired", "idempotency_conflict"} <= observed


def test_reviewed_plan_rechecks_authority_hash_policy_and_current_state():
    module = importlib.import_module("contract_semantics")
    case = next(c for c in validator().load_semantic_cases(ROOT) if c["id"] == "plan-result-valid")
    result, context = deepcopy(case["payload"]), deepcopy(case["context"])
    result["proposal"]["action_hash"] = "0" * 64
    result["decision"]["policy_result"] = "deny"
    context["state_revision"] += 1
    assert {"action_hash_mismatch", "policy_result_mismatch", "stale_revision"} <= set(module.semantic_errors("plan_result", result, context))


def test_correlation_uses_service_identity_not_observation_membership():
    module = importlib.import_module("contract_semantics")
    case = next(c for c in validator().load_semantic_cases(ROOT) if c["id"] == "correlation-valid")
    context, payload = deepcopy(case["context"]), deepcopy(case["payload"])
    observation = deepcopy(context["observations"][0])
    observation["id"] = "00000000-0000-4000-8000-000000000031"
    observation["service"]["observation_ids"] = [observation["id"]]
    context["observations"].append(observation)
    context["compatible_observation_ids"].append(observation["id"])
    payload["observation_ids"] = [observation["id"]]
    assert module.semantic_errors("correlation", payload, context) == []


def test_priority_examples_preserve_urgency_and_unknowns_without_numeric_scores():
    cases_path = ROOT / "contracts/examples/priority-cases.json"
    assert cases_path.is_file(), "Twelve priority comparison expectations are missing"
    cases = json.loads(cases_path.read_text())["cases"]
    module = importlib.import_module("contract_semantics")
    assert len(cases) == 12
    for case in cases:
        assert module.review_priority(case["finding"]) == case["expected_priority"], case["id"]
    high_low_confidence = next(case for case in cases if case["id"] == "high-low-confidence")
    assert high_low_confidence["expected_priority"] == "review_first"


def test_validator_detects_missing_route_and_tampered_response(tmp_path):
    import shutil
    module = validator()
    shutil.copytree(ROOT / "contracts", tmp_path / "contracts",
                    ignore=shutil.ignore_patterns("node_modules", "__pycache__"))
    path = tmp_path / "contracts/examples/http-cases.json"
    document = json.loads(path.read_text())
    document["cases"] = [case for case in document["cases"] if case["operation_id"] != "getSession"]
    path.write_text(json.dumps(document))
    with pytest.raises(module.ContractError, match="cover every operation"):
        module.validate_contracts(tmp_path)
    document = json.loads((ROOT / "contracts/examples/http-cases.json").read_text())
    case = next(case for case in document["cases"] if case["operation_id"] == "appendMessage")
    case["request"]["payload"]["actor_id"] = "injected"
    path.write_text(json.dumps(document))
    with pytest.raises(module.ContractError, match="request invalid"):
        module.validate_contracts(tmp_path)


def test_offline_audit_rejects_remote_refs_and_duplicate_yaml_keys(tmp_path):
    module = validator()
    spec = module.load_contract(ROOT)
    spec["components"]["schemas"]["MessageCreate"] = {"$ref": "https://outside.example/schema"}
    assert any("External reference forbidden" in error for error in module.audit_spec(spec))
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts/openapi.yaml").write_text("openapi: 3.1.2\nopenapi: 3.0.0\n")
    with pytest.raises(module.ContractError, match="Duplicate YAML key"):
        module.load_contract(tmp_path)
