from sqlalchemy import select

from app.models import FlowEvent


def test_reception_creates_confirmed_booking_from_kanban(client, admin_headers, db):
    response = client.post(
        "/api/v1/operations/bookings",
        headers=admin_headers,
        json={
            "full_name": "Cliente de mostrador",
            "phone": "+504 9999-0000",
            "email": "cliente@example.com",
            "vehicle_summary": "Ford Escape 2020 VIN 1FMCU0G6XLUA12545",
            "service_requested": "Diagnostico electronico",
            "preferred_date": "2026-08-20T09:00",
            "concern": "Revision preventiva creada desde el Kanban.",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "CONFIRMED"
    assert response.json()["source"] == "KANBAN"
    listed = client.get("/api/v1/operations/bookings", headers=admin_headers)
    assert any(item["id"] == response.json()["id"] for item in listed.json())
    event = db.scalar(select(FlowEvent).where(FlowEvent.item_reference == response.json()["id"]))
    assert event is not None
    assert event.action == "BOOKING_CREATED_FROM_KANBAN"


def test_technician_labor_catalog_exposes_only_controlled_sale_fields(client, admin_headers):
    response = client.get("/api/v1/operations/labor-catalog", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert {"code", "description", "hours", "price"} == set(response.json()[0])
    assert "cost" not in response.json()[0]
