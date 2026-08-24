import hashlib
import hmac

from fastapi.testclient import TestClient

from smartdiag_platform_api.main import create_app


client = TestClient(create_app(testing=True))


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog_can_filter_by_query() -> None:
    response = client.get("/api/v1/catalog/products", params={"q": "filtro"})
    assert response.status_code == 200
    products = response.json()["items"]
    assert products
    assert all("filtro" in (item["name"] + item["description"]).lower() for item in products)
    assert all(item["category"] for item in products)


def test_catalog_search_treats_sql_injection_as_plain_text() -> None:
    hostile = "filtro' OR 1=1; DROP TABLE catalog_products; --"
    response = client.get("/api/v1/catalog/products", params={"q": hostile})
    assert response.status_code == 200
    assert response.json()["items"] == []
    follow_up = client.get("/api/v1/catalog/products", params={"q": "filtro"})
    assert follow_up.status_code == 200
    assert follow_up.json()["items"]


def test_booking_is_idempotent() -> None:
    payload = {
        "customer_name": "Ana López",
        "phone": "+50499990000",
        "service_code": "DIAGNOSTICO",
        "requested_date": "2026-08-20",
        "vehicle": {"make": "Ford", "model": "Escape", "year": 2018},
    }
    headers = {"Idempotency-Key": "booking-demo-1"}
    first = client.post("/api/v1/bookings", json=payload, headers=headers)
    second = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["booking_id"] == second.json()["booking_id"]


def test_event_endpoint_requires_valid_signature() -> None:
    body = b'{"event_type":"WORK_ORDER_CREATED","aggregate_id":"SO-0001","payload":{}}'
    invalid = client.post(
        "/api/v1/events",
        content=body,
        headers={"content-type": "application/json", "X-SmartDiag-Signature": "bad"},
    )
    assert invalid.status_code == 401

    signature = hmac.new(b"test-webhook-secret", body, hashlib.sha256).hexdigest()
    valid = client.post(
        "/api/v1/events",
        content=body,
        headers={"content-type": "application/json", "X-SmartDiag-Signature": signature},
    )
    assert valid.status_code == 202


def test_readiness_reports_configured_adapters_without_exposing_secrets(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://smartdiag:db-secret@postgres-platform/smartdiag")
    monkeypatch.setenv("REDIS_URL", "redis://:cache-secret@redis-platform:6379/0")
    monkeypatch.setenv("S3_ENDPOINT", "http://garage:3900")
    monkeypatch.setenv("S3_REGION", "garage")
    monkeypatch.setenv("S3_ACCESS_KEY", "GK0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("S3_SECRET_KEY", "storage-secret")
    monkeypatch.setenv("S3_BUCKET", "smartdiag-evidence")
    monkeypatch.setenv("FRAPPE_API_KEY", "frappe-key")
    monkeypatch.setenv("FRAPPE_API_SECRET", "frappe-secret")
    monkeypatch.setenv("INTERNAL_API_KEY", "internal-secret")

    response = TestClient(create_app(testing=True)).get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": "configured",
            "cache": "configured",
            "object_storage": "configured",
            "frappe": "configured",
            "security": "configured",
        },
    }
    serialized = response.text.lower()
    assert "db-secret" not in serialized
    assert "cache-secret" not in serialized
    assert "storage-secret" not in serialized
    assert "frappe-secret" not in serialized


def test_production_readiness_fails_closed_when_required_adapters_are_missing(monkeypatch) -> None:
    for key in (
        "DATABASE_URL",
        "REDIS_URL",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "FRAPPE_API_KEY",
        "FRAPPE_API_SECRET",
        "INTERNAL_API_KEY",
        "WEBHOOK_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)

    response = TestClient(create_app()).get("/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "configuration_incomplete"
    assert payload["checks"]["database"] == "not_configured"
    assert payload["checks"]["cache"] == "not_configured"
    assert payload["checks"]["object_storage"] == "not_configured"
    assert payload["checks"]["frappe"] == "not_configured"
    assert payload["checks"]["security"] == "not_configured"
