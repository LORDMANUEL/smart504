from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compose_runs_two_internal_ai_gateway_replicas() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert {"ai-gateway-a", "ai-gateway-b"} <= set(services)
    for name in ("ai-gateway-a", "ai-gateway-b"):
        assert "healthcheck" in services[name]
        assert "ports" not in services[name]
    haproxy = (ROOT / "infra/haproxy/haproxy.cfg").read_text(encoding="utf-8")
    assert "frontend ai_gateway" in haproxy
    assert "ai-gateway-a:8000" in haproxy
    assert "ai-gateway-b:8000" in haproxy


def test_public_site_contains_chatbot_component_and_no_secret() -> None:
    app = (ROOT / "apps/public-web/src/App.tsx").read_text(encoding="utf-8")
    widget = ROOT / "apps/public-web/src/components/ChatWidget.tsx"
    assert widget.exists()
    assert "<ChatWidget" in app
    text = widget.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" not in text
    assert "AI_GATEWAY_INTERNAL_TOKEN" not in text


def test_release_fetches_pinned_beveren_and_applies_v16_patch() -> None:
    containerfile = (ROOT / "infra/frappe/Containerfile").read_text(encoding="utf-8")
    patch = (ROOT / "infra/frappe/patches/beveren/0001-v16-compat.patch").read_text(encoding="utf-8")
    assert "BEVEREN_REF=ab6d56d1069882326475f256d09cc63236eddec1" in containerfile
    assert "git checkout --detach ${BEVEREN_REF}" in containerfile
    assert "git apply /tmp/0001-v16-compat.patch" in containerfile
    assert "from erpnext.controllers.selling_controller import SellingController" in patch
    assert "class ServiceOrder(SellingController)" in patch


def test_public_contact_actions_are_build_time_configurable_and_not_hardcoded() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    for name in ("public-web-a", "public-web-b"):
        args = compose["services"][name]["build"]["args"]
        assert "VITE_BUSINESS_PHONE" in args
        assert "VITE_WHATSAPP_URL" in args
        assert "VITE_BUSINESS_ADDRESS" in args

    dockerfile = (ROOT / "apps/public-web/Dockerfile").read_text(encoding="utf-8")
    for variable in ("VITE_BUSINESS_PHONE", "VITE_WHATSAPP_URL", "VITE_BUSINESS_ADDRESS"):
        assert f"ARG {variable}" in dockerfile
        assert f"ENV {variable}=${{{variable}}}" in dockerfile

    app = (ROOT / "apps/public-web/src/App.tsx").read_text(encoding="utf-8")
    widget = (ROOT / "apps/public-web/src/components/ChatWidget.tsx").read_text(encoding="utf-8")
    assert "+50400000000" not in app
    assert "50400000000" not in widget
    assert "VITE_WHATSAPP_URL" in widget


def test_public_photo_sources_are_real_existing_commons_assets_with_attribution() -> None:
    fetcher = (ROOT / "scripts/fetch-public-assets.sh").read_text(encoding="utf-8")
    attribution = (ROOT / "apps/public-web/public/images/stock/ATTRIBUTION.md").read_text(encoding="utf-8")
    app = (ROOT / "apps/public-web/src/App.tsx").read_text(encoding="utf-8")
    assert "commons.wikimedia.org" in fetcher
    assert "Wikimedia Commons" in attribution
    assert "dominio público" in attribution
    assert "CC0" in attribution
    assert "commons.wikimedia.org" in app
    assert "images.pexels.com" not in app


def test_public_openapi_contract_documents_chatbot_store_and_admin_media() -> None:
    contract = yaml.safe_load((ROOT / "contracts/openapi-public.yaml").read_text(encoding="utf-8"))
    paths = contract["paths"]
    for path in (
        "/api/v1/chat/sessions",
        "/api/v1/chat/sessions/{session_id}/messages",
        "/api/v1/chat/sessions/{session_id}/close",
        "/api/v1/store/orders",
        "/api/v1/admin/catalog/products/{product_id}/images/upload",
        "/api/v1/admin/catalog/images/google",
        "/api/v1/operations/work-orders/board",
        "/api/v1/operations/work-orders/{work_order_id}/transitions",
    ):
        assert path in paths
    assert contract["info"]["version"] == "0.4.0"
