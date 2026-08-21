from __future__ import annotations

import pytest
from playwright.sync_api import Page, sync_playwright

from tests.frontend_test_utils import chromium_launch_options, load_app


@pytest.fixture()
def page() -> Page:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**chromium_launch_options())
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="es-HN")
        page = context.new_page()
        yield page
        context.close()
        browser.close()


def test_public_storefront_search_cart_and_booking(page: Page) -> None:
    load_app(page, "public-web")
    assert page.locator("#booking-success").is_hidden()
    assert page.locator("h1").inner_text() == "Tu vehículo no necesita suposiciones."

    page.locator("[data-nav-target='repuestos']").first.click()
    page.locator("#parts-search").fill("filtro")
    assert page.locator("[data-product-card]").count() >= 1
    assert "Filtro" in page.locator("[data-product-card]").first.inner_text()

    page.locator("[data-product-card] [data-add-to-cart]").first.click()
    assert page.locator("#cart-count").inner_text() == "1"
    page.locator("#open-cart").click()
    assert page.locator("#cart-drawer").get_attribute("aria-hidden") == "false"
    assert "Subtotal" in page.locator("#cart-drawer").inner_text()
    page.locator("#close-cart").click()

    page.locator("[data-nav-target='reservar']").first.click()
    page.locator("#booking-name").fill("Ana Martínez")
    page.locator("#booking-phone").fill("9999-1234")
    page.locator("#booking-make").fill("Ford")
    page.locator("#booking-model").fill("Escape")
    page.locator("#booking-year").fill("2018")
    page.locator("#booking-date").fill("2099-08-20")
    page.locator("#booking-reason").fill("Diagnóstico de luz de motor")
    page.locator(".consent input").check()
    page.locator("#booking-form button[type='submit']").click()
    page.locator("#booking-success").wait_for(state="visible")
    assert "Solicitud recibida" in page.locator("#booking-success").inner_text()


def test_public_web_maps_platform_api_catalog_and_booking_contract(page: Page) -> None:
    captured_booking: dict[str, object] = {}

    def catalog_route(route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body='''{
              "items": [{
                "sku": "API-001",
                "slug": "filtro-api",
                "name": "Filtro enviado por API",
                "description": "Producto conectado con ERPNext.",
                "brand": "Motorcraft",
                "price": 725.5,
                "currency": "HNL",
                "stock_qty": 11,
                "online_available_qty": 6,
                "compatibility_status": "REQUIRES_VALIDATION",
                "fitment": ["Ford Escape 2018"],
                "image_url": null
              }],
              "total": 1
            }''',
        )

    def booking_route(route) -> None:
        captured_booking.update(route.request.post_data_json)
        route.fulfill(
            status=201,
            content_type="application/json",
            body='''{
              "booking_id": "SD-BKG-TEST01",
              "status": "REQUESTED",
              "created_at": "2026-08-12T12:00:00Z",
              "idempotent_replay": false
            }''',
        )

    page.route("https://api.smartdiag.test/api/v1/catalog/products", catalog_route)
    page.route("https://api.smartdiag.test/api/v1/bookings", booking_route)
    load_app(page, "public-web", config={"apiBaseUrl": "https://api.smartdiag.test"})

    page.locator("[data-product-card]").wait_for()
    assert page.locator("[data-product-card]").count() == 1
    assert "Filtro enviado por API" in page.locator("[data-product-card]").inner_text()
    assert "6 disponibles" in page.locator("[data-product-card]").inner_text()
    assert "Requiere validación" in page.locator("[data-product-card]").inner_text()

    page.locator("#booking-name").fill("Ana Martínez")
    page.locator("#booking-phone").fill("9999-1234")
    page.locator("#booking-email").fill("ana@example.com")
    page.locator("#booking-make").fill("Ford")
    page.locator("#booking-model").fill("Escape")
    page.locator("#booking-year").fill("2018")
    page.locator("#booking-date").fill("2099-08-20")
    page.locator("#booking-service").select_option("DIAGNOSTICO")
    page.locator("#booking-reason").fill("Luz de motor encendida")
    page.locator(".consent input").check()
    page.locator("#booking-form button[type='submit']").click()
    page.locator("#booking-reference").get_by_text("SD-BKG-TEST01", exact=False).wait_for()

    assert page.locator("#booking-reference").inner_text().startswith("Referencia SD-BKG-TEST01")
    assert captured_booking == {
        "customer_name": "Ana Martínez",
        "phone": "9999-1234",
        "email": "ana@example.com",
        "service_code": "DIAGNOSTICO",
        "requested_date": "2099-08-20",
        "vehicle": {"make": "Ford", "model": "Escape", "year": 2018},
        "notes": "Luz de motor encendida",
    }
