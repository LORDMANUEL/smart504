from __future__ import annotations

import io

from PIL import Image


def make_image() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (640, 480), (230, 230, 230)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_public_catalog_is_empty_before_admin_creates_product(client) -> None:
    assert client.get("/api/v1/catalog/products").json() == []


def test_admin_can_create_product_and_upload_primary_image(client, admin_headers) -> None:
    category = client.post(
        "/api/v1/admin/catalog/categories",
        headers=admin_headers,
        json={"name": "Filtros", "description": "Filtros automotrices"},
    )
    assert category.status_code == 201

    product = client.post(
        "/api/v1/admin/catalog/products",
        headers=admin_headers,
        json={
            "sku": "FL-001",
            "name": "Filtro de aceite",
            "category_id": category.json()["id"],
            "price": "350.00",
            "currency": "HNL",
            "stock_qty": "5",
            "compatibility_notes": "Validar por VIN",
        },
    )
    assert product.status_code == 201
    product_id = product.json()["id"]

    image = client.post(
        f"/api/v1/admin/catalog/products/{product_id}/images/upload",
        headers=admin_headers,
        files={"image": ("filter.jpg", make_image(), "image/jpeg")},
        data={
            "alt_text": "Filtro de aceite visto de frente",
            "attribution_text": "Fotografía de prueba",
            "make_primary": "true",
        },
    )
    assert image.status_code == 201
    assert image.json()["is_primary"] is True
    assert image.json()["public_url"].startswith("/media/products/")
    assert image.json()["alt_text"] == "Filtro de aceite visto de frente"

    public_products = client.get("/api/v1/catalog/products").json()
    assert len(public_products) == 1
    assert public_products[0]["images"][0]["attribution_text"] == "Fotografía de prueba"
    assert public_products[0]["images"][0]["alt_text"] == "Filtro de aceite visto de frente"


def test_google_search_requires_explicit_configuration(client, admin_headers) -> None:
    response = client.get(
        "/api/v1/admin/catalog/images/google?q=filtro+aceite",
        headers=admin_headers,
    )
    assert response.status_code == 503
    assert "upload" in response.json()["detail"].lower()


def test_catalog_admin_requires_token(client) -> None:
    response = client.get("/api/v1/admin/catalog/products")
    assert response.status_code == 401


def test_public_fitment_never_enumerates_persisted_private_vehicles(client, db) -> None:
    from decimal import Decimal
    from app.models import CatalogProduct, Customer, Vehicle

    customer = Customer(full_name="Cliente VIN", phone="99991111")
    db.add(customer); db.flush()
    vehicle = Vehicle(customer_id=customer.id, vin="1FMCU0G6XLUA12545", make="Ford", model="Escape", model_year=2020)
    matched = CatalogProduct(sku="VIN-ESC-1", slug="vin-esc-1", name="Filtro Escape", price=Decimal("100"), active=True, compatibility_notes="Ford Escape 2020")
    other = CatalogProduct(sku="VIN-CIV-1", slug="vin-civ-1", name="Filtro Civic", price=Decimal("90"), active=True, compatibility_notes="Honda Civic 2008")
    db.add_all([vehicle, matched, other]); db.commit()

    response = client.get("/api/v1/catalog/fitment?vin=1fmcu0g6xlua12545")
    assert response.status_code == 200
    assert response.json()["status"] == "AUTH_REQUIRED"
    assert response.json()["vehicle"] is None
    assert response.json()["products"] == []

    unknown = client.get("/api/v1/catalog/fitment?vin=UNKNOWNVIN1234567")
    assert unknown.status_code == 200
    assert unknown.json()["status"] == "AUTH_REQUIRED"


def test_public_booking_is_persisted(client) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "full_name": "Luis Rivera",
            "phone": "+504 9999-9999",
            "email": "luis@example.com",
            "vehicle_summary": "Ford Escape 2020",
            "service_requested": "Diagnóstico electrónico",
            "preferred_date": "2026-08-15",
            "concern": "La luz de check engine permanece encendida.",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "NEW"
    booking_id = response.json()["id"]

    listed = client.get(
        "/api/v1/operations/bookings",
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert listed.status_code == 200
    assert any(item["id"] == booking_id for item in listed.json())

    heatmap = client.get(
        "/api/v1/operations/flow-events/heatmap",
        headers={"X-Admin-Token": "test-admin-token"},
    ).json()
    assert any(
        cell["module"] == "RECEPTION" and cell["action"] == "BOOKING_CREATED" for cell in heatmap
    )

    confirmed = client.patch(
        f"/api/v1/operations/bookings/{booking_id}",
        headers={"X-Admin-Token": "test-admin-token"},
        json={"status": "CONFIRMED", "actor": "asesor-demo"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"


def test_deleting_product_image_removes_stored_file(client, admin_headers) -> None:
    import os
    from pathlib import Path

    category = client.post(
        "/api/v1/admin/catalog/categories",
        headers=admin_headers,
        json={"name": f"Imagenes-{os.urandom(3).hex()}"},
    ).json()
    product = client.post(
        "/api/v1/admin/catalog/products",
        headers=admin_headers,
        json={
            "sku": f"IMG-{os.urandom(4).hex()}",
            "name": f"Producto imagen {os.urandom(3).hex()}",
            "category_id": category["id"],
            "price": "100.00",
        },
    ).json()
    uploaded = client.post(
        f"/api/v1/admin/catalog/products/{product['id']}/images/upload",
        headers=admin_headers,
        files={"image": ("part.jpg", make_image(), "image/jpeg")},
        data={"alt_text": "Repuesto de prueba"},
    ).json()
    relative = uploaded["public_url"].removeprefix("/media/")
    stored = Path(os.environ["MEDIA_ROOT"]) / relative
    assert stored.exists()

    response = client.delete(
        f"/api/v1/admin/catalog/products/{product['id']}/images/{uploaded['id']}",
        headers=admin_headers,
    )
    assert response.status_code == 204
    assert not stored.exists()
