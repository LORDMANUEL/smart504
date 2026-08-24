from __future__ import annotations

import os
from io import BytesIO

from PIL import Image

from fastapi_users.password import PasswordHelper
from app.models import CatalogProduct, ClientUser, Customer, Vehicle
from app.request_context import worker_identity
from sqlalchemy import select


def _login(client, monkeypatch) -> dict[str, str]:
    del monkeypatch
    response = client.post(
        "/api/v1/client-auth/login",
        data={"username": "cliente@example.com", "password": "cliente-demo-password"},
    )
    assert response.status_code == 204
    return {}


def _work_order_and_quote(client, admin_headers, db) -> tuple[dict, dict]:
    customer = Customer(
        full_name="Cliente Portal",
        phone=f"+504 9{os.urandom(3).hex()}",
        email="cliente@example.com",
    )
    db.add(customer)
    db.flush()
    vehicle = Vehicle(
        customer_id=customer.id,
        vin=f"TESTPORTAL{os.urandom(5).hex().upper()}",
        make="Ford",
        model="Escape",
        model_year=2020,
        plate="HPORTAL",
        mileage_km=81200,
    )
    db.add(vehicle)
    db.add(ClientUser(email="cliente@example.com", hashed_password=PasswordHelper().hash("cliente-demo-password"),
                      is_active=True, is_verified=True, is_superuser=False,
                      organization_id=customer.organization_id, customer_id=customer.id,
                      username=f"cliente.{customer.id[:8]}", full_name=customer.full_name,
                      notification_email="cliente@example.com",
                      managed_email=f"cliente.{customer.id[:8]}@smartdiag504.com",
                      mailbox_status="PENDING_CONFIGURATION"))
    db.commit()
    work_order = client.post(
        "/api/v1/operations/work-orders",
        headers=admin_headers,
        json={
            "customer_id": customer.id,
            "vehicle_id": vehicle.id,
            "title": "Servicio del portal",
            "concern": "Preparar cotizacion visible para el cliente.",
            "actor": "asesor-portal",
        },
    )
    assert work_order.status_code == 201
    quote = client.post(
        "/api/v1/operations/finance/quotes",
        headers=admin_headers,
        json={
            "work_order_id": work_order.json()["id"],
            "created_by": "asesor-portal",
            "discount": "0.00",
            "tax": "0.00",
            "lines": [
                {
                    "line_type": "LABOR",
                    "code": "MO-PORTAL",
                    "description": "Diagnostico completo",
                    "quantity": "1",
                    "unit_price": "850.00",
                    "unit_cost": "400.00",
                }
            ],
        },
    )
    assert quote.status_code == 201
    return work_order.json(), quote.json()


def test_client_portal_persists_vehicle_and_prints_quote(
    client, admin_headers, db, monkeypatch
) -> None:
    work_order, quote = _work_order_and_quote(client, admin_headers, db)
    headers = _login(client, monkeypatch)

    dashboard = client.get("/api/v1/client-portal/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert quote["id"] in {item["id"] for item in dashboard.json()["quotes"]}
    assert work_order["id"] == quote["work_order_id"]

    vehicle = client.post(
        "/api/v1/client-portal/vehicles",
        headers=headers,
        json={
            "vin": f"1HGCM82633A{os.urandom(3).hex().upper()}",
            "plate": "HCIVIC",
            "make": "Honda",
            "model": "Civic",
            "model_year": 2008,
            "engine": "1.8 i-VTEC",
            "mileage_km": 156000,
        },
    )
    assert vehicle.status_code == 201
    assert vehicle.json()["photo_url"] == "/vehicles/honda-civic-2008.png"

    html = client.get(f"/api/v1/client-documents/quotes/{quote['id']}.html", headers=headers)
    pdf = client.get(f"/api/v1/client-documents/quotes/{quote['id']}.pdf", headers=headers)
    assert html.status_code == 200
    assert quote["number"] in html.text
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")


def test_client_redeems_points_for_vehicle_maintenance(client, client_account, db) -> None:
    user = db.scalar(select(ClientUser).where(ClientUser.email == client_account["email"]))
    user.loyalty_enabled = True
    user.loyalty_points = 2000
    db.commit()
    assert client.post("/api/v1/client-auth/login", data={"username": client_account["email"], "password": client_account["password"]}).status_code == 204
    packages = client.get("/api/v1/client-portal/maintenance-packages")
    assert packages.status_code == 200
    package = next(item for item in packages.json() if item["id"] == "BASIC_OIL")
    assert package["available"] is True
    redemption = client.post("/api/v1/client-portal/loyalty/redeem", json={"package_id": package["id"], "vehicle_id": client_account["vehicle"].id, "idempotency_key": "redeem-basic-oil-001"})
    assert redemption.status_code == 201
    assert redemption.json()["remaining_points"] == 800


def test_client_fitment_uses_persisted_catalog_and_rejects_other_tenant_vehicle(
    client, client_account, db
) -> None:
    vehicle = client_account["vehicle"]
    product = CatalogProduct(
        sku=f"FIT-{os.urandom(3).hex()}", slug=f"fit-{os.urandom(4).hex()}",
        name="Filtro compatible persistente", price="525.00", stock_qty="4",
        stock_status="IN_STOCK", active=True,
        compatibility_notes=f"{vehicle.make} {vehicle.model} {vehicle.model_year}",
    )
    db.add(product)
    db.commit()
    login = client.post("/api/v1/client-auth/login", data={
        "username": client_account["email"], "password": client_account["password"],
    })
    assert login.status_code == 204
    response = client.get(f"/api/v1/client-portal/vehicles/{vehicle.id}/compatible-parts")
    assert response.status_code == 200
    assert product.id in {item["id"] for item in response.json()}

    with worker_identity(actor="test-provisioner", organization_id="OTHER-WORKSHOP"):
        other = Customer(organization_id="OTHER-WORKSHOP", full_name="Otro cliente", phone="+50495550000", email="otro@example.com")
        db.add(other)
        db.flush()
        other_vehicle = Vehicle(organization_id="OTHER-WORKSHOP", customer_id=other.id, vin="1HGCM82633A999999",
                                make="Honda", model="Civic", model_year=2008)
        db.add(other_vehicle)
        db.commit()
    denied = client.get(f"/api/v1/client-portal/vehicles/{other_vehicle.id}/compatible-parts")
    assert denied.status_code == 404


def test_client_profile_changes_password_and_does_not_fake_mfa_activation(
    client, client_account, db
) -> None:
    login = client.post("/api/v1/client-auth/login", data={
        "username": client_account["email"], "password": client_account["password"],
    })
    assert login.status_code == 204

    changed = client.put("/api/v1/client-portal/profile", json={
        "full_name": "Cliente Portal Seguro",
        "email": client_account["email"],
        "username": "cliente.portal.seguro",
        "credit_requested": True,
        "credit_amount": 25000,
        "new_password": "Nueva-clave-segura-504!",
    })
    assert changed.status_code == 200
    assert changed.json()["mfa_enabled"] is False
    assert changed.json()["credit_amount"] == "25000.00"

    client.post("/api/v1/client-auth/logout")
    old_login = client.post("/api/v1/client-auth/login", data={
        "username": client_account["email"], "password": client_account["password"],
    })
    assert old_login.status_code == 400
    new_login = client.post("/api/v1/client-auth/login", data={
        "username": client_account["email"], "password": "Nueva-clave-segura-504!",
    })
    assert new_login.status_code == 204


def test_marketing_campaign_publish_link_and_click_tracking(client, admin_headers) -> None:
    image_file = BytesIO()
    Image.new("RGB", (2, 2), "red").save(image_file, format="PNG")
    created = client.post(
        "/api/v1/operations/marketing/campaigns",
        headers=admin_headers,
        json={
            "title": f"Afinamiento Ford {os.urandom(3).hex()}",
            "description": "Campania medible para clientes Ford.",
            "audience": "Ford Escape y F-150",
            "price_from": 1850,
            "call_to_action": "Reserve su afinamiento",
            "tv_enabled": True,
            "display_seconds": 9,
        },
    )
    assert created.status_code == 201
    campaign = created.json()

    uploaded = client.post(
        f"/api/v1/operations/marketing/campaigns/{campaign['id']}/media",
        headers=admin_headers,
        files={
            "file": (
                "campania.png",
                image_file.getvalue(),
                "image/png",
            )
        },
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["media_type"] == "IMAGE"

    published = client.post(
        f"/api/v1/operations/marketing/campaigns/{campaign['id']}/publish",
        headers=admin_headers,
    )
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"
    assert published.json()["tv_enabled"] is True
    assert published.json()["display_seconds"] == 9

    public = client.get("/api/v1/marketing/campaigns")
    assert campaign["id"] in {item["id"] for item in public.json()}
    click = client.get(campaign["public_path"], follow_redirects=False)
    assert click.status_code == 302

    listed = client.get("/api/v1/operations/marketing/campaigns", headers=admin_headers)
    tracked = next(item for item in listed.json() if item["id"] == campaign["id"])
    assert tracked["clicks"] == 1
