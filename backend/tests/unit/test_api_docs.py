"""The API documentation is opt-in and uses the reviewed contract."""
from fastapi.testclient import TestClient

from reknyx.config import Settings
from reknyx.contracts import CONTRACT
from reknyx.main import create_app


def test_api_docs_are_opt_in(monkeypatch, tmp_path):
    monkeypatch.setenv("REKNYX_DATABASE_URL", "postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
    monkeypatch.setenv("REKNYX_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("REKNYX_PASSWORD_HASH", "scrypt$unused")
    monkeypatch.delenv("REKNYX_ENABLE_API_DOCS", raising=False)
    with TestClient(create_app(Settings.from_env())) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404

    monkeypatch.setenv("REKNYX_ENABLE_API_DOCS", "true")
    with TestClient(create_app(Settings.from_env())) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").json() == CONTRACT
