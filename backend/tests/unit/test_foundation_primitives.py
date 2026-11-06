"""Synthetic tests for foundation boundaries; no scanner/provider calls."""
import hashlib
import uuid

import pytest


def test_password_hash_is_salted_and_verifies():
    from reknyx.infrastructure.auth import hash_password, verify_password
    value = uuid.uuid4().hex
    hashed = hash_password(value)
    assert value not in hashed
    assert hashed != hash_password(value)
    assert verify_password(value, hashed)
    assert not verify_password(uuid.uuid4().hex, hashed)
    assert not verify_password(value, "broken")


def test_exact_bytes_private_storage_and_integrity(tmp_path):
    from reknyx.evidence.storage import LocalArtifactStore, IntegrityError
    store = LocalArtifactStore(tmp_path / "private")
    raw = b"<report>\r\nraw &amp; bytes</report>"
    blob = store.put(raw)
    assert store.get(blob.storage_key, blob.sha256) == raw
    assert blob.sha256 == hashlib.sha256(raw).hexdigest()
    assert blob.size == len(raw)
    assert (store.root.stat().st_mode & 0o777) == 0o700
    with pytest.raises(ValueError):
        store.get("../escape")
    (store.root / blob.storage_key).write_bytes(b"changed")
    with pytest.raises(IntegrityError):
        store.get(blob.storage_key, blob.sha256)


def test_storage_rejects_symlinks_empty_and_oversize(tmp_path):
    from reknyx.evidence.storage import LocalArtifactStore, IntegrityError
    store = LocalArtifactStore(tmp_path / "private", max_bytes=8)
    with pytest.raises(ValueError):
        store.put(b"")
    with pytest.raises(ValueError):
        store.put(b"123456789")
    target = tmp_path / "outside"
    target.write_bytes(b"secret")
    key = uuid.uuid4().hex
    (store.root / key).symlink_to(target)
    with pytest.raises(IntegrityError):
        store.get(key)


def test_strict_json_rejects_duplicates_nonfinite_and_extra_fields():
    from reknyx.contracts import parse_json, validate
    for raw in [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'{"a":"\\ud800"}']:
        with pytest.raises(ValueError):
            parse_json(raw)
    with pytest.raises(ValueError):
        validate("LoginRequest", {"username": "u", "password": "x", "actor_id": str(uuid.uuid4())})


def test_unavailable_database_is_not_ready(tmp_path):
    from fastapi.testclient import TestClient
    from reknyx.config import Settings
    from reknyx.main import create_app
    from reknyx.infrastructure.auth import hash_password
    settings = Settings(database_url="postgresql+psycopg://nobody:unused@127.0.0.1:1/missing?connect_timeout=1", artifact_root=tmp_path, password_hash=hash_password(uuid.uuid4().hex))
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/health/live").json()["status"] == "ok"
        assert client.get("/api/v1/health/ready").status_code == 503
        assert client.post("/api/v1/assessments", json={}).status_code == 401
