from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "platform-api"}


@router.get("/ready")
def ready(request: Request) -> JSONResponse:
    checks = request.app.state.settings.adapter_checks()
    configured = all(value == "configured" for value in checks.values())
    return JSONResponse(
        status_code=200 if configured else 503,
        content={
            "status": "ready" if configured else "configuration_incomplete",
            "checks": checks,
        },
    )
