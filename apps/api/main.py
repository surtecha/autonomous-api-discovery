"""Authenticated control plane. Target destinations are administrator-configured only."""

from __future__ import annotations

import hmac
import json
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text

from packages.discovery.persistence import Store
from packages.discovery.security import TargetPolicy

from .database import AuditEvent, DiscoverySession, database
from .settings import Settings


class CreateSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str = Field(pattern=r"^[a-z_]{1,32}$")
    budget: int = Field(default=100, ge=1, le=200)
    strategy: Literal["gain", "fifo", "random", "llm"] = "gain"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine, sessions = database(settings.database_url.get_secret_value())
    policies = {
        name: TargetPolicy(**value)
        for name, value in json.loads(settings.policy_file.read_text()).items()
    }
    for policy in policies.values():
        policy.validate()

    def authorize(authorization: Annotated[str | None, Header()] = None) -> None:
        expected = "Bearer " + settings.backend_api_token.get_secret_value()
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise HTTPException(401, "Authentication required")

    app = FastAPI(
        title="API Discovery Control Plane",
        version="0.1.0",
        dependencies=[Depends(authorize)],
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.middleware("http")
    async def headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "POST":
            length = request.headers.get("content-length", "")
            if (
                not length.isdigit()
                or int(length) > 4096
                or request.headers.get("transfer-encoding")
            ):
                return JSONResponse(
                    {"detail": "Bounded request content length required"}, status_code=413
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": "Request validation failed"}, status_code=422)

    @app.exception_handler(Exception)
    async def safe_failure(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse({"detail": "Internal operation failed"}, status_code=500)

    def row(session_id: uuid.UUID) -> DiscoverySession:
        with sessions() as db:
            found = db.get(DiscoverySession, str(session_id))
            if found is None:
                raise HTTPException(404, "Session not found")
            return found

    def summary(item: DiscoverySession) -> dict[str, Any]:
        return {
            "id": item.id,
            "target": item.target,
            "status": item.status,
            "strategy": item.strategy,
            "budget": item.budget,
            "created_at": item.created_at,
            "result": item.result,
        }

    @app.get("/api/v1/openapi", include_in_schema=False)
    def api_schema() -> dict[str, Any]:
        return app.openapi()

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/readiness")
    def readiness() -> dict[str, str]:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    @app.get("/api/v1/targets")
    def targets() -> list[dict[str, Any]]:
        return [
            {"id": name, "disposable": policy.disposable, "max_requests": policy.max_requests}
            for name, policy in policies.items()
        ]

    @app.post("/api/v1/discovery-sessions", status_code=202)
    def create(body: CreateSession) -> dict[str, Any]:
        if body.target not in policies:
            raise HTTPException(422, "Target is not authorized")
        if body.budget > policies[body.target].max_requests:
            raise HTTPException(422, "Target request budget exceeded")
        with sessions.begin() as db:
            # Serialize quota checks across API processes using a transaction-scoped lock.
            db.execute(text("SELECT pg_advisory_xact_lock(180513)"))
            active = db.scalar(
                select(func.count())
                .select_from(DiscoverySession)
                .where(DiscoverySession.status.in_(["queued", "running"]))
            )
            if active is not None and active >= 8:
                raise HTTPException(429, "Session quota reached")
            item = DiscoverySession(target=body.target, budget=body.budget, strategy=body.strategy)
            db.add(item)
            db.flush()
            db.add(
                AuditEvent(session_id=item.id, category="created", payload={"target": body.target})
            )
            return summary(item)

    @app.get("/api/v1/discovery-sessions")
    def listing(
        limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
    ) -> list[dict[str, Any]]:
        with sessions() as db:
            values = db.scalars(
                select(DiscoverySession)
                .order_by(DiscoverySession.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return [summary(item) for item in values]

    @app.get("/api/v1/discovery-sessions/{session_id}")
    def details(session_id: uuid.UUID) -> dict[str, Any]:
        return summary(row(session_id))

    @app.post("/api/v1/discovery-sessions/{session_id}/cancel")
    def cancel(session_id: uuid.UUID) -> dict[str, str]:
        with sessions.begin() as db:
            item = db.get(DiscoverySession, str(session_id), with_for_update=True)
            if item is None:
                raise HTTPException(404, "Session not found")
            if item.status in {"queued", "running"}:
                item.status = "cancelled"
                directory = settings.artifact_root / str(session_id)
                store = Store(directory / "evidence.sqlite")
                if store.load(str(session_id)) is None:
                    from packages.discovery.engine import initialize

                    store.save(initialize(str(session_id), strategy=item.strategy))
                store.cancel(str(session_id))
                store.close()
                db.add(AuditEvent(session_id=item.id, category="cancelled", payload={}))
            return {"status": item.status}

    @app.get("/api/v1/discovery-sessions/{session_id}/events")
    def events(session_id: uuid.UUID) -> list[dict[str, Any]]:
        row(session_id)
        with sessions() as db:
            return [
                {"id": event.id, "category": event.category, "payload": event.payload}
                for event in db.scalars(
                    select(AuditEvent)
                    .where(AuditEvent.session_id == str(session_id))
                    .order_by(AuditEvent.id)
                    .limit(500)
                )
            ]

    @app.get("/api/v1/discovery-sessions/{session_id}/evidence/{section}")
    def evidence(
        session_id: uuid.UUID,
        section: Literal["operations", "observations", "transitions", "relationships"],
    ) -> Any:
        row(session_id)
        path = settings.artifact_root / str(session_id) / "knowledge.json"
        if path.exists():
            return json.loads(path.read_text())[section]
        checkpoint = path.parent / "evidence.sqlite"
        if checkpoint.exists():
            store = Store(checkpoint)
            try:
                state = store.load(str(session_id))
                if state:
                    return state.to_dict()[section]
            finally:
                store.close()
        return {} if section == "operations" else []

    @app.get("/api/v1/discovery-sessions/{session_id}/artifacts/{name}")
    def artifact(
        session_id: uuid.UUID, name: Literal["openapi", "sdk", "tests", "validation", "report"]
    ) -> FileResponse:
        row(session_id)
        names = {
            "openapi": "sdk/openapi.json",
            "sdk": "sdk.zip",
            "tests": "sdk/test_client.py",
            "validation": "sdk/validation.json",
            "report": "knowledge.json",
        }
        path = settings.artifact_root / str(session_id) / names[name]
        if not path.is_file():
            raise HTTPException(404, "Artifact is not available")
        return FileResponse(path, filename=path.name)

    return app
