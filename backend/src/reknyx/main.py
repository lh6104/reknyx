"""FastAPI assembly. Startup never creates tables or enables planned operations."""
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from reknyx.api.router import install_routes, error_body
from reknyx.config import Settings
from reknyx.contracts import CONTRACT
from reknyx.evidence.storage import LocalArtifactStore
from reknyx.infrastructure.db import build_database
from reknyx.infrastructure.errors import DomainError


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    engine, factory = build_database(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(title="Reknyx", version="0.1.0", lifespan=lifespan, docs_url="/docs" if settings.enable_api_docs else None, redoc_url=None, openapi_url="/openapi.json" if settings.enable_api_docs else None)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.artifact_store = LocalArtifactStore(settings.artifact_root, settings.max_artifact_bytes)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"], expose_headers=["X-Request-ID", "Location", "X-Content-SHA256", "Retry-After"])

    @app.middleware("http")
    async def metadata(request, call_next):
        request.state.request_id = str(uuid4())
        result = await call_next(request)
        result.headers["X-Request-ID"] = request.state.request_id
        result.headers["Cache-Control"] = "no-store"
        result.headers["X-Content-Type-Options"] = "nosniff"
        return result

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(error_body(exc, request.state.request_id), status_code=exc.status, headers={"Retry-After": str(exc.retry_after)} if exc.retry_after else None)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        return JSONResponse(error_body(DomainError(503, "dependency_unavailable"), request.state.request_id), status_code=503)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        status = 404 if exc.status_code == 404 else 422
        return JSONResponse(error_body(DomainError(status, "not_found" if status == 404 else "validation_error"), request.state.request_id), status_code=status)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return JSONResponse(error_body(DomainError(500, "internal_error"), request.state.request_id), status_code=500, headers={"Cache-Control": "no-store", "X-Request-ID": request.state.request_id})

    install_routes(app)
    # The exported document remains the candidate authority, including its pending
    # owner/runtime metadata. Runtime capability truth comes from /capabilities.
    app.openapi = lambda: CONTRACT
    return app
