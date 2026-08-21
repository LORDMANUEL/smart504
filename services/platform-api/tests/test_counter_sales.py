from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.models import Branch, CatalogProduct, InventoryBalance, InventoryMovement, WarehouseLocation


def seed_counter_inventory(db):
    suffix = uuid4().hex[:6].upper()
    branch = Branch(code=f"SPS-{suffix}", name="Mostrador SPS")
    db.add(branch)
    db.flush()
    warehouse = WarehouseLocation(
        branch_id=branch.id,
        code=f"SPS-{suffix}-STOCK",
        name="Bodega mostrador",
        warehouse_type="STOCK",
    )
    product = CatalogProduct(
        sku=f"MOST-FIL-{suffix}",
        slug=f"most-fil-{suffix.lower()}",
        name="Filtro de aceite mostrador",
        price=Decimal("320.00"),
        stock_qty=Decimal("8.000"),
        stock_status="IN_STOCK",
        active=True,
        purchase_cost=Decimal("200.00"),
        landed_cost_factor=Decimal("1.10"),
    )
    db.add_all([warehouse, product]); db.flush()
    db.add(InventoryBalance(organization_id=branch.organization_id, warehouse_id=warehouse.id, product_id=product.id, quantity_on_hand=Decimal("8.000"), quantity_reserved=Decimal("0")))
    db.commit()
    return branch, warehouse, product


def test_counter_sale_rejects_price_and_discount_below_landed_cost(client, admin_headers, db) -> None:
    branch, warehouse, product = seed_counter_inventory(db)
    opened = client.post(
        "/api/v1/operations/finance/cash-sessions",
        headers=admin_headers,
        json={"opening_balance": "0", "actor": "cajera-mostrador"},
    )
    session = opened.json() if opened.status_code == 201 else client.get(
        "/api/v1/operations/finance/cash-sessions/current", headers=admin_headers
    ).json()
    base = {
        "cash_session_id": session["id"], "branch_id": branch.id,
        "warehouse_id": warehouse.id, "customer_name": "Consumidor final",
        "discount": "0", "tax": "0", "method": "CASH", "actor": "cajera-mostrador",
    }
    below_price = client.post(
        "/api/v1/operations/finance/counter-sales", headers=admin_headers,
        json={**base, "items": [{"product_id": product.id, "quantity": "1", "unit_price": "219.99"}]},
    )
    assert below_price.status_code == 422
    assert "debe venir del catálogo" in below_price.json()["detail"].lower()

    below_after_discount = client.post(
        "/api/v1/operations/finance/counter-sales", headers=admin_headers,
        json={**base, "discount": "101", "items": [{"product_id": product.id, "quantity": "1", "unit_price": "320"}]},
    )
    assert below_after_discount.status_code == 422
    assert "descuento" in below_after_discount.json()["detail"].lower()
    closed = client.post(
        f"/api/v1/operations/finance/cash-sessions/{session['id']}/close",
        headers=admin_headers,
        json={"counted_cash": "0", "actor": "cajera-mostrador"},
    )
    assert closed.status_code == 200, closed.text


def test_counter_sale_payment_stock_receipt_and_return(client, admin_headers, db) -> None:
    branch, warehouse, product = seed_counter_inventory(db)
    opened = client.post(
        "/api/v1/operations/finance/cash-sessions",
        headers=admin_headers,
        json={"opening_balance": "500.00", "actor": "cajera-mostrador"},
    )
    assert opened.status_code == 201

    sale = client.post(
        "/api/v1/operations/finance/counter-sales",
        headers=admin_headers,
        json={
            "cash_session_id": opened.json()["id"],
            "branch_id": branch.id,
            "warehouse_id": warehouse.id,
            "customer_name": "Consumidor final",
            "phone": "99990000",
            "vehicle_vin": "1FMCU0G6XLUA12545",
            "discount": "20.00",
            "tax": "0.00",
            "method": "CARD",
            "reference": "POS-MOST-504",
            "actor": "cajera-mostrador",
            "items": [{"product_id": product.id, "quantity": "2", "unit_price": "320.00"}],
        },
    )
    assert sale.status_code == 201, sale.text
    body = sale.json()
    assert body["status"] == "COMPLETED"
    assert Decimal(body["total"]) == Decimal("620.00")
    assert body["payment"]["method"] == "CARD"
    assert body["invoice_number"].startswith("FAC-M-")

    db.expire_all()
    assert db.get(CatalogProduct, product.id).stock_qty == Decimal("6.000")
    balance = db.scalar(select(InventoryBalance).where(InventoryBalance.product_id == product.id))
    assert balance.quantity_on_hand == Decimal("6.000")
    assert db.scalar(select(InventoryMovement).where(InventoryMovement.reference == body["sale_number"]))

    receipt = client.get(
        f"/api/v1/operations/finance/counter-sales/{body['id']}.pdf",
        headers=admin_headers,
    )
    assert receipt.status_code == 200
    assert receipt.content.startswith(b"%PDF-")

    approval_request = client.post(
        f"/api/v1/operations/finance/counter-sales/{body['id']}/approval-requests",
        headers=admin_headers,
        json={
            "request_type": "RETURN",
            "reason": "Producto sin abrir devuelto por cliente",
            "method": "CARD",
            "reference": "REV-POS-MOST-504",
            "requested_by": "cajera-mostrador",
            "owner_email": "dueno@example.com",
            "items": [{"sale_item_id": body["items"][0]["id"], "quantity": "1"}],
        },
    )
    assert approval_request.status_code == 201, approval_request.text
    approval = approval_request.json()
    decision = client.post(
        f"/api/v1/public/approvals/{approval['token']}/decision",
        json={"decision": "APPROVED"},
    )
    assert decision.status_code == 200
    returned = client.post(
        f"/api/v1/operations/finance/counter-sales/{body['id']}/returns",
        headers=admin_headers,
        json={
            "approval_id": approval["id"],
            "reason": "Producto sin abrir devuelto por cliente",
            "method": "CARD",
            "reference": "REV-POS-MOST-504",
            "actor": "cajera-mostrador",
            "items": [{"sale_item_id": body["items"][0]["id"], "quantity": "1"}],
        },
    )
    assert returned.status_code == 201, returned.text
    assert returned.json()["status"] == "COMPLETED"
    assert Decimal(returned.json()["total"]) == Decimal("310.00")
    assert returned.json()["sale_status"] == "PARTIAL_RETURN"
    db.expire_all()
    assert db.get(CatalogProduct, product.id).stock_qty == Decimal("7.000")
    db.expire_all()
    assert db.scalar(select(InventoryBalance).where(InventoryBalance.product_id == product.id)).quantity_on_hand == Decimal("7.000")
    closed = client.post(
        f"/api/v1/operations/finance/cash-sessions/{opened.json()['id']}/close",
        headers=admin_headers,
        json={"counted_cash": "500.00", "actor": "cajera-mostrador"},
    )
    assert closed.status_code == 200


def test_counter_sale_rejects_closed_cash_and_insufficient_stock(client, admin_headers, db) -> None:
    branch, warehouse, product = seed_counter_inventory(db)
    payload = {
        "cash_session_id": "missing",
        "branch_id": branch.id,
        "warehouse_id": warehouse.id,
        "customer_name": "Consumidor final",
        "discount": "0",
        "tax": "0",
        "method": "CASH",
        "actor": "cajera-mostrador",
        "items": [{"product_id": product.id, "quantity": "20", "unit_price": "320.00"}],
    }
    missing_session = client.post(
        "/api/v1/operations/finance/counter-sales", headers=admin_headers, json=payload
    )
    assert missing_session.status_code == 409

    opened_response = client.post(
        "/api/v1/operations/finance/cash-sessions",
        headers=admin_headers,
        json={"opening_balance": "0", "actor": "cajera-mostrador"},
    )
    opened = (
        opened_response.json()
        if opened_response.status_code == 201
        else client.get(
            "/api/v1/operations/finance/cash-sessions/current", headers=admin_headers
        ).json()
    )
    payload["cash_session_id"] = opened["id"]
    no_stock = client.post(
        "/api/v1/operations/finance/counter-sales", headers=admin_headers, json=payload
    )
    assert no_stock.status_code == 409
    closed = client.post(
        f"/api/v1/operations/finance/cash-sessions/{opened['id']}/close",
        headers=admin_headers,
        json={"counted_cash": "0", "actor": "cajera-mostrador"},
    )
    assert closed.status_code == 200


def test_counter_fitment_returns_customer_vehicle_and_only_compatible_parts(client, admin_headers, db) -> None:
    from app.models import Customer, Vehicle

    customer = Customer(full_name="Ana Mostrador", phone="99992222")
    db.add(customer); db.flush()
    vehicle = Vehicle(customer_id=customer.id, vin="2HGFA16538H508504", plate="HAC2008", make="Honda", model="Civic", model_year=2008)
    compatible = CatalogProduct(sku="FIT-CIV-1", slug="fit-civ-1", name="Bujias Civic", price=Decimal("1320"), stock_qty=Decimal("6"), active=True, compatibility_notes="Honda Civic 2008")
    incompatible = CatalogProduct(sku="FIT-F150-1", slug="fit-f150-1", name="Filtro F150", price=Decimal("320"), stock_qty=Decimal("4"), active=True, compatibility_notes="Ford F-150 2020")
    db.add_all([vehicle, compatible, incompatible]); db.commit()

    response = client.get("/api/v1/operations/finance/counter-sales/fitment?vin=2hgfa16538h508504", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["vehicle"]["owner"] == "Ana Mostrador"
    returned_skus = {item["sku"] for item in response.json()["products"]}
    assert "FIT-CIV-1" in returned_skus
    assert "FIT-F150-1" not in returned_skus
