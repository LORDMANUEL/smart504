from __future__ import annotations

import os


def create_product(client, admin_headers, *, stock_status: str = "IN_STOCK") -> dict:
    suffix = os.urandom(4).hex()
    response = client.post(
        "/api/v1/admin/catalog/products",
        headers=admin_headers,
        json={
            "sku": f"WEB-{suffix}",
            "name": f"Repuesto web {suffix}",
            "price": "875.50",
            "currency": "HNL",
            "stock_qty": "4",
            "stock_status": stock_status,
            "compatibility_notes": "Validar por VIN antes de instalar",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_public_customer_can_submit_idempotent_parts_order(client, admin_headers) -> None:
    product = create_product(client, admin_headers)
    payload = {
        "customer_name": "Luis Rivera",
        "phone": "+504 9999-9999",
        "email": "luis@example.com",
        "vehicle_vin": "1FMCU0GDXLUA00001",
        "notes": "Confirmar compatibilidad antes de facturar.",
        "idempotency_key": "web-checkout-0001",
        "items": [{"product_id": product["id"], "quantity": 2}],
    }

    created = client.post("/api/v1/store/orders", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "PENDING_CONFIRMATION"
    assert body["fulfillment_status"] == "AWAITING_REVIEW"
    assert body["assigned_cashier"] == "Caja principal"
    assert body["whatsapp_status"] == "PENDING"
    assert body["order_number"].startswith("WEB-")
    assert body["subtotal"] == "1751.00"
    assert body["discount"] == "0.00"
    assert body["total"] == "1751.00"
    assert body["items"][0]["sku"] == product["sku"]
    assert body["items"][0]["quantity"] == 2

    replay = client.post("/api/v1/store/orders", json=payload)
    assert replay.status_code == 200
    assert replay.json()["id"] == body["id"]


def test_published_promotion_applies_server_side_discount(client, admin_headers) -> None:
    product = create_product(client, admin_headers)
    campaign = client.post("/api/v1/operations/marketing/campaigns", headers=admin_headers, json={
        "title": "Promoción patria de prueba", "description": "Descuento verificado en servidor",
        "promo_code": "PATRIA504", "discount_percent": 10, "store_banner": True,
    })
    assert campaign.status_code == 201
    published = client.post(f"/api/v1/operations/marketing/campaigns/{campaign.json()['id']}/publish", headers=admin_headers)
    assert published.status_code == 200
    response = client.post("/api/v1/store/orders", json={
        "customer_name": "Cliente Promoción", "phone": "+504 9555-0000",
        "promo_code": "patria504", "idempotency_key": f"promotion-{os.urandom(4).hex()}",
        "items": [{"product_id": product["id"], "quantity": 1}],
    })
    assert response.status_code == 201
    assert response.json()["promo_code"] == "PATRIA504"
    assert response.json()["discount"] == "87.55"
    assert response.json()["total"] == "787.95"


def test_store_rejects_unavailable_product(client, admin_headers) -> None:
    product = create_product(client, admin_headers, stock_status="OUT_OF_STOCK")
    response = client.post(
        "/api/v1/store/orders",
        json={
            "customer_name": "Cliente Prueba",
            "phone": "+504 9999-8888",
            "idempotency_key": "web-checkout-0002",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 409
    assert "agotado" in response.json()["detail"].lower()


def test_admin_can_list_and_advance_store_order(client, admin_headers) -> None:
    product = create_product(client, admin_headers, stock_status="ON_REQUEST")
    created = client.post(
        "/api/v1/store/orders",
        json={
            "customer_name": "Cliente Repuestos",
            "phone": "+504 9777-7777",
            "idempotency_key": "web-checkout-0003",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    ).json()

    orders = client.get("/api/v1/admin/store/orders", headers=admin_headers)
    assert orders.status_code == 200
    assert created["id"] in {item["id"] for item in orders.json()}

    updated = client.patch(
        f"/api/v1/admin/store/orders/{created['id']}",
        headers=admin_headers,
        json={
            "status": "CONTACTED",
            "assigned_cashier": "María Caja",
            "whatsapp_status": "SENT",
            "actor": "maria-caja",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "CONTACTED"
    assert updated.json()["assigned_cashier"] == "María Caja"
    assert updated.json()["whatsapp_status"] == "SENT"


def test_cashier_can_store_private_payment_proof(client, admin_headers) -> None:
    product = create_product(client, admin_headers)
    order = client.post("/api/v1/store/orders", json={
        "customer_name": "Cliente Transferencia", "phone": "+504 9666-0000",
        "idempotency_key": f"payment-proof-{os.urandom(4).hex()}",
        "items": [{"product_id": product["id"], "quantity": 1}],
    }).json()
    uploaded = client.post(f"/api/v1/admin/store/orders/{order['id']}/payment-proofs",
        headers=admin_headers, data={"reference": "BAC-TRX-504", "amount": "875.50"},
        files={"file": ("transferencia.pdf", b"%PDF-1.4\n% comprobante de prueba\n%%EOF", "application/pdf")})
    assert uploaded.status_code == 201
    assert uploaded.json()["reference"] == "BAC-TRX-504"
    assert "storage_key" not in uploaded.json()
    listed = client.get(f"/api/v1/admin/store/orders/{order['id']}/payment-proofs", headers=admin_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["amount"] == "875.50"
    assert client.get(listed.json()[0]["content_url"]).status_code == 401
    content = client.get(listed.json()[0]["content_url"], headers=admin_headers)
    assert content.status_code == 200
    assert content.content.startswith(b"%PDF-")
