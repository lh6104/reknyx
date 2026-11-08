"""Explicit local configuration. Passwords are accepted only as salted hashes."""
from dataclasses import dataclass, field
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid5, NAMESPACE_URL


@dataclass(frozen=True)
class Settings:
    database_url: str
    artifact_root: Path
    password_hash: str
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    username: str = "admin"
    display_name: str = "Local administrator"
    actor_id: str = field(default_factory=lambda: str(uuid5(NAMESPACE_URL, "reknyx:local-admin")))
    cookie_secure: bool | None = None
    max_artifact_bytes: int = 20 * 1024 * 1024
    enable_api_docs: bool = False
    analysis_provider: str = "deterministic"
    groq_api_key: str = field(default="", repr=False)
    groq_synthetic_enabled: bool = False
    groq_free_plan_confirmed: bool = False
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.1
    groq_reasoning_effort: str = "low"
    groq_max_output_tokens: int = 1024

    def __post_init__(self):
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("PostgreSQL with psycopg is required")
        if not self.password_hash.startswith("scrypt$"):
            raise ValueError("Configure a scrypt password hash, never plaintext")
        if self.analysis_provider not in {"deterministic", "groq"}:
            raise ValueError("Unsupported analysis provider")
        from reknyx.security_analysis.model_providers.groq import options_for
        options_for(self)
        UUID(self.actor_id)
        if not self.allowed_origins or not self.username or len(self.username) > 100:
            raise ValueError("A username and exact origins are required")
        for origin in self.allowed_origins:
            parts = urlsplit(origin)
            if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.path or parts.query or parts.fragment:
                raise ValueError("Origins must be exact HTTP(S) origins without a path")
        remote = any(urlsplit(o).hostname not in {"localhost", "127.0.0.1", "::1"} for o in self.allowed_origins)
        if remote and (self.cookie_secure is False or any(urlsplit(o).scheme != "https" for o in self.allowed_origins)):
            raise ValueError("Non-loopback origins require HTTPS and secure cookies")

    @property
    def secure_cookie(self):
        return self.cookie_secure if self.cookie_secure is not None else any(urlsplit(o).scheme == "https" for o in self.allowed_origins)

    @classmethod
    def from_env(cls):
        return cls(database_url=os.environ["REKNYX_DATABASE_URL"], artifact_root=Path(os.environ["REKNYX_ARTIFACT_ROOT"]), password_hash=os.environ["REKNYX_PASSWORD_HASH"], username=os.getenv("REKNYX_USERNAME", "admin"), display_name=os.getenv("REKNYX_DISPLAY_NAME", "Local administrator"), actor_id=os.getenv("REKNYX_ACTOR_ID", str(uuid5(NAMESPACE_URL, "reknyx:local-admin"))), allowed_origins=tuple(os.getenv("REKNYX_ALLOWED_ORIGINS", "http://localhost:3000").split(",")), groq_model=os.getenv("REKNYX_GROQ_MODEL", "openai/gpt-oss-120b"), groq_temperature=float(os.getenv("REKNYX_GROQ_TEMPERATURE", "0.1")), groq_reasoning_effort=os.getenv("REKNYX_GROQ_REASONING_EFFORT", "low"), groq_max_output_tokens=int(os.getenv("REKNYX_GROQ_MAX_OUTPUT_TOKENS", "1024")), analysis_provider=os.getenv("REKNYX_ANALYSIS_PROVIDER", "deterministic"), groq_api_key=os.getenv("REKNYX_GROQ_API_KEY", ""), groq_free_plan_confirmed=os.getenv("REKNYX_GROQ_FREE_PLAN_CONFIRMED", "false").lower()=="true", groq_synthetic_enabled=os.getenv("REKNYX_GROQ_SYNTHETIC_ENABLED", "false").lower()=="true", enable_api_docs=os.getenv("REKNYX_ENABLE_API_DOCS", "false").lower() == "true")
