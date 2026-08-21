from __future__ import annotations

from app.config import Settings


def test_cors_origins_accept_comma_separated_value(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://smartdiag504.com, https://app.smartdiag504.com")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == [
        "https://smartdiag504.com",
        "https://app.smartdiag504.com",
    ]


def test_cors_origins_accept_empty_value(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == []
