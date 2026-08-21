from __future__ import annotations

import socket
from urllib.parse import urlparse

import boto3
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import get_settings
from app.db import SessionLocal
from app.staff_auth import fastapi_staff_users, staff_auth_backend
from app.client_auth import fastapi_client_users, client_auth_backend
from app.request_context import begin_request, end_request
from app.routes import (
    admin_catalog,
    catalog_import,
    chat,
    client_appointments,
    client_auth,
    client_documents,
    client_portal,
    demo,
    document_templates,
    erp_integration,
    enterprise,
    finance,
    flow_events,
    heartbeat,
    hr_self_service,
    marketing,
    notifications,
    operations_control,
    public_catalog,
    public_approvals,
    settings,
    staff,
    store,
    work_orders,
)

settings_value = get_settings()
if settings_value.media_backend.lower() in {"filesystem", "local"}:
    settings_value.media_root.mkdir(parents=True, exist_ok=True)
    settings_value.private_evidence_root.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings_value.app_name,
    version=settings_value.app_version,
    docs_url="/docs" if not settings_value.production else None,
    redoc_url=None,
)


@app.middleware("http")
async def isolate_request_identity(request, call_next):
    token = begin_request()
    try:
        return await call_next(request)
    finally:
        end_request(token)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_value.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Admin-Token",
        "X-Heartbeat-Token",
        "X-Chat-Session-Token",
    ],
)
if settings_value.media_backend.lower() in {"filesystem", "local"}:
    app.mount(
        settings_value.public_media_base_url,
        StaticFiles(directory=settings_value.media_root),
        name="media",
    )
app.include_router(public_catalog.router)
app.include_router(public_approvals.router)
app.include_router(store.router)
app.include_router(store.admin_router)
app.include_router(chat.router)
app.include_router(
    fastapi_client_users.get_auth_router(client_auth_backend),
    prefix="/api/v1/client-auth",
    tags=["client-identity"],
)
app.include_router(
    fastapi_client_users.get_reset_password_router(),
    prefix="/api/v1/client-auth",
    tags=["client-identity"],
)
app.include_router(client_auth.router)
app.include_router(client_appointments.router)
app.include_router(client_documents.router)
app.include_router(client_portal.router)
app.include_router(admin_catalog.router)
app.include_router(work_orders.router)
app.include_router(settings.public_router)
app.include_router(settings.router)
app.include_router(catalog_import.router)
app.include_router(demo.router)
app.include_router(document_templates.router)
app.include_router(erp_integration.router)
app.include_router(enterprise.router)
app.include_router(hr_self_service.router)
app.include_router(flow_events.router)
app.include_router(finance.router)
app.include_router(heartbeat.router)
app.include_router(heartbeat.legacy_router)
app.include_router(marketing.public_router)
app.include_router(marketing.admin_router)
app.include_router(notifications.router)
app.include_router(operations_control.public_router)
app.include_router(operations_control.router)
app.include_router(
    fastapi_staff_users.get_auth_router(staff_auth_backend),
    prefix="/api/v1/staff/auth",
    tags=["staff-identity"],
)
app.include_router(
    fastapi_staff_users.get_reset_password_router(),
    prefix="/api/v1/staff/auth",
    tags=["staff-identity"],
)
app.include_router(staff.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "platform-api",
        "version": settings_value.app_version,
        "node_id": settings_value.node_id,
    }


@app.get("/live", tags=["system"])
def live() -> dict[str, str]:
    return {"status": "live", "service": "platform-api", "version": settings_value.app_version}


@app.get("/startup", tags=["system"])
def startup() -> dict[str, str]:
    return {"status": "started", "service": "platform-api", "version": settings_value.app_version}


def _check_valkey(url: str) -> None:
    parsed = urlparse(url)
    with socket.create_connection(
        (parsed.hostname or "redis-platform", parsed.port or 6379), timeout=2
    ) as connection:
        password = parsed.password
        if password:
            encoded = password.encode()
            connection.sendall(
                b"*2\r\n$4\r\nAUTH\r\n$" + str(len(encoded)).encode() + b"\r\n" + encoded + b"\r\n"
            )
            if not connection.recv(256).startswith(b"+OK"):
                raise RuntimeError("Valkey authentication failed")
        connection.sendall(b"*1\r\n$4\r\nPING\r\n")
        if not connection.recv(256).startswith(b"+PONG"):
            raise RuntimeError("Valkey ping failed")


def _check_s3() -> None:
    client = boto3.client(
        "s3",
        endpoint_url=settings_value.s3_endpoint_url,
        region_name=settings_value.s3_region,
        aws_access_key_id=settings_value.s3_access_key_id.get_secret_value()
        if settings_value.s3_access_key_id
        else None,
        aws_secret_access_key=settings_value.s3_secret_access_key.get_secret_value()
        if settings_value.s3_secret_access_key
        else None,
    )
    client.head_bucket(Bucket=settings_value.s3_bucket)


def _check_http(url: str, headers: dict[str, str] | None = None) -> None:
    with httpx.Client(timeout=3.0, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()


@app.get("/ready", tags=["system"])
def ready() -> dict[str, object]:
    checks: dict[str, str] = {}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "failed"
        raise HTTPException(
            status_code=503, detail={"status": "not-ready", "checks": checks}
        ) from exc

    if settings_value.environment.lower() in {"staging", "production"}:
        try:
            if not settings_value.redis_url:
                raise RuntimeError("REDIS_URL is required")
            _check_valkey(settings_value.redis_url)
            checks["valkey"] = "ok"
            if (
                settings_value.media_backend.lower() == "s3"
                or settings_value.private_evidence_backend.lower() == "s3"
            ):
                _check_s3()
            checks["object_storage"] = (
                "ok"
                if (
                    settings_value.media_backend.lower() == "s3"
                    or settings_value.private_evidence_backend.lower() == "s3"
                )
                else "filesystem"
            )
            frappe_headers = None
            if settings_value.frappe_api_key and settings_value.frappe_api_secret:
                frappe_key = settings_value.frappe_api_key.get_secret_value()
                frappe_secret = settings_value.frappe_api_secret.get_secret_value()
                frappe_headers = {"Authorization": f"token {frappe_key}:{frappe_secret}"}
            if settings_value.frappe_required:
                if not settings_value.frappe_base_url:
                    raise RuntimeError("FRAPPE_BASE_URL is required")
                _check_http(
                    f"{settings_value.frappe_base_url.rstrip('/')}/api/method/ping", frappe_headers
                )
                checks["frappe"] = "ok"
            else:
                checks["frappe"] = "disabled-for-demo"
            if settings_value.expected_schema_revision:
                with SessionLocal() as db:
                    revision = db.execute(
                        text("SELECT version_num FROM alembic_version")
                    ).scalar_one()
                if revision != settings_value.expected_schema_revision:
                    raise RuntimeError("Schema revision does not match the deployed image")
            checks["schema"] = "ok"
            if settings_value.public_chat_enabled:
                _check_http(f"{settings_value.ai_gateway_url.rstrip('/')}/ready")
                checks["ai_gateway"] = "ok"
        except Exception as exc:
            checks.setdefault("dependencies", "failed")
            raise HTTPException(
                status_code=503, detail={"status": "not-ready", "checks": checks}
            ) from exc

    insecure_defaults = []
    if settings_value.production:
        if settings_value.seed_demo_data:
            insecure_defaults.append("seed_demo_data")
        if settings_value.admin_api_token.get_secret_value().startswith("change-"):
            insecure_defaults.append("admin_api_token")
        if settings_value.event_hmac_secret.get_secret_value().startswith("change-"):
            insecure_defaults.append("event_hmac_secret")
        if settings_value.ai_gateway_internal_token.get_secret_value().startswith("change-"):
            insecure_defaults.append("ai_gateway_internal_token")
        if settings_value.chat_session_secret.get_secret_value().startswith("change-"):
            insecure_defaults.append("chat_session_secret")
        if settings_value.client_demo_password.get_secret_value().startswith("change-"):
            insecure_defaults.append("client_demo_password")
    if insecure_defaults:
        checks["security"] = "failed"
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not-ready",
                "checks": checks,
                "invalid_settings": insecure_defaults,
            },
        )
    checks["security"] = "ok"
    return {"status": "ready", "checks": checks, "node_id": settings_value.node_id}
