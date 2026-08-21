from decimal import Decimal

from sqlalchemy import select

from app.config import get_settings
from app.models import Branch, CatalogProduct, Customer, ErpIntegrationJob, InventoryBalance, Quote, Vehicle, WarehouseLocation
from app.services.erp_sync import process_erp_jobs


def create_work_order(client, admin_headers, db) -> dict:
    customer = Customer(full_name="Cliente Caja", phone="99990001", email="caja@example.com")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(
        customer_id=customer.id,
        make="Ford",
        model="Escape",
        model_year=2020,
        plate="HCAJA01",
    )
    db.add(vehicle)
    db.commit()
    response = client.post(
        "/api/v1/operations/work-orders",
        headers=admin_headers,
        json={
            "customer_id": customer.id,
            "vehicle_id": vehicle.id,
            "title": "Servicio para cobro",
            "concern": "Preparar cotización y registrar pago completo.",
            "actor": "asesor-demo",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_quote_approval_card_payment_and_cash_close(client, admin_headers, db) -> None:
    work_order = create_work_order(client, admin_headers, db)
    quote = client.post(
        "/api/v1/operations/finance/quotes",
        headers=admin_headers,
        json={
            "work_order_id": work_order["id"],
            "created_by": "asesor-demo",
            "discount": "50.00",
            "tax": "0.00",
            "lines": [
                {
                    "line_type": "LABOR",
                    "code": "MO-DIAG",
                    "description": "Diagnóstico electrónico",
                    "quantity": "1",
                    "unit_price": "1200.00",
                    "unit_cost": "500.00",
                },
                {
                    "line_type": "PART",
                    "code": "ESC-FIL-2020",
                    "description": "Filtro de aceite",
                    "quantity": "1",
                    "unit_price": "285.00",
                    "unit_cost": "180.00",
                },
            ],
        },
    )
    assert quote.status_code == 201
    assert Decimal(quote.json()["total"]) == Decimal("1435.00")
    quote_id = quote.json()["id"]
    for target in ("SENT", "APPROVED"):
        response = client.patch(
            f"/api/v1/operations/finance/quotes/{quote_id}/status",
            headers=admin_headers,
            json={"status": target, "actor": "asesor-demo"},
        )
        assert response.status_code == 200

    opened = client.post(
        "/api/v1/operations/finance/cash-sessions",
        headers=admin_headers,
        json={"opening_balance": "1000.00", "actor": "cajero-demo"},
    )
    assert opened.status_code == 201
    session_id = opened.json()["id"]

    payment = client.post(
        f"/api/v1/operations/finance/cash-sessions/{session_id}/payments",
        headers=admin_headers,
        json={
            "work_order_id": work_order["id"],
            "quote_id": quote_id,
            "method": "CARD",
            "amount": "1435.00",
            "reference": "POS-APROB-504",
            "actor": "cajero-demo",
        },
    )
    assert payment.status_code == 201
    assert payment.json()["method"] == "CARD"

    summary = client.get("/api/v1/operations/finance/cash-summary", headers=admin_headers).json()
    assert Decimal(summary["totals_by_method"]["CARD"]) == Decimal("1435.00")

    closed = client.post(
        f"/api/v1/operations/finance/cash-sessions/{session_id}/close",
        headers=admin_headers,
        json={"counted_cash": "1000.00", "actor": "cajero-demo"},
    )
    assert closed.status_code == 200
    assert Decimal(closed.json()["difference"]) == Decimal("0.00")


def test_quote_is_an_erp_projection_and_keeps_returned_reference(
    client, admin_headers, db
) -> None:
    work_order = create_work_order(client, admin_headers, db)
    quote = client.post(
        "/api/v1/operations/finance/quotes",
        headers=admin_headers,
        json={
            "work_order_id": work_order["id"],
            "created_by": "asesor-demo",
            "lines": [
                {
                    "line_type": "LABOR",
                    "code": "MO-ERP-TEST",
                    "description": "Diagnostico sincronizado",
                    "quantity": "1",
                    "unit_price": "800",
                    "unit_cost": "300",
                }
            ],
        },
    ).json()
    job = db.scalar(
        select(ErpIntegrationJob).where(
            ErpIntegrationJob.aggregate_type == "QUOTE",
            ErpIntegrationJob.aggregate_id == quote["id"],
        )
    )
    assert job is not None
    assert job.operation == "UPSERT_SERVICE_QUOTATION"

    class RecordingErpClient:
        def __init__(self) -> None:
            self.commands = []

        def apply_integration_command(self, *, operation, payload):
            self.commands.append((operation, payload))
            return {"name": "SQ-2026-00042" if operation == "UPSERT_SERVICE_QUOTATION" else "SO-TEST"}

    fake = RecordingErpClient()
    process_erp_jobs(db, get_settings(), limit=100, client=fake)
    persisted = db.get(Quote, quote["id"])
    assert persisted.erp_sync_status == "SYNCED"
    assert persisted.erpnext_quotation_id == "SQ-2026-00042"
    command = next(
        payload
        for operation, payload in fake.commands
        if operation == "UPSERT_SERVICE_QUOTATION" and payload["quote_number"] == quote["number"]
    )
    assert command["quote_number"] == quote["number"]
    assert command["items"][0]["item_code"] == "MO-ERP-TEST"


def test_prequote_searches_vin_and_converts_only_after_approval(client, admin_headers, db) -> None:
    work_order = create_work_order(client, admin_headers, db)
    from app.models import WorkOrder
    persisted = db.get(WorkOrder, work_order["id"])
    context = client.get(
        f"/api/v1/operations/finance/quote-context?query={persisted.vehicle.vin or persisted.vehicle.plate}",
        headers=admin_headers,
    )
    assert context.status_code == 200
    assert persisted.vehicle_id in {item["vehicle_id"] for item in context.json()}
    quote = client.post("/api/v1/operations/finance/quotes", headers=admin_headers, json={
        "customer_id": persisted.customer_id, "vehicle_id": persisted.vehicle_id,
        "created_by": "asesor-demo", "notes": "Precotizacion por VIN", "discount": "0", "tax": "0",
        "lines": [{"line_type": "LABOR", "code": "MO-VIN", "description": "Diagnostico por VIN",
                   "quantity": "1", "unit_price": "650", "unit_cost": "250"}],
    })
    assert quote.status_code == 201
    assert quote.json()["work_order_id"] is None
    blocked = client.post(f"/api/v1/operations/finance/quotes/{quote.json()['id']}/convert-to-work-order",
                          headers=admin_headers, json={"actor": "asesor-demo"})
    assert blocked.status_code == 409
    for target in ("SENT", "APPROVED"):
        assert client.patch(f"/api/v1/operations/finance/quotes/{quote.json()['id']}/status",
                            headers=admin_headers, json={"status": target, "actor": "asesor-demo"}).status_code == 200
    converted = client.post(f"/api/v1/operations/finance/quotes/{quote.json()['id']}/convert-to-work-order",
                            headers=admin_headers, json={"actor": "asesor-demo"})
    assert converted.status_code == 200
    assert converted.json()["work_order_id"]
    assert converted.json()["converted_work_order_id"] == converted.json()["work_order_id"]


def test_quote_is_assembled_from_ot_and_tracks_line_approval(client, admin_headers, db) -> None:
    work_order = create_work_order(client, admin_headers, db)
    updated = client.patch(
        f"/api/v1/operations/work-orders/{work_order['id']}",
        headers=admin_headers,
        json={
            "technician_quote": {
                "labor_description": "Diagnóstico electrónico y revisión",
                "labor_total": "850.00",
            },
            "parts_required": [
                {
                    "request_id": "part-demo-001",
                    "sku": "FIL-ESC-2020",
                    "name": "Filtro de aceite",
                    "quantity": 1,
                    "unit_price": "320.00",
                    "status": "REQUESTED",
                }
            ],
        },
    )
    assert updated.status_code == 200

    quote = client.post(
        f"/api/v1/operations/finance/quotes/from-work-order/{work_order['id']}",
        headers=admin_headers,
        json={"actor": "asesor-demo"},
    )
    assert quote.status_code == 201
    assert len(quote.json()["lines"]) == 2
    assert all(line["approval_status"] == "PENDING" for line in quote.json()["lines"])

    line = quote.json()["lines"][0]
    approval = client.patch(
        f"/api/v1/operations/finance/quotes/{quote.json()['id']}/lines/{line['id']}",
        headers=admin_headers,
        json={"approval_status": "APPROVED", "actor": "cliente-demo"},
    )
    assert approval.status_code == 200
    statuses = {item["id"]: item["approval_status"] for item in approval.json()["lines"]}
    assert statuses[line["id"]] == "APPROVED"


def test_cashier_documents_are_real_pdf_files(client, admin_headers, db) -> None:
    work_order = create_work_order(client, admin_headers, db)
    quote = client.post(
        "/api/v1/operations/finance/quotes",
        headers=admin_headers,
        json={
            "work_order_id": work_order["id"],
            "created_by": "cajero-demo",
            "discount": "0.00",
            "tax": "0.00",
            "lines": [
                {
                    "line_type": "LABOR",
                    "code": "MO-DOC",
                    "description": "Servicio documentado",
                    "quantity": "1",
                    "unit_price": "500.00",
                    "unit_cost": "250.00",
                }
            ],
        },
    ).json()

    quote_html = client.get(
        f"/api/v1/operations/finance/quotes/{quote['id']}.html", headers=admin_headers
    )
    quote_pdf = client.get(
        f"/api/v1/operations/finance/quotes/{quote['id']}.pdf", headers=admin_headers
    )
    assert quote_html.status_code == 200
    assert quote["number"] in quote_html.text
    assert quote_pdf.content.startswith(b"%PDF-")

    for kind in ("invoice", "warranty", "exit-pass"):
        document = client.get(
            f"/api/v1/operations/finance/work-orders/{work_order['id']}/documents/{kind}.pdf",
            headers=admin_headers,
        )
        assert document.status_code == 200
        assert document.content.startswith(b"%PDF-")


def test_counter_only_exposes_sellable_warehouse_inventory_and_records_missing_demand(
    client, admin_headers, db
) -> None:
    branch = Branch(code="TST", name="Sucursal prueba")
    db.add(branch)
    db.flush()
    warehouse = WarehouseLocation(
        organization_id=branch.organization_id,
        branch_id=branch.id,
        code="TST-STOCK",
        name="Bodega mostrador",
        warehouse_type="STOCK",
    )
    sellable = CatalogProduct(
        sku="TST-SELL-001", slug="tst-sell-001", name="Filtro vendible",
        price=Decimal("350.00"), purchase_cost=Decimal("200.00"), stock_qty=Decimal("99"),
    )
    no_price = CatalogProduct(
        sku="TST-NOPRICE", slug="tst-noprice", name="Pieza sin precio",
        price=Decimal("0.00"), purchase_cost=Decimal("100.00"), stock_qty=Decimal("8"),
    )
    no_balance = CatalogProduct(
        sku="TST-NOBAL", slug="tst-nobal", name="Pieza sin saldo de bodega",
        price=Decimal("500.00"), purchase_cost=Decimal("250.00"), stock_qty=Decimal("50"),
    )
    db.add_all([warehouse, sellable, no_price, no_balance])
    db.flush()
    db.add_all([
        InventoryBalance(
            organization_id=branch.organization_id, warehouse_id=warehouse.id,
            product_id=sellable.id, quantity_on_hand=Decimal("3"), quantity_reserved=Decimal("1"),
        ),
        InventoryBalance(
            organization_id=branch.organization_id, warehouse_id=warehouse.id,
            product_id=no_price.id, quantity_on_hand=Decimal("8"), quantity_reserved=Decimal("0"),
        ),
    ])
    db.commit()

    context = client.get(
        f"/api/v1/operations/finance/counter-sales/context?warehouse_id={warehouse.id}",
        headers=admin_headers,
    )
    assert context.status_code == 200
    products = {item["sku"]: item for item in context.json()["products"]}
    assert products["TST-SELL-001"]["warehouse_stock"][warehouse.id] == "2.000"
    assert products["TST-SELL-001"]["sellable"] is True
    assert products["TST-NOPRICE"]["sellable"] is False
    assert "SIN_PRECIO" in products["TST-NOPRICE"]["blocking_reasons"]
    assert products["TST-NOBAL"]["sellable"] is False
    assert "SIN_EXISTENCIA" in products["TST-NOBAL"]["blocking_reasons"]

    demand = client.post(
        "/api/v1/operations/finance/counter-item-requests",
        headers=admin_headers,
        json={
            "search_query": "sensor ABS Ford Escape",
            "customer_name": "Cliente interesado",
            "phone": "9999-5040",
            "vehicle_vin": "1FMCU0G6XLUA12545",
            "quantity": "2",
            "branch_id": branch.id,
            "warehouse_id": warehouse.id,
            "notes": "Cliente solicita llamada al conseguirlo",
        },
    )
    assert demand.status_code == 201
    assert demand.json()["status"] == "NEW"
    assert demand.json()["search_query"] == "sensor ABS Ford Escape"
    listed = client.get("/api/v1/operations/finance/counter-item-requests", headers=admin_headers)
    assert any(item["id"] == demand.json()["id"] for item in listed.json())
