from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "https://smartdiag504.com,https://app.smartdiag504.com",
            ["https://smartdiag504.com", "https://app.smartdiag504.com"],
        ),
        ("http://testserver", ["http://testserver"]),
    ],
)
def test_platform_settings_accept_human_readable_cors_origins(monkeypatch, raw, expected) -> None:
    from app.config import Settings

    monkeypatch.setenv("CORS_ORIGINS", raw)

    settings = Settings(_env_file=None)

    assert settings.cors_origins == expected


def test_demo_seed_is_opt_in(monkeypatch) -> None:
    from app.config import Settings

    monkeypatch.delenv("SEED_DEMO_DATA", raising=False)
    assert Settings(_env_file=None).seed_demo_data is False

    monkeypatch.setenv("SEED_DEMO_DATA", "true")
    assert Settings(_env_file=None).seed_demo_data is True
