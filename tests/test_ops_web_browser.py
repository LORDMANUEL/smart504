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


def test_ops_dashboard_navigation_and_order_transition(page: Page) -> None:
    load_app(page, "ops-web")
    assert page.locator("h1").inner_text() == "Operación de hoy"
    assert page.locator("[data-metric='open-orders']").inner_text() == "18"

    page.locator(".ops-nav [data-view-target='orders']").click()
    order = page.locator("[data-order-id='OT-2026-0184']")
    assert order.count() == 1
    assert "APROBADO" in order.inner_text()
    order.locator("[data-action='advance']").click()
    assert "PROGRAMADO" in order.inner_text()

    page.locator(".ops-nav [data-view-target='workshop']").click()
    assert page.locator("[data-bay-id='B-03']").count() == 1
    assert "Diagnóstico" in page.locator("[data-bay-id='B-03']").inner_text()

    page.locator(".ops-nav [data-view-target='parts']").click()
    assert page.locator("[data-part-request]").count() >= 2
