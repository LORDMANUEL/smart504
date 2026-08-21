from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_coolify_compose_is_isolated_and_uses_registry_images() -> None:
    compose = yaml.safe_load((ROOT / "compose.coolify.yaml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert "caddy" not in services
    assert "networks" not in compose
    assert all("networks" not in service for service in services.values())
    assert all("ports" not in service for service in services.values())
    assert all("container_name" not in service for service in services.values())
    assert all("build" not in service for service in services.values())
    assert services["platform-migrate"]["exclude_from_hc"] is True
    assert services["frappe-site-init"]["exclude_from_hc"] is True


def test_private_services_are_not_exposed() -> None:
    compose = yaml.safe_load((ROOT / "compose.coolify.yaml").read_text(encoding="utf-8"))
    for name in ("postgres", "mariadb", "redis-platform", "redis-cache", "redis-queue"):
        assert "expose" not in compose["services"][name]
