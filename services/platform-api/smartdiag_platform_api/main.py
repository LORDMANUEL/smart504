from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .repositories import InMemoryRepository
from .routers import bookings, catalog, events, health
from .settings import Settings


def create_app(*, testing: bool = False) -> FastAPI:
    settings = Settings.from_env(testing=testing)
    application = FastAPI(
        title="SmartDiag504 Platform API",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )
    application.state.settings = settings
    application.state.repository = InMemoryRepository()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key", "X-SmartDiag-Signature"],
    )
    application.include_router(health.router)
    application.include_router(catalog.router)
    application.include_router(bookings.router)
    application.include_router(events.router)
    return application


app = create_app()
