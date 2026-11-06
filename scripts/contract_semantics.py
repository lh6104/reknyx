"""Pure G0 acceptance rules over synthetic canonical context.

These checks specify contract behavior; they are not runtime authorization,
database transactions, network enforcement or permission to scan.
"""

from datetime import datetime
import hashlib
import json
from contract_hashes import authority_hash


def _time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def request_digest(payload):
    """Digest a validated JSON request; multipart replaces file by raw SHA-256.

    Request strings are exact (including Unicode); no authority normalization
    or intent classification. JSON numbers must already satisfy their schema.
    """
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def review_priority(finding):
    """Contract rule ordinal-v1, not a numeric risk score or confidence model."""
    severity = finding["severity"]
    if (severity in {"critical", "high"}
            or finding["exploitability"]["value"] == "demonstrated"
            or (severity == "medium" and finding["exposure"]["value"] == "reachable"
                and finding["asset_impact"]["value"] == "high")):
        return "review_first"
    known_context = all(finding[key]["value"] != "unknown"
                        for key in ("exposure", "exploitability", "asset_impact"))
    if severity in {"low", "informational"} and known_context:
        return "routine"
    return "review_next"


def semantic_errors(kind, payload, context):
    """Return deterministic diagnostic codes after structural schema validation."""
    errors = set()
    assessment_id = context["assessment_id"]
    observations = {item["id"]: item for item in context.get("observations", [])}
    artifacts = {item["id"]: item for item in context.get("artifacts", [])}
    findings = {item["id"]: item for item in context.get("findings", [])}

    def evidence(ids):
        for identifier in ids:
            item = observations.get(identifier)
            if item is None:
                errors.add("missing_evidence")
            elif item["assessment_id"] != assessment_id:
                errors.add("foreign_evidence")

    def revision(value, expected):
        if value != expected:
            errors.add("stale_revision")

    def scope_rules(scope):
        start, end = _time(scope["valid_from"]), _time(scope["valid_until"])
        if start >= end:
            errors.add("invalid_scope_window")
        if scope["asset"]["authorization_ref_id"] != scope["authorization_ref_id"]:
            errors.add("authorization_reference_mismatch")
        if not set(scope["allowed_ports"]) - set(scope["excluded_ports"]):
            errors.add("empty_effective_scope")
        if "zap_baseline_v1" in scope["allowed_profiles"] and not scope["origin_wide"]:
            errors.add("origin_wide_required")

    if "assessment_id" in payload and payload["assessment_id"] != assessment_id:
        errors.add("foreign_assessment")

    if kind == "scope":
        scope_rules(payload)
    elif kind == "message":
        revision(payload["expected_revision"], context["state_revision"])
    elif kind in ("action", "plan"):
        scope = context["scope"]
        now = _time(context["now"])
        if kind == "plan":
            revision(payload["expected_revision"], context["state_revision"])
            retry = payload["retry"]
            if retry:
                rows = context.get("executions" if retry["kind"] == "execution" else "decisions", [])
                prior = next((item for item in rows if item["id"] == retry["prior_id"]), None)
                if prior is None:
                    errors.add("missing_retry_reference")
                elif prior["assessment_id"] != assessment_id:
                    errors.add("foreign_retry_reference")
                elif prior.get("state") == "execution_unknown":
                    errors.add("execution_unknown")
        else:
            revision(payload["state_revision"], context["state_revision"])
            if payload["scope_version"] != scope["version"] or payload["scope_hash"] != scope["hash"]:
                errors.add("stale_scope")
            if payload["profile"] not in scope["allowed_profiles"]:
                errors.add("unsupported_profile")
            if payload["target"] != scope["asset"]:
                errors.add("out_of_scope_target")
            params = payload["parameters"]
            ports = params.get("ports", [params.get("port")])
            effective = set(scope["allowed_ports"]) - set(scope["excluded_ports"])
            if not set(ports) <= effective:
                errors.add("out_of_scope_port")
            evidence(payload["basis_observation_ids"])
            if _time(payload["expires_at"]) <= now or _time(payload["expires_at"]) > _time(scope["valid_until"]):
                errors.add("action_expired_or_outside_scope")
            if payload["budget"]["runtime_seconds"] != params["deadline_seconds"]:
                errors.add("budget_parameters_mismatch")
            if payload["budget"]["runtime_seconds"] > context["remaining_runtime_seconds"] or context["remaining_actions"] < 1:
                errors.add("budget_exhausted")
            if payload["profile"] == "zap_baseline_v1":
                if not scope["origin_wide"]:
                    errors.add("origin_wide_required")
                matching = []
                for identifier in payload["basis_observation_ids"]:
                    item = observations.get(identifier)
                    if not item or item["assessment_id"] != assessment_id:
                        continue
                    service = item.get("service")
                    if (service and item["asset"].get("authorized_asset_id") == payload["target"]["id"]
                            and service["transport"] == "tcp" and service["port"] == params["port"]
                            and service["scheme"] == params["scheme"]
                            and item.get("observed_at") is not None
                            and _time(scope["valid_from"]) <= _time(item["observed_at"]) <= now):
                        matching.append(item)
                if not matching:
                    errors.add("http_basis_required")
        if now < _time(scope["valid_from"]):
            errors.add("scope_not_started")
        if now >= _time(scope["valid_until"]):
            errors.add("scope_expired")
    elif kind == "observation":
        artifact = artifacts.get(payload["artifact_id"])
        if artifact is None:
            errors.add("missing_artifact")
        elif artifact["assessment_id"] != assessment_id:
            errors.add("foreign_artifact")
        if payload["observed_at"] is not None and _time(payload["observed_at"]) > _time(payload["ingested_at"]):
            errors.add("future_observation")
    elif kind in ("review", "correlation"):
        finding_id = payload.get("finding_id", context.get("finding_id"))
        finding = findings.get(finding_id)
        if finding is None:
            errors.add("missing_finding")
        elif finding["assessment_id"] != assessment_id:
            errors.add("foreign_finding")
        else:
            revision(payload["expected_revision"], finding["revision"])
        ids = payload.get("evidence_ids", payload.get("observation_ids", []))
        evidence(ids)
        if kind == "correlation" and payload["decision"] == "link" and finding:
            # Compatibility is contextual. Equal titles/CVEs never suffice.
            for identifier in ids:
                item = observations.get(identifier)
                if item and item["assessment_id"] == assessment_id:
                    service = item["service"]
                    finding_service = finding["service"]
                    service_identity = lambda value: None if value is None else tuple(value[key] for key in ("transport", "port", "scheme"))
                    if (item["asset"] != finding["asset"] or service_identity(service) != service_identity(finding_service)
                            or item["location"] != finding["location"]
                            or identifier not in context.get("compatible_observation_ids", [])):
                        errors.add("incompatible_correlation")
    elif kind == "finding":
        evidence(payload["observation_ids"])
        if not any(observations.get(identifier, {}).get("kind") == "vulnerability"
                   for identifier in payload["observation_ids"]):
            errors.add("vulnerability_basis_required")
        for key in ("exposure", "exploitability", "asset_impact"):
            evidence(payload[key]["observation_ids"])
        for source in payload["risk_input_sources"]:
            evidence(source["observation_ids"])
        if payload["validation_evidence"]:
            evidence(payload["validation_evidence"]["observation_ids"])
        if payload["priority"] != review_priority(payload):
            errors.add("unknown_priority_floor" if payload["severity"] == "unknown"
                       and payload["priority"] == "routine" else "priority_mismatch")
        supported_cves = set(context.get("supported_cve_ids", []))
        if not set(payload["cve_ids"]) <= supported_cves:
            errors.add("unsupported_cve")
        source_fields = {row["field"] for row in payload["risk_input_sources"]
                         if row["observation_ids"] or row["analyst"]}
        required = {key for key in ("exposure", "exploitability", "asset_impact")
                    if payload[key]["value"] != "unknown"}
        if payload["severity"] != "unknown":
            required.add("severity")
        if payload["cvss"] is not None:
            required.add("cvss")
        if not required <= source_fields:
            errors.add("missing_risk_provenance")
    elif kind == "async":
        expected = (f"/api/v1/assessments/{assessment_id}/"
                    f"{context['resource_kind']}/{payload['resource_id']}")
        if payload["status_url"] != expected:
            errors.add("status_url_mismatch")
    elif kind == "plan_result":
        decision, proposal = payload["decision"], payload["proposal"]
        if decision["assessment_id"] != assessment_id:
            errors.add("foreign_assessment")
        evidence(decision["basis_observation_ids"])
        if decision["outcome"] == "propose":
            if proposal is None:
                errors.add("proposal_required")
            else:
                authority = proposal["authority"]
                errors.update(semantic_errors("action", authority, context))
                if proposal["action_hash"] != authority_hash("action", authority):
                    errors.add("action_hash_mismatch")
                if proposal["policy_result"] != decision["policy_result"]:
                    errors.add("policy_result_mismatch")
                if (decision["proposal_id"] != proposal["id"]
                        or proposal["id"] != authority["action_id"]
                        or proposal["assessment_id"] != assessment_id
                        or authority["assessment_id"] != assessment_id
                        or decision["state_revision"] != authority["state_revision"]
                        or decision["scope_version"] != authority["scope_version"]
                        or decision["candidate_profile"] != authority["profile"]
                        or set(decision["basis_observation_ids"]) != set(authority["basis_observation_ids"])):
                    errors.add("proposal_reference_mismatch")
        elif proposal is not None:
            errors.add("non_proposal_outcome")
    elif kind == "import":
        job = payload["job"]
        if job["assessment_id"] != assessment_id or job["resource_id"] != payload["id"] or job["kind"] != "import":
            errors.add("job_resource_mismatch")
        artifact = artifacts.get(payload["artifact_id"])
        if artifact is None:
            errors.add("missing_artifact")
        elif artifact["assessment_id"] != assessment_id:
            errors.add("foreign_artifact")
        evidence(payload["observation_ids"])
    elif kind == "report":
        revision(payload["expected_revision"], context["state_revision"])
    elif kind == "approval":
        approval = context["approval"]
        if payload["action_hash"] != approval["action_hash"]:
            errors.add("stale_action")
        if payload["expected_scope_version"] != context["scope"]["version"]:
            errors.add("stale_scope")
        if approval["status"] != "pending":
            errors.add("approval_already_decided")
        if _time(approval["expires_at"]) <= _time(context["now"]):
            errors.add("approval_expired")
        if payload["decision"] == "grant" and context["policy_result"] == "deny":
            errors.add("policy_denied")
    elif kind == "replay":
        # Authentication/membership precede replay; a completed replay precedes
        # revision validation. This pure check specifies no DB concurrency claim.
        previous = context.get("previous_operation")
        if previous:
            if previous["digest"] != request_digest(payload):
                errors.add("idempotency_conflict")
            elif previous["state"] == "in_progress":
                errors.add("operation_in_progress")
    else:
        raise ValueError(f"Unknown semantic case kind: {kind}")
    return sorted(errors)
