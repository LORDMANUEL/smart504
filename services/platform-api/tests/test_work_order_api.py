from __future__ import annotations

import uuid
from io import BytesIO

from PIL import Image
from sqlalchemy import select

from app.models import ErpIntegrationJob
from app.config import get_settings
from app.services.erp_sync import process_erp_jobs
from app.services.work_orders import reconcile_work_order

STATUS_FLOW = [
    "CREATED",
    "QUOTED_BY_TECHNICIAN",
    "PENDING_CUSTOMER_APPROVAL",
    "PENDING_PARTS",
    "READY_TO_INVOICE",
    "INVOICED",
]


def test_work_order_evidence_is_persisted_and_printable(client, admin_headers) -> None:
    customer, vehicle = create_customer_vehicle(client, admin_headers)
    created = client.post(
        "/api/v1/operations/work-orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "vehicle_id": vehicle["id"],
            "title": "Diagnostico con evidencia",
            "concern": "Documentar visualmente las piezas revisadas.",
            "actor": "tecnico-demo",
        },
    ).json()
    buffer = BytesIO()
    Image.new("RGB", (32, 24), "red").save(buffer, format="JPEG")
    uploaded = client.post(
        f"/api/v1/operations/work-orders/{created['id']}/evidence",
        headers=admin_headers,
        data={"category": "DIAGNOSIS", "caption": "Pastilla delantera", "actor": "tecnico-demo"},
        files={"file": ("pieza.jpg", buffer.getvalue(), "image/jpeg")},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["caption"] == "Pastilla delantera"
    assert uploaded.json()["media_url"].endswith("/content")
    assert "storage_key" not in uploaded.json()
    assert client.get(uploaded.json()["media_url"]).status_code == 401
    protected_image = client.get(uploaded.json()["media_url"], headers=admin_headers)
    assert protected_image.status_code == 200
    assert protected_image.headers["cache-control"] == "private, no-store"
    listed = client.get(
        f"/api/v1/operations/work-orders/{created['id']}/evidence", headers=admin_headers
    )
    assert len(listed.json()) == 1
    assert "storage_key" not in listed.json()[0]
    diagnosis = client.get(
        f"/api/v1/operations/finance/work-orders/{created['id']}/documents/diagnosis.pdf",
        headers=admin_headers,
    )
    assert diagnosis.status_code == 200
    assert diagnosis.content.startswith(b"%PDF-")
    picking = client.get(
        f"/api/v1/operations/finance/work-orders/{created['id']}/warehouse-documents/picking-ticket.pdf",
        headers=admin_headers,
    )
    assert picking.status_code == 200
    assert picking.content.startswith(b"%PDF-")


def test_work_order_evidence_rejects_unsafe_pixel_dimensions(client, admin_headers) -> None:
    customer, vehicle = create_customer_vehicle(client, admin_headers)
    created = client.post(
        "/api/v1/operations/work-orders",
        headers=admin_headers,
        json={
            "customer_id": customer["id"],
            "vehicle_id": vehicle["id"],
            "title": "Diagnostico dimensional",
            "concern": "Rechazar imagenes comprimidas con dimensiones abusivas.",
            "actor": "tecnico-demo",
        },
    ).json()
    buffer = BytesIO()
    Image.new("RGB", (12001, 2), "red").save(buffer, format="PNG")
    response = client.post(
        f"/api/v1/operations/work-orders/{created['id']}/evidence",
        headers=admin_headers,
        data={"category": "DIAGNOSIS", "caption": "Imagen insegura", "actor": "tecnico-demo"},
        files={"file": ("pieza.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 422
    assert "dimensiones" in response.json()["detail"]


def create_customer_vehicle(client, headers):
    suffix = uuid.uuid4().hex[:8]
    customer = client.post(
        "/api/v1/operations/customers",
        headers=headers,
        json={
            "full_name": f"Cliente {suffix}",
            "phone": f"+504 99{suffix[:6]}",
            "email": f"{suffix}@example.com",
        },
    ).json()
    vehicle = client.post(
        "/api/v1/operations/vehicles",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "vin": f"VIN-{suffix}",
            "plate": f"P{suffix[:5]}",
            "make": "Ford",
            "model": "Escape",
            "model_year": 2020,
            "mileage_km": 86000,
        },
    ).json()
    return customer, vehicle


def create_ot(client, headers):
    customer, vehicle = create_customer_vehicle(client, headers)
    response = client.post(
        "/api/v1/operations/work-orders",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "vehicle_id": vehicle["id"],
            "title": "Diagnóstico de transmisión",
            "concern": "El vehículo presenta golpe al cambiar de segunda a tercera.",
            "assigned_technicians": ["Técnico A"],
            "bay_code": "B-01",
            "actor": "asesor@smartdiag504.com",
        },
    )
    assert response.status_code == 201
    return response.json()


def move(client, headers, ot_id, status, key, invoice=None):
    response = client.post(
        f"/api/v1/operations/work-orders/{ot_id}/transitions",
        headers=headers,
        json={
            "to_status": status,
            "actor": "tecnico@smartdiag504.com",
            "reason": f"Mover a {status}",
            "invoice_reference": invoice,
            "idempotency_key": key,
        },
    )
    return response


def test_board_has_exact_six_columns_in_required_order(client, admin_headers) -> None:
    create_ot(client, admin_headers)
    response = client.get("/api/v1/operations/work-orders/board", headers=admin_headers)
    assert response.status_code == 200
    board = response.json()
    assert [column["status"] for column in board] == STATUS_FLOW
    assert [column["label"] for column in board] == [
        "OT creada",
        "OT cotizada por técnico",
        "OT pendiente aprobación cliente",
        "OT pendiente de repuestos",
        "OT finalizada para facturar",
        "OT facturada",
    ]


def test_ready_to_invoice_requires_check_in_stopped_timer_and_quality(
    client, admin_headers
) -> None:
    work_order = create_ot(client, admin_headers)
    assert move(client, admin_headers, work_order["id"], "QUOTED_BY_TECHNICIAN", "gate-quoted").status_code == 200
    assert move(client, admin_headers, work_order["id"], "PENDING_CUSTOMER_APPROVAL", "gate-approval").status_code == 200

    blocked = move(client, admin_headers, work_order["id"], "READY_TO_INVOICE", "gate-blocked")
    assert blocked.status_code == 409
    assert "ingreso 360" in blocked.json()["detail"]

    check_in = client.post(f"/api/v1/operations/work-orders/{work_order['id']}/check-in",
        headers=admin_headers, json={"mileage_km": 86040, "fuel_percent": 55,
        "accessories": ["Llave", "Llanta de repuesto"], "exterior_notes": "Rayón previo trasero",
        "customer_name": "Cliente de prueba", "customer_accepted": True, "actor": "recepcion"})
    assert check_in.status_code == 200
    assert client.post(f"/api/v1/operations/work-orders/{work_order['id']}/timer",
        headers=admin_headers, json={"action": "START", "note": "Diagnóstico", "actor": "tecnico"}).status_code == 200
    still_running = move(client, admin_headers, work_order["id"], "READY_TO_INVOICE", "gate-running")
    assert still_running.status_code == 409
    assert "cronómetro detenido" in still_running.json()["detail"]
    stopped = client.post(f"/api/v1/operations/work-orders/{work_order['id']}/timer",
        headers=admin_headers, json={"action": "STOP", "note": "Trabajo terminado", "actor": "tecnico"})
    assert stopped.status_code == 200
    quality = client.post(f"/api/v1/operations/work-orders/{work_order['id']}/quality",
        headers=admin_headers, json={"checklist": {"frenos": True, "niveles": True, "limpieza": True},
        "road_test_required": True, "road_test_result": "PASS", "notes": "Sin novedad",
        "result": "PASS", "actor": "supervisor-calidad"})
    assert quality.status_code == 200
    completed = move(client, admin_headers, work_order["id"], "READY_TO_INVOICE", "gate-complete")
    assert completed.status_code == 200


def test_new_work_order_is_a_pending_erp_projection(client, admin_headers, db) -> None:
    work_order = create_ot(client, admin_headers)
    assert work_order["erp_sync_status"] == "PENDING"
    job = db.scalar(
        select(ErpIntegrationJob).where(
            ErpIntegrationJob.aggregate_type == "WORK_ORDER",
            ErpIntegrationJob.aggregate_id == work_order["id"],
        )
    )
    assert job is not None
    assert job.operation == "UPSERT_SERVICE_ORDER"
    assert job.status == "PENDING"
    assert job.payload_json["work_order_number"] == work_order["number"]


def test_erp_worker_marks_projection_synced_only_with_erp_reference(
    client, admin_headers, db
) -> None:
    work_order = create_ot(client, admin_headers)

    class RecordingErpClient:
        def __init__(self) -> None:
            self.commands = []

        def apply_integration_command(self, *, operation, payload):
            self.commands.append((operation, payload))
            return {"name": "SVC-ORD-2026-00042"}

    fake = RecordingErpClient()
    result = process_erp_jobs(db, get_settings(), limit=100, client=fake)
    assert result["synced"] >= 1
    refreshed = client.get(
        f"/api/v1/operations/work-orders/{work_order['id']}", headers=admin_headers
    ).json()
    assert refreshed["erp_sync_status"] == "SYNCED"
    assert refreshed["erpnext_service_order_id"] == "SVC-ORD-2026-00042"
    command = next(
        payload for operation, payload in fake.commands
        if operation == "UPSERT_SERVICE_ORDER"
        and payload["work_order_number"] == work_order["number"]
    )
    assert command["vin"]
    assert command["customer_name"]
    assert command["company"]


def test_technical_edit_requeues_complete_service_order_projection(
    client, admin_headers, db
) -> None:
    work_order = create_ot(client, admin_headers)

    class RecordingErpClient:
        def __init__(self) -> None:
            self.commands = []

        def apply_integration_command(self, *, operation, payload):
            self.commands.append((operation, payload))
            return {"name": "SVC-ORD-EDIT-0001"}

    fake = RecordingErpClient()
    process_erp_jobs(db, get_settings(), limit=100, client=fake)
    edited = client.patch(
        f"/api/v1/operations/work-orders/{work_order['id']}",
        headers=admin_headers,
        json={"diagnosis": "Falla confirmada en solenoide de cambio.", "bay_code": "B-03"},
    )
    assert edited.status_code == 200
    assert edited.json()["erp_sync_status"] == "PENDING"
    process_erp_jobs(db, get_settings(), limit=100, client=fake)
    payload = fake.commands[-1][1]
    assert payload["diagnosis"] == "Falla confirmada en solenoide de cambio."
    assert payload["bay_code"] == "B-03"
    assert payload["assigned_technicians"] == ["Técnico A"]
    assert "parts_required" in payload
    assert "labor_entries" in payload
    assert "evidence" in payload


def test_reconciliation_refreshes_local_projection_from_authoritative_erp(
    client, admin_headers, db
) -> None:
    work_order = create_ot(client, admin_headers)

    class AuthoritativeErpClient:
        def get_service_order_by_external_reference(self, external_reference):
            assert external_reference == work_order["number"]
            return {
                "name": "SVC-ORD-AUTH-0001",
                "title": "Título controlado en ERP",
                "preference_note": "Solicitud conciliada",
                "sd_workflow_state": "QUOTED_BY_TECHNICIAN",
                "sd_platform_diagnosis": "Diagnóstico conciliado desde ERP",
                "sd_platform_assigned_technicians": "Técnico ERP",
                "sd_platform_bay_code": "B-09",
                "sd_platform_parts_json": '[{"sku":"ERP-PART-1","quantity":1}]',
                "modified": "2026-08-21 01:55:00.000000",
            }

    reconciled = reconcile_work_order(db, work_order["id"], client=AuthoritativeErpClient())
    assert reconciled.status == "QUOTED_BY_TECHNICIAN"
    assert reconciled.title == "Título controlado en ERP"
    assert reconciled.diagnosis == "Diagnóstico conciliado desde ERP"
    assert reconciled.assigned_technicians == ["Técnico ERP"]
    assert reconciled.parts_required[0]["sku"] == "ERP-PART-1"
    assert reconciled.erpnext_service_order_id == "SVC-ORD-AUTH-0001"
    assert reconciled.erp_sync_status == "SYNCED"


def test_invoice_transition_requires_real_reference_and_is_idempotent(
    client, admin_headers
) -> None:
    ot = create_ot(client, admin_headers)
    assert client.post(f"/api/v1/operations/work-orders/{ot['id']}/check-in",
        headers=admin_headers, json={"mileage_km": 1000, "fuel_percent": 50,
        "accessories": [], "exterior_notes": "Sin novedad", "customer_name": "Cliente",
        "customer_accepted": True, "actor": "recepcion"}).status_code == 200
    assert client.post(f"/api/v1/operations/work-orders/{ot['id']}/quality",
        headers=admin_headers, json={"checklist": {"revision": True},
        "road_test_required": False, "road_test_result": "NOT_REQUIRED", "notes": "Aprobado",
        "result": "PASS", "actor": "supervisor"}).status_code == 200
    for index, status in enumerate(STATUS_FLOW[1:-1], start=1):
        response = move(client, admin_headers, ot["id"], status, f"step-{index}")
        assert response.status_code == 200

    rejected = move(client, admin_headers, ot["id"], "INVOICED", "invoice-no-ref")
    assert rejected.status_code == 409
    assert "invoice_reference" in rejected.json()["detail"]

    accepted = move(
        client,
        admin_headers,
        ot["id"],
        "INVOICED",
        "invoice-with-ref",
        "ACC-SINV-2026-00001",
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "INVOICED"
    event_count = len(accepted.json()["events"])

    duplicate = move(
        client,
        admin_headers,
        ot["id"],
        "INVOICED",
        "invoice-with-ref",
        "ACC-SINV-2026-00001",
    )
    assert duplicate.status_code == 200
    assert len(duplicate.json()["events"]) == event_count


def test_invalid_status_skip_is_rejected(client, admin_headers) -> None:
    ot = create_ot(client, admin_headers)
    response = move(client, admin_headers, ot["id"], "READY_TO_INVOICE", "skip-1")
    assert response.status_code == 409


def test_technician_can_request_catalog_part_from_work_order(client, admin_headers) -> None:
    ot = create_ot(client, admin_headers)
    product = client.post(
        "/api/v1/admin/catalog/products",
        headers=admin_headers,
        json={
            "sku": f"REQ-{uuid.uuid4().hex[:8]}",
            "name": "Filtro solicitado desde OT",
            "price": "450.00",
            "stock_qty": "3",
            "compatibility_notes": "Validar por VIN",
        },
    ).json()

    requested = client.post(
        f"/api/v1/operations/work-orders/{ot['id']}/part-requests",
        headers=admin_headers,
        json={
            "product_id": product["id"],
            "quantity": 2,
            "note": "Confirmar compatibilidad antes de entregar",
            "actor": "tecnico-demo",
        },
    )
    assert requested.status_code == 201
    payload = requested.json()
    assert payload["parts_required"][-1]["sku"] == product["sku"]
    assert payload["parts_required"][-1]["quantity"] == 2
    assert payload["events"][-1]["event_type"] == "PART_REQUESTED"

    part_request = payload["parts_required"][-1]
    delivered = client.patch(
        f"/api/v1/operations/work-orders/{ot['id']}/part-requests/"
        f"{part_request['request_id']}/delivery",
        headers=admin_headers,
        json={
            "actor": "bodega-demo",
            "location": "B-03-01",
        },
    )
    assert delivered.status_code == 200
    delivered_payload = delivered.json()
    assert delivered_payload["parts_required"][-1]["status"] == "DELIVERED"
    assert delivered_payload["parts_required"][-1]["location"] == "B-03-01"
    assert delivered_payload["events"][-1]["event_type"] == "PART_DELIVERED"

    heatmap = client.get("/api/v1/operations/flow-events/heatmap", headers=admin_headers).json()
    assert any(
        cell["module"] == "TECHNICIAN" and cell["action"] == "PART_REQUESTED" for cell in heatmap
    )
    assert any(
        cell["module"] == "WAREHOUSE" and cell["action"] == "PART_DELIVERED" for cell in heatmap
    )
