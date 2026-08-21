from __future__ import annotations

from fastapi import Request

from .repositories import InMemoryRepository
from .settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_repository(request: Request) -> InMemoryRepository:
    return request.app.state.repository
