from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.yaml"
PREVIEW = ROOT / "compose.preview.yaml"

REQUIRED_PRODUCTION_SERVICES = {
    "caddy",
    "haproxy",
    "public-web-a",
    "public-web-b",
    "ops-web-a",
    "ops-web-b",
    "platform-migrate",
    "platform-seed",
    "platform-api-a",
    "platform-api-b",
    "ai-gateway-a",
    "ai-gateway-b",
    "heartbeat-a",
    "heartbeat-b",
    "alerts-worker-a",
    "alerts-worker-b",
    "postgres",
    "redis-platform",
    "chromadb",
    "garage-configurator",
    "garage",
    "mariadb",
    "redis-cache",
    "redis-queue",
    "frappe-configurator",
    "frappe-site-init",
    "frappe-backend",
    "frappe-frontend",
    "frappe-websocket",
    "frappe-queue-short",
    "frappe-queue-long",
    "frappe-scheduler",
    "backup-runner",
}

ONE_SHOT_SERVICES = {
    "platform-migrate",
    "platform-seed",
    "garage-configurator",
    "frappe-configurator",
    "frappe-site-init",
}
LONG_RUNNING_SERVICES = REQUIRED_PRODUCTION_SERVICES - ONE_SHOT_SERVICES


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_production_compose_has_complete_replicated_topology() -> None:
    data = load(COMPOSE)
    services = data["services"]
    assert REQUIRED_PRODUCTION_SERVICES <= set(services)
    assert data["networks"]["app"]["internal"] is True
    assert data["networks"]["data"]["internal"] is True
    assert data["networks"]["egress"].get("internal") is not True
    for service_name in LONG_RUNNING_SERVICES:
        assert "healthcheck" in services[service_name], f"{service_name} needs a healthcheck"


def test_databases_and_internal_ai_are_not_published_to_host() -> None:
    services = load(COMPOSE)["services"]
    for service_name in (
        "postgres",
        "redis-platform",
        "mariadb",
        "redis-cache",
        "redis-queue",
        "chromadb",
        "garage",
        "ai-gateway-a",
        "ai-gateway-b",
        "ollama",
    ):
        assert "ports" not in services[service_name], f"{service_name} must stay private"


def test_preview_exposes_balancers_without_changing_service_names() -> None:
    services = load(PREVIEW)["services"]
    required = {
        "haproxy",
        "public-web-a",
        "public-web-b",
        "ops-web-a",
        "ops-web-b",
        "platform-api-a",
        "platform-api-b",
        "ai-gateway-a",
        "ai-gateway-b",
    }
    assert required <= set(services)
    assert {
        "18080:8080",
        "18081:8081",
        "18082:8082",
        "18083:8083",
        "18404:8404",
    } <= set(services["haproxy"]["ports"])


def test_caddy_routes_public_operations_api_and_erp_surfaces() -> None:
    caddy = (ROOT / "infra" / "caddy" / "Caddyfile").read_text(encoding="utf-8")
    for variable in (
        "PUBLIC_SITE_ADDRESS",
        "CUSTOMER_SITE_ADDRESS",
        "OPS_SITE_ADDRESS",
        "API_SITE_ADDRESS",
        "ERP_SITE_ADDRESS",
    ):
        assert f"{{${variable}}}" in caddy
    assert "reverse_proxy haproxy:8080" in caddy
    assert "reverse_proxy haproxy:8081" in caddy
    assert "reverse_proxy haproxy:8082" in caddy
    assert "reverse_proxy frappe-frontend:8080" in caddy
    assert "ai-gateway-a" not in caddy


def test_haproxy_balances_every_replicated_application_surface() -> None:
    config = (ROOT / "infra" / "haproxy" / "haproxy.cfg").read_text(encoding="utf-8")
    for frontend in ("public_web", "ops_web", "platform_api", "ai_gateway"):
        assert f"frontend {frontend}" in config
    for server in (
        "public-web-a:8080",
        "public-web-b:8080",
        "ops-web-a:8080",
        "ops-web-b:8080",
        "platform-api-a:8000",
        "platform-api-b:8000",
        "ai-gateway-a:8000",
        "ai-gateway-b:8000",
    ):
        assert server in config


def test_optional_profiles_are_explicit_and_private() -> None:
    services = load(COMPOSE)["services"]
    assert services["ollama"]["profiles"] == ["local-ai"]
    assert services["ollama-model-init"]["profiles"] == ["local-ai"]
    assert services["ollama"]["image"] == "ollama/ollama:0.32.5"
    assert "ports" not in services["ollama"]
    for name in ("blackbox-exporter", "prometheus", "grafana"):
        assert "observability" in services[name]["profiles"]
    assert services["prometheus"]["ports"][0].startswith("127.0.0.1:")
    assert services["grafana"]["ports"][0].startswith("127.0.0.1:")


def test_cache_services_use_valkey_and_pinned_chroma_release() -> None:
    services = load(COMPOSE)["services"]
    for name in ("redis-platform", "redis-cache", "redis-queue"):
        assert "valkey/valkey" in services[name]["image"]
    assert services["chromadb"]["image"] == "chromadb/chroma:1.5.9"


def test_services_that_call_external_providers_have_egress_without_published_ports() -> None:
    services = load(COMPOSE)["services"]
    for name in ("platform-api-a", "platform-api-b", "ai-gateway-a", "ai-gateway-b", "backup-runner"):
        assert "egress" in services[name]["networks"]
        assert "ports" not in services[name]


def test_runtime_ports_match_reverse_proxy_contract() -> None:
    public_dockerfile = (ROOT / "apps/public-web/Dockerfile").read_text(encoding="utf-8")
    ops_dockerfile = (ROOT / "apps/ops-web/Dockerfile").read_text(encoding="utf-8")
    platform_dockerfile = (ROOT / "services/platform-api/Dockerfile").read_text(encoding="utf-8")
    assert "EXPOSE 8080" in public_dockerfile
    assert "127.0.0.1:8080/health" in public_dockerfile
    assert "EXPOSE 8080" in ops_dockerfile
    assert "127.0.0.1:8080/health" in ops_dockerfile
    assert "EXPOSE 8000" in platform_dockerfile
    assert '"--port", "8000"' in platform_dockerfile


def test_frappe_site_init_uses_versioned_bootstrap_and_creates_integration_credentials() -> None:
    compose = load(COMPOSE)
    site_init = compose["services"]["frappe-site-init"]
    containerfile = (ROOT / "infra/frappe/Containerfile").read_text(encoding="utf-8")
    bootstrap = (ROOT / "infra/frappe/bootstrap-site.sh").read_text(encoding="utf-8")
    assert site_init["entrypoint"] == ["/usr/local/bin/bootstrap-site.sh"]
    assert "FRAPPE_API_KEY" in site_init["environment"]
    assert "FRAPPE_API_SECRET" in site_init["environment"]
    assert "COPY infra/frappe/bootstrap-site.sh /usr/local/bin/bootstrap-site.sh" in containerfile
    assert "smartdiag_workshop.setup.integration.ensure_integration_user" in bootstrap
    assert (ROOT / "frappe-apps/smartdiag_workshop/smartdiag_workshop/setup/integration.py").is_file()
