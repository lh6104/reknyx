"""Contract-registered HTTP seams. Planned operations return truthful typed 501."""
from datetime import timedelta
import hashlib
import secrets
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select, text, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from reknyx.assessments.service import AssessmentService, require_membership
from reknyx.contracts import CONTRACT, parse_json, validate_schema, SCHEMAS
from reknyx.evidence.service import ArtifactService
from reknyx.infrastructure.auth import token_digest, verify_password
from reknyx.infrastructure.errors import DomainError, error_body
from reknyx.infrastructure.events import append_event
from reknyx.infrastructure.idempotency import begin_operation, finalize_known_database_failure
from reknyx.infrastructure.models import Actor, AuthSession, LoginBucket, Assessment, Membership, Message, AuditEvent, Artifact
from reknyx.infrastructure.pagination import page
from reknyx.shared.time import now, timestamp
from .dependencies import get_session, require_origin, require_csrf

from reknyx.infrastructure.models import ObservationRecord, FindingRecord, ReviewRecord, ReportRecord

REVISION = "0003_evidence_analysis"
COOKIE = "reknyx_session"
MUTATIONS = {"post", "put", "patch", "delete"}


def session_body(settings, session):
    return {"actor": {"id": session.actor_id, "display_name": settings.display_name}, "csrf_token": session.csrf_token, "expires_at": timestamp(session.expires_at)}


def response(status, body=None, location=None):
    headers = {"Location": location} if location else {}
    return Response(status_code=status, headers=headers) if body is None else JSONResponse(body, status_code=status, headers=headers)


def _parameters(request, operation):
    """Validate all declared path/query/header parameters without coercing bodies."""
    allowed_query = set()
    values = {}
    for parameter in operation.get("parameters", []):
        if "$ref" in parameter:
            parameter = CONTRACT["components"]["parameters"][parameter["$ref"].split("/")[-1]]
        name, location = parameter["name"], parameter["in"]
        if location == "query":
            allowed_query.add(name)
            if len(request.query_params.getlist(name)) > 1:
                raise DomainError(422, "validation_error")
        source = request.path_params if location == "path" else request.query_params if location == "query" else request.headers
        value = source.get(name)
        if value is None:
            if parameter.get("required"):
                raise DomainError(422, "validation_error")
            continue
        if parameter["schema"].get("type") == "integer":
            try:
                if not value.isascii() or not value.isdigit():
                    raise ValueError()
                value = int(value)
            except ValueError:
                raise DomainError(422, "validation_error")
        try:
            validate_schema(parameter["schema"], value)
        except ValueError as exc:
            raise DomainError(422, "validation_error") from exc
        values[name] = value
    if set(request.query_params) - allowed_query:
        raise DomainError(422, "validation_error", "Unknown query parameter")
    return values


def _login(request, body, db, settings):
    require_origin(settings, request.headers.get("origin"))
    source = request.client.host if request.client else "unknown"
    # One source bucket and one global account bucket prevent arbitrary usernames
    # from growing storage or bypassing the configured account's attempt bound.
    keys = sorted({hashlib.sha256(source.encode()).hexdigest(), hashlib.sha256(("account:" + settings.username).encode()).hexdigest()})
    instant = now()
    for key in keys:
        db.execute(insert(LoginBucket).values(id=key, window_start=instant, attempts=0).on_conflict_do_nothing())
        bucket = db.scalar(select(LoginBucket).where(LoginBucket.id == key).with_for_update())
        if instant - bucket.window_start >= timedelta(minutes=5):
            bucket.window_start, bucket.attempts = instant, 0
        bucket.attempts += 1
        if bucket.attempts > 10:
            db.commit()
            raise DomainError(403, "forbidden", "Login attempt limit reached; retry after the fixed five-minute window")
    if not verify_password(body["password"], settings.password_hash) or body["username"] != settings.username:
        db.commit()
        raise DomainError(401, "unauthenticated", "Invalid credentials")
    db.execute(insert(Actor).values(id=settings.actor_id, username=settings.username, display_name=settings.display_name).on_conflict_do_nothing(index_elements=[Actor.id]))
    old_token = request.cookies.get(COOKIE)
    if old_token and len(old_token) <= 128:
        old = db.get(AuthSession, token_digest(old_token))
        if old:
            old.revoked = True
    token = secrets.token_urlsafe(32)
    auth = AuthSession(token_hash=token_digest(token), actor_id=settings.actor_id, csrf_token=secrets.token_urlsafe(32), expires_at=instant + timedelta(hours=8), revoked=False)
    db.add(auth)
    db.commit()
    result = response(200, session_body(settings, auth))
    result.set_cookie(COOKIE, token, max_age=8 * 3600, expires=auth.expires_at, path="/api/v1", secure=settings.secure_cookie, httponly=True, samesite="strict")
    return result


def _capabilities(settings):
    implemented = {"foundation", "assessments.persistence", "messages.persistence", "evidence", "imports", "imports.nmap_xml", "imports.zap_json", "imports.greenbone_xml", "findings.review", "reports.pdf", "planner"}
    ids = SCHEMAS["Capability"]["properties"]["id"]["enum"]
    result = {"contract_version": "0.1.0", "capabilities": [{"id": item, "availability": "available" if item in implemented else "planned", "reason_code": "phase_one_implemented" if item in implemented else "not_implemented", "message": "Verified with synthetic fixtures and isolated local PostgreSQL; live execution unavailable" if item in implemented else "In development", "mode": "http" if item in implemented else "none", "evidence_level": "local_integration_verified" if item in implemented else "none", "profile": None} for item in ids]}
    for capability in result['capabilities']:
        if capability['id']=='planner':
            from reknyx.security_analysis.readiness import describe
            capability.update(describe(settings))
    return result


def _health(db):
    checks = []
    try:
        db.execute(text("SELECT 1"))
        checks.append({"name": "database", "status": "ok"})
        revisions = list(db.scalars(text("SELECT version_num FROM alembic_version")))
        checks.append({"name": "migrations", "status": "ok" if revisions == [REVISION] else "unavailable"})
    except SQLAlchemyError:
        db.rollback()
        checks.append({"name": "database" if not checks else "migrations", "status": "unavailable"})
    ready = len(checks) == 2 and all(c["status"] == "ok" for c in checks)
    return response(200 if ready else 503, {"status": "ok" if ready else "unavailable", "checks": checks})


def execute(request, operation, body):
    app, settings = request.app, request.app.state.settings
    operation_id = operation["operationId"]
    if operation_id == "getLiveness":
        return response(200, {"status": "ok", "checks": [{"name": "process", "status": "ok"}]})
    with app.state.session_factory() as db:
        if operation_id == "getReadiness":
            return _health(db)
        if operation_id == "login":
            require_origin(settings, request.headers.get("origin"))
            _parameters(request, operation)
            value = _validated_body(operation, body)
            return _login(request, value, db, settings)
        auth = get_session(db, request.cookies.get(COOKIE))
        mutation = request.method.lower() in MUTATIONS
        if mutation:
            require_csrf(settings, auth, request.headers)
        params = _parameters(request, operation)
        assessment_id = request.path_params.get("assessment_id")
        if assessment_id:
            require_membership(db, auth.actor_id, assessment_id)
        if operation_id == "getSession":
            return response(200, session_body(settings, auth))
        if operation_id == "logout":
            auth.revoked = True
            db.commit()
            result = response(204)
            result.delete_cookie(COOKIE, path="/api/v1", secure=settings.secure_cookie, httponly=True, samesite="strict")
            return result
        if operation_id == "getCapabilities":
            return response(200, _capabilities(settings))
        value = _validated_body(operation, body) if mutation else None
        digest_value = value
        if operation_id == "createImport":
            digest_value = {**value, "file_sha256": hashlib.sha256(request.state.upload).hexdigest()}
        if mutation:
            record, replay = begin_operation(db, auth.actor_id, assessment_id, operation_id, request.url.path, request.headers.get("idempotency-key"), digest_value)
            if replay:
                if record.assessment_id:
                    require_membership(db, auth.actor_id, record.assessment_id)
                return response(record.status, record.body, record.location)
            if operation_id == "createPlan":
                from reknyx.security_analysis.assessment_planning import create_plan
                status, result, location = create_plan(db, auth, settings, assessment_id, value, record, request.state.request_id)
                return response(status, result, location)
            namespace = record.namespace
            try:
                try:
                    with db.begin_nested():
                        status, result, location = _dispatch(request, db, auth, operation_id, value, params)
                        db.flush()
                except DomainError as exc:
                    status, result, location = exc.status, error_body(exc, request.state.request_id), None
                    if assessment_id:
                        append_event(db, auth.actor_id, assessment_id, "request.denied", assessment_id, exc.code, "denied")
                record.status, record.body, record.location = status, result, location
                # Attaching a created assessment never changes its replay namespace.
                if operation_id == "createAssessment" and status == 201:
                    record.assessment_id = result["assessment"]["id"]
                db.commit()
            except SQLAlchemyError:
                if operation_id not in {"createAssessment", "replaceScope", "replaceRequest", "appendMessage"}:
                    # Future provider/worker/file operations require their own exact
                    # receipt reconciliation and cannot use this database-only proof.
                    raise
                failure = error_body(DomainError(503, "dependency_unavailable"), request.state.request_id)
                record = finalize_known_database_failure(db, namespace, failure)
                return response(record.status, record.body, record.location)
            return response(status, result, location)
        status, result, location = _dispatch(request, db, auth, operation_id, value, params)
        return result if isinstance(result, Response) else response(status, result, location)


def _validated_body(operation, raw):
    if "requestBody" not in operation:
        if raw:
            raise DomainError(422, "validation_error", "This operation has no request body")
        return None
    content = operation["requestBody"]["content"]
    if "application/json" not in content:
        if not isinstance(raw, dict):
            raise DomainError(415, "unsupported_media_type")
        try:
            validate_schema(content["multipart/form-data"]["schema"], {**raw, "file": "uploaded-bytes"})
        except ValueError as exc:
            raise DomainError(422, "validation_error") from exc
        return raw
    try:
        value = parse_json(raw)
        validate_schema(content["application/json"]["schema"], value)
        return value
    except (ValueError, RecursionError, OverflowError) as exc:
        raise DomainError(422, "validation_error") from exc


def _dispatch(request, db, auth, operation, value, params):
    assessment_id = request.path_params.get("assessment_id")
    assessments = AssessmentService(db, auth.actor_id)
    if operation == "createAssessment":
        result = assessments.create(value)
        return 201, result, "/api/v1/assessments/" + result["assessment"]["id"]
    if operation == "getAssessment":
        return 200, assessments.detail(assessment_id), None
    if operation == "replaceScope":
        return 200, assessments.replace_scope(assessment_id, value)["scope"], None
    if operation == "replaceRequest":
        return 200, assessments.replace_request(assessment_id, value), None
    if operation == "appendMessage":
        result = assessments.append_message(assessment_id, value)
        return 201, result, f"/api/v1/assessments/{assessment_id}/messages"
    from reknyx.infrastructure.models import AnalysisDecision
    if operation == "listActions":
        return 200, {"items": [], "next_cursor": None}, None
    listing = {"listDecisions": AnalysisDecision, "listAssessments": Assessment, "listMessages": Message, "listTimeline": AuditEvent, "listArtifacts": Artifact, "listObservations": ObservationRecord, "listFindings": FindingRecord, "listReports": ReportRecord, "listWorkspaceFindings": FindingRecord, "listWorkspaceReports": ReportRecord, "listWorkspaceTimeline": AuditEvent}
    if operation == "getWorkspaceSummary":
        # One SQL statement provides a consistent authorized count snapshot.
        counts = []
        for model in (Assessment, FindingRecord, ReportRecord):
            field = Assessment.id if model is Assessment else model.assessment_id
            counts.append(select(func.count()).select_from(model).join(Membership, Membership.assessment_id == field).where(Membership.actor_id == auth.actor_id).scalar_subquery())
        a, f, r = db.execute(select(*counts)).one()
        return 200, {"assessment_count": a, "finding_count": f, "report_count": r, "pending_approval_count": 0, "failed_latest_execution_count": 0, "as_of": timestamp(now())}, None
    if operation in {"listWorkspaceApprovals", "listApprovals"}:
        return 200, {"items": [], "next_cursor": None}, None
    if operation in listing:
        model = listing[operation]
        query = select(model)
        if model is Assessment or operation.startswith("listWorkspace"):
            query = query.join(Membership, Membership.assessment_id == (Assessment.id if model is Assessment else model.assessment_id)).where(Membership.actor_id == auth.actor_id)
        else:
            query = query.where(model.assessment_id == assessment_id)
        # CSRF is returned to the browser, so it cannot be the signing secret.
        # Derive a domain-separated per-session key from server-only configured
        # credential material; rotation invalidates old pagination cursors.
        cursor_key = hashlib.sha256(("reknyx:cursor:v1:" + request.app.state.settings.password_hash + ":" + auth.token_hash).encode()).hexdigest()
        if model is FindingRecord and "priority" in params:
            query = query.where(FindingRecord.data["priority"].astext == params["priority"])
        if model is FindingRecord:
            for parameter, field in (("severity", "severity"), ("disposition", "analyst_disposition")):
                if parameter in params:
                    query = query.where(FindingRecord.data[field].astext == params[parameter])
            if "search" in params:
                query = query.where(FindingRecord.data["title"].astext.contains(params["search"], autoescape=True))
        pagination = page
        if model is FindingRecord:
            from reknyx.findings.pagination import page_findings
            pagination = page_findings
        result = pagination(db, model, query, params.get("limit", 50), params.get("cursor"), [auth.actor_id, operation, request.url.path, {k: v for k, v in params.items() if k != "cursor"}], cursor_key)
        if operation in {"listWorkspaceFindings", "listWorkspaceReports"}:
            field = {"listWorkspaceFindings": "finding", "listWorkspaceReports": "report", "listWorkspaceTimeline": "event"}[operation]
            result["items"] = [{"assessment": db.get(Assessment, item["assessment_id"]).data, field: item} for item in result["items"]]
        return 200, result, None
    if operation in {"getArtifact", "downloadArtifact"}:
        service = ArtifactService(db, request.app.state.artifact_store, auth.actor_id)
        artifact_id = request.path_params["artifact_id"]
        artifact = service.manifest(assessment_id, artifact_id)
        if operation == "getArtifact":
            return 200, artifact.data, None
        raw = service.read_bytes(assessment_id, artifact_id)
        return 200, Response(raw, media_type=artifact.data["content_type"], headers={"Content-Disposition": f'attachment; filename="{artifact_id}"', "X-Content-Type-Options": "nosniff", "X-Content-SHA256": artifact.data["sha256"]}), None
    from reknyx.evidence.imports import ImportService
    from reknyx.findings.service import FindingsService
    store = request.app.state.artifact_store
    if operation == "createImport":
        result = ImportService(db, store, auth.actor_id).create(assessment_id, value, request.state.upload)
        return 202, result, result["status_url"]
    if operation == "getImport":
        return 200, ImportService(db, store, auth.actor_id).get(assessment_id, request.path_params["import_id"]), None
    if operation in {"getFinding", "reviewFinding"}:
        service = FindingsService(db, auth.actor_id)
        finding_id = request.path_params["finding_id"]
        return (200, service.get(assessment_id, finding_id), None) if operation == "getFinding" else (201, service.review(assessment_id, finding_id, value), None)
    from reknyx.reporting.service import ReportService
    service = ReportService(db, store, auth.actor_id)
    if operation == "createReport":
        result = service.create(assessment_id, value)
        return 202, result, result["status_url"]
    if operation == "getReport":
        return 200, service.get(assessment_id, request.path_params["report_id"]), None
    if operation == "getReportSnapshot":
        return 200, service.get_snapshot(assessment_id, request.path_params["report_id"]), None
    if operation == "downloadReport":
        raw = service.download(assessment_id, request.path_params["report_id"])
        return 200, Response(raw, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="assessment.pdf"', "X-Content-SHA256": hashlib.sha256(raw).hexdigest()}), None
    raise DomainError(501, "capability_not_implemented", "In development")


def install_routes(app):
    def make_endpoint(operation):
        async def endpoint(request: Request):
            # Stream cap avoids trusting Content-Length and allocating unbounded IO.
            raw = bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > (21 * 1024 * 1024 if operation["operationId"] == "createImport" else 256 * 1024):
                    raise DomainError(413, "request_too_large")
            if raw and "application/json" in operation.get("requestBody", {}).get("content", {}):
                if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                    raise DomainError(415, "unsupported_media_type")
            if operation["operationId"] == "createImport":
                if not request.headers.get("content-type", "").startswith("multipart/form-data;"):
                    raise DomainError(415, "unsupported_media_type")
                request._body = bytes(raw)
                from starlette.datastructures import UploadFile
                try:
                    async with request.form(max_files=1, max_fields=4, max_part_size=20 * 1024 * 1024) as form:
                        if len(form.multi_items()) != 5 or set(form) != {"file", "kind", "observed_at", "provenance", "source_label"} or not isinstance(form["file"], UploadFile):
                            raise DomainError(422, "validation_error")
                        media = form["file"].content_type
                        expected_media = "application/json" if form["kind"] == "zap_json" else "application/xml"
                        if media != expected_media:
                            raise DomainError(415, "unsupported_media_type")
                        upload = await form["file"].read(20 * 1024 * 1024 + 1)
                        if len(upload) > 20 * 1024 * 1024:
                            raise DomainError(413, "request_too_large")
                        if not upload:
                            raise DomainError(422, "validation_error", "Upload must contain original bytes")
                        request.state.upload = upload
                        body = {key: form[key] for key in form if key != "file"}
                        if any(not isinstance(v, str) for v in body.values()):
                            raise DomainError(422, "validation_error")
                        body["observed_at"] = None if body["observed_at"] in ("", "null") else body["observed_at"]
                except DomainError:
                    raise
                except Exception as exc:
                    raise DomainError(422, "validation_error", "Invalid multipart upload") from exc
                return await run_in_threadpool(execute, request, operation, body)
            return await run_in_threadpool(execute, request, operation, bytes(raw))
        return endpoint
    for path, item in CONTRACT["paths"].items():
        for method, operation in item.items():
            app.add_api_route("/api/v1" + path, make_endpoint(operation), methods=[method.upper()], name=operation["operationId"], operation_id=operation["operationId"])
