from fastapi.testclient import TestClient

from app.main import app


def test_demo_catalog_has_three_vehicles_five_labor_and_nine_parts() -> None:
    response = TestClient(app).get("/api/v1/demo/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["vehicles"]) == 3
    assert len(payload["labor"]) == 5
    assert len(payload["parts"]) == 9
    assert {item["model"] for item in payload["vehicles"]} == {"Escape", "F-150", "Civic"}
    assert all("cost" not in item for item in payload["parts"])


def test_demo_warehouse_requires_admin_token() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/demo/warehouse").status_code == 401
    response = client.get(
        "/api/v1/demo/warehouse", headers={"X-Admin-Token": "test-admin-token"}
    )
    assert response.status_code == 200
    assert all("cost" in item and "location" in item for item in response.json()["parts"])
