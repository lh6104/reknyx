"""Synthetic scope checks confer no authorization to send live traffic."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from reknyx.assessments.scope import allows_destination
from reknyx.assessments.service import make_scope
from reknyx.infrastructure.errors import DomainError


@pytest.fixture
def scope():
    ref = str(uuid4())
    return make_scope(str(uuid4()), 1, {"authorization_ref_id": ref, "asset": {"id": str(uuid4()), "hostname": "web.lab.example", "ipv4": "192.0.2.20", "aliases": ["alias.lab.example"], "authorization_ref_id": ref}, "allowed_ports": [8080, 8081], "excluded_ports": [8081], "allowed_profiles": [], "valid_from": "2026-11-01T00:00:00Z", "valid_until": "2026-12-01T00:00:00Z", "budget": {"max_actions": 0, "max_runtime_seconds": 0, "max_model_calls": 0, "max_input_tokens": 0, "max_output_tokens": 0}, "origin_wide": False})


def test_exact_hosts_exclusions_and_validity(scope):
    clock = lambda: datetime(2026, 11, 6, tzinfo=timezone.utc)
    assert allows_destination(scope, "WEB.LAB.EXAMPLE.", 8080, clock=clock)
    assert allows_destination(scope, "alias.lab.example", 8080, clock=clock)
    assert allows_destination(scope, "192.0.2.20", 8080, clock=clock)
    for host in ("web.lab.example.attacker.test", "user@web.lab.example", "http://web.lab.example", "192.0.2.21", "::ffff:192.0.2.20"):
        assert not allows_destination(scope, host, 8080, clock=clock)
    for port in (0, 65536, True, 8081, 443):
        assert not allows_destination(scope, "web.lab.example", port, clock=clock)
    assert not allows_destination(scope, "web.lab.example", 8080, clock=lambda: datetime(2026, 12, 1, tzinfo=timezone.utc))


def test_normalized_duplicate_aliases_and_unmatched_references_are_typed(scope):
    value = {key: deepcopy(item) for key, item in scope.items() if key not in {"assessment_id", "version", "hash"}}
    value["asset"]["aliases"] = ["alias.lab.example", "ALIAS.LAB.EXAMPLE."]
    with pytest.raises(DomainError) as duplicate:
        make_scope(scope["assessment_id"], 2, value)
    assert duplicate.value.code == "validation_error"
    value["asset"]["aliases"] = []
    value["asset"]["authorization_ref_id"] = str(uuid4())
    with pytest.raises(DomainError):
        make_scope(scope["assessment_id"], 2, value)


def test_scope_uses_shared_hash_authority(scope):
    from reknyx.contracts import HASH_AUTHORITY
    original = {k: v for k, v in scope.items() if k != "hash"}
    assert scope["hash"] == HASH_AUTHORITY.authority_hash("scope", original)
    changed = {**original, "version": 2}
    assert scope["hash"] != HASH_AUTHORITY.authority_hash("scope", changed)
