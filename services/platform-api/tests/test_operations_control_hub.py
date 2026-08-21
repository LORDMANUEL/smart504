from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select

from app.models import Branch, CatalogProduct, Customer, StoreOrder, StoreOrderItem, Vehicle


def _seed_order(db) -> tuple[CatalogProduct, StoreOrder, Vehicle]:
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        full_name="Cliente Operaciones",
        phone=f"99{suffix[:6]}",
        email=f"ops-{suffix}@example.com",
    )
    db.add(customer)
    db.flush()
    vehicle = Vehicle(
        customer_id=customer.id,
        vin=f"VINOPS{suffix.upper()}",
        make="Ford",
        model="Escape",
        model_year=2020,
    )
    product = CatalogProduct(
        sku=f"OPS-{suffix}",
        slug=f"ops-{suffix}",
        name="Filtro de prueba operativa",
        price=Decimal("350.00"),
        stock_qty=Decimal("10.000"),
    )
    db.add_all([vehicle, product])
    db.flush()
    branch_id = db.scalar(select(Branch.id).where(Branch.code == "MAIN"))
    order = StoreOrder(
        branch_id=branch_id,
        order_number=f"WEB-OPS-{suffix}",
        customer_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        vehicle_vin=vehicle.vin,
        subtotal=Decimal("350.00"),
        idempotency_key=f"ops-order-{suffix}",
        customer_id=customer.id,
        items=[
            StoreOrderItem(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                quantity=1,
                unit_price=Decimal("350.00"),
                line_total=Decimal("350.00"),
            )
        ],
    )
    db.add(order)
    db.commit()
    return product, order, vehicle


def test_public_lead_is_captured_and_moves_through_kanban(client, admin_headers) -> None:
    suffix = uuid.uuid4().hex[:8]
    created = client.post(
        "/api/v1/leads",
        json={
            "full_name": "Interesado Demo",
            "phone": f"98{suffix[:6]}",
            "interest": "Necesita diagnóstico y desea hablar con un asesor",
            "vehicle_summary": "Honda Civic 2008",
            "source": "AI_CHAT",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "NEW"

    updated = client.patch(
        f"/api/v1/operations/control/leads/{created.json()['id']}",
        headers=admin_headers,
        json={
            "status": "ADVISOR",
            "assigned_to": "María - asesora",
            "notes": "Contactar por WhatsApp",
            "actor": "supervisor-demo",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["assigned_to"] == "María - asesora"


def test_crm_activity_and_survey_are_auditable(client, admin_headers) -> None:
    created = client.post("/api/v1/operations/control/leads", headers=admin_headers, json={
        "full_name": "Prospecto Taller", "phone": "99887766", "interest": "Cotizacion de frenos",
        "vehicle_summary": "Ford Escape 2020", "source": "WALK_IN",
    })
    assert created.status_code == 201
    lead_id = created.json()["id"]
    assert client.post(f"/api/v1/operations/control/leads/{lead_id}/activities", headers=admin_headers,
        json={"activity_type": "WHATSAPP", "content": "Se envio propuesta.", "outcome": "Interesado", "actor": "asesor-demo"}).status_code == 201
    assert client.post(f"/api/v1/operations/control/leads/{lead_id}/surveys", headers=admin_headers,
        json={"survey_name": "Satisfaccion", "answers": {"calificacion": 5}, "actor": "asesor-demo"}).status_code == 201
    timeline = client.get(f"/api/v1/operations/control/leads/{lead_id}/activities", headers=admin_headers)
    assert {item["action"] for item in timeline.json()} >= {"ACTIVITY_WHATSAPP", "SURVEY_RECORDED"}


def test_reservation_freight_return_and_vin_history_are_auditable(
    client, admin_headers, db
) -> None:
    product, order, vehicle = _seed_order(db)
    overview = client.get("/api/v1/operations/control/overview", headers=admin_headers)
    assert overview.status_code == 200
    warehouses = overview.json()["warehouses"]
    stock = next(item for item in warehouses if item["warehouse_type"] == "STOCK")

    reservation = client.post(
        "/api/v1/operations/control/reservations",
        headers=admin_headers,
        json={
            "product_id": product.id,
            "warehouse_id": stock["id"],
            "store_order_id": order.id,
            "quantity": "1.000",
            "actor": "bodega-demo",
        },
    )
    assert reservation.status_code == 201
    assert reservation.json()["status"] == "RESERVED"

    shipment = client.post(
        "/api/v1/operations/control/shipments",
        headers=admin_headers,
        json={
            "store_order_id": order.id,
            "from_warehouse_id": stock["id"],
            "carrier": "Mensajería Demo",
            "recipient_name": order.customer_name,
            "recipient_phone": order.phone,
            "actor": "caja-demo",
        },
    )
    assert shipment.status_code == 201
    shipped = client.patch(
        f"/api/v1/operations/control/shipments/{shipment.json()['id']}",
        headers=admin_headers,
        json={
            "status": "SHIPPED",
            "tracking_number": "GUIA-DEMO-001",
            "guide_image_url": "https://example.com/guias/demo-001.jpg",
            "actor": "caja-demo",
        },
    )
    assert shipped.status_code == 200
    assert shipped.json()["status"] == "SHIPPED"

    quality = client.post(
        "/api/v1/operations/control/quality-cases",
        headers=admin_headers,
        json={
            "case_type": "RETURN",
            "customer_id": vehicle.customer_id,
            "vehicle_id": vehicle.id,
            "store_order_id": order.id,
            "description": "Cliente solicita revisión y devolución documentada del repuesto.",
            "actor": "calidad-demo",
        },
    )
    assert quality.status_code == 201
    resolved = client.patch(
        f"/api/v1/operations/control/quality-cases/{quality.json()['id']}",
        headers=admin_headers,
        json={
            "status": "RESOLVED",
            "resolution": "Repuesto recibido y enviado a bodega de devoluciones.",
            "actor": "calidad-demo",
        },
    )
    assert resolved.status_code == 200

    history = client.get(
        f"/api/v1/operations/control/vehicle-history?vin={vehicle.vin}",
        headers=admin_headers,
    )
    assert history.status_code == 200
    assert any(item["event_type"] == "RETURN" for item in history.json())


def test_reservation_rejects_ambiguous_owner(client, admin_headers) -> None:
    response = client.post(
        "/api/v1/operations/control/reservations",
        headers=admin_headers,
        json={
            "product_id": str(uuid.uuid4()),
            "warehouse_id": str(uuid.uuid4()),
            "quantity": "1",
            "actor": "bodega-demo",
        },
    )
    assert response.status_code == 422


def test_fiscal_configuration_requires_accountant_confirmation_and_closes_previous(
    client, admin_headers
) -> None:
    overview = client.get("/api/v1/operations/control/overview", headers=admin_headers).json()
    branch_id = overview["branches"][0]["id"]

    def create_series(number: str, start: int) -> dict:
        response = client.post(
            "/api/v1/operations/control/management-documents",
            headers=admin_headers,
            json={
                "branch_id": branch_id,
                "document_type": "FISCAL_CONFIGURATION",
                "number": number,
                "status": "DRAFT",
                "metadata_json": {
                    "numbering_owner": "PREPRINTED",
                    "legal_name": "SmartDiag504 Demo, S. de R.L.",
                    "rtn": "08011999123456",
                    "document_kind": "FACTURA",
                    "range_start": start,
                    "range_end": start + 99,
                },
            },
        )
        assert response.status_code == 201
        return response.json()

    first = create_series("FACTURA TEST A", 1)
    rejected = client.patch(
        f"/api/v1/operations/control/management-documents/{first['id']}/status",
        headers=admin_headers,
        json={"status": "ACTIVE", "accountant_confirmed": False},
    )
    assert rejected.status_code == 422
    assert client.patch(
        f"/api/v1/operations/control/management-documents/{first['id']}/status",
        headers=admin_headers,
        json={"status": "ACTIVE", "accountant_confirmed": True, "note": "Validado"},
    ).status_code == 200

    second = create_series("FACTURA TEST B", 101)
    assert client.patch(
        f"/api/v1/operations/control/management-documents/{second['id']}/status",
        headers=admin_headers,
        json={"status": "ACTIVE", "accountant_confirmed": True},
    ).status_code == 200
    current = client.get("/api/v1/operations/control/overview", headers=admin_headers).json()
    states = {item["id"]: item["status"] for item in current["management_documents"]}
    assert states[first["id"]] == "EXPIRED"
    assert states[second["id"]] == "ACTIVE"
