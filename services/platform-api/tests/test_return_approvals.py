from decimal import Decimal
from uuid import uuid4

from app.models import ApprovalRequest, Branch, CatalogProduct, InventoryBalance, RetailSale, WarehouseLocation


def seed_counter_inventory(db):
    suffix = uuid4().hex[:6].upper()
    branch = Branch(code=f"APR-{suffix}", name="Mostrador autorizaciones")
    db.add(branch)
    db.flush()
    warehouse = WarehouseLocation(
        branch_id=branch.id,
        code=f"APR-{suffix}-STOCK",
        name="Bodega autorizaciones",
        warehouse_type="STOCK",
    )
    product = CatalogProduct(
        sku=f"APR-FIL-{suffix}", slug=f"apr-fil-{suffix.lower()}",
        name="Filtro sujeto a autorización", price=Decimal("320.00"),
        stock_qty=Decimal("8.000"), stock_status="IN_STOCK", active=True,
        purchase_cost=Decimal("200.00"), landed_cost_factor=Decimal("1.10"),
    )
    db.add_all([warehouse, product]); db.flush()
    db.add(InventoryBalance(organization_id=branch.organization_id, warehouse_id=warehouse.id, product_id=product.id, quantity_on_hand=Decimal("8.000"), quantity_reserved=Decimal("0")))
    db.commit()
    return branch, warehouse, product


def _sale(client, headers, db):
    branch, warehouse, product = seed_counter_inventory(db)
    opened = client.post(
        "/api/v1/operations/finance/cash-sessions", headers=headers,
        json={"opening_balance": "500", "actor": "cajera-mostrador"},
    )
    session = opened.json() if opened.status_code == 201 else client.get(
        "/api/v1/operations/finance/cash-sessions/current", headers=headers
    ).json()
    response = client.post(
        "/api/v1/operations/finance/counter-sales", headers=headers,
        json={
            "cash_session_id": session["id"], "branch_id": branch.id,
            "warehouse_id": warehouse.id, "customer_name": "Consumidor final",
            "discount": "0", "tax": "0", "method": "CASH", "actor": "cajera-mostrador",
            "items": [{"product_id": product.id, "quantity": "1", "unit_price": "320"}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_return_requires_owner_link_approval_before_inventory_or_refund(client, admin_headers, db) -> None:
    sale = _sale(client, admin_headers, db)
    item_id = sale["items"][0]["id"]
    requested = client.post(
        f"/api/v1/operations/finance/counter-sales/{sale['id']}/approval-requests",
        headers=admin_headers,
        json={
            "request_type": "RETURN", "reason": "Cliente solicita devolver producto sin abrir",
            "method": "CASH", "requested_by": "cajera-mostrador",
            "owner_email": "dueno@example.com",
            "items": [{"sale_item_id": item_id, "quantity": "1"}],
        },
    )
    assert requested.status_code == 201, requested.text
    approval = requested.json()
    assert approval["status"] == "PENDING"
    assert approval["approval_url"].endswith(approval["token"])

    blocked = client.post(
        f"/api/v1/operations/finance/counter-sales/{sale['id']}/returns",
        headers=admin_headers,
        json={
            "approval_id": approval["id"], "reason": "Cliente solicita devolver producto sin abrir",
            "method": "CASH", "actor": "cajera-mostrador",
            "items": [{"sale_item_id": item_id, "quantity": "1"}],
        },
    )
    assert blocked.status_code == 409

    decision = client.post(
        f"/api/v1/public/approvals/{approval['token']}/decision",
        json={"decision": "APPROVED", "comment": "Autorizado por propietario"},
    )
    assert decision.status_code == 200, decision.text

    returned = client.post(
        f"/api/v1/operations/finance/counter-sales/{sale['id']}/returns",
        headers=admin_headers,
        json={
            "approval_id": approval["id"], "reason": "Cliente solicita devolver producto sin abrir",
            "method": "CASH", "actor": "cajera-mostrador",
            "items": [{"sale_item_id": item_id, "quantity": "1"}],
        },
    )
    assert returned.status_code == 201, returned.text
    db.expire_all()
    assert db.get(ApprovalRequest, approval["id"]).status == "CONSUMED"
    assert db.get(RetailSale, sale["id"]).status == "RETURNED"
    current = client.get(
        "/api/v1/operations/finance/cash-sessions/current", headers=admin_headers
    ).json()
    closed = client.post(
        f"/api/v1/operations/finance/cash-sessions/{current['id']}/close",
        headers=admin_headers,
        json={"counted_cash": "500", "actor": "cajera-mostrador"},
    )
    assert closed.status_code == 200, closed.text
