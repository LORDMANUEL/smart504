from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from pydantic import SecretStr

from app.config import Settings
from app.services.counter_sales_sync import (
    build_credit_note_document,
    build_sales_invoice_document,
    synchronize_retail_sale,
)


def sale_fixture():
    item = SimpleNamespace(
        id="sale-line-1",
        sku="ESC-FIL-2020",
        name="Filtro de aceite Motorcraft",
        quantity=Decimal("2"),
        unit_price=Decimal("320.00"),
        line_total=Decimal("640.00"),
    )
    sale = SimpleNamespace(
        id="sale-1",
        sale_number="MOST-260814-ERP001",
        customer_name="Consumidor final",
        phone="9999-5040",
        tax_id=None,
        currency="HNL",
        subtotal=Decimal("640.00"),
        discount=Decimal("20.00"),
        tax=Decimal("0.00"),
        total=Decimal("620.00"),
        payment_method="CARD",
        payment_reference="POS-504-001",
        completed_at=datetime(2026, 8, 14, tzinfo=UTC),
        items=[item],
        sync_status="PENDING",
        sync_attempts=0,
        sync_error=None,
        erpnext_invoice_id=None,
        erpnext_payment_id=None,
        last_sync_at=None,
    )
    return sale


def test_invoice_document_is_idempotent_and_updates_stock() -> None:
    document = build_sales_invoice_document(
        sale_fixture(),
        company="SmartDiag504 Demo",
        customer="Consumidor Final SmartDiag504",
        warehouse="MAIN-STOCK - SD504",
    )
    assert document["po_no"] == "MOST-260814-ERP001"
    assert document["update_stock"] == 1
    assert document["discount_amount"] == 20.0
    assert document["items"] == [
        {
            "item_code": "ESC-FIL-2020",
            "item_name": "Filtro de aceite Motorcraft",
            "qty": 2.0,
            "rate": 320.0,
            "warehouse": "MAIN-STOCK - SD504",
        }
    ]


def test_credit_note_uses_negative_quantities_and_original_invoice() -> None:
    sale = sale_fixture()
    returned = SimpleNamespace(
        return_number="DEV-M-260814-ERP001",
        total=Decimal("310.00"),
        reason="Producto sellado por error",
        created_at=datetime(2026, 8, 14, tzinfo=UTC),
        items=[
            SimpleNamespace(
                quantity=Decimal("1"),
                unit_refund=Decimal("310.00"),
                sale_item_id="sale-line-1",
            )
        ],
    )
    document = build_credit_note_document(
        sale,
        returned,
        company="SmartDiag504 Demo",
        customer="Consumidor Final SmartDiag504",
        warehouse="MAIN-STOCK - SD504",
        erpnext_invoice_id="ACC-SINV-2026-00001",
    )
    assert document["is_return"] == 1
    assert document["return_against"] == "ACC-SINV-2026-00001"
    assert document["po_no"] == "DEV-M-260814-ERP001"
    assert document["items"][0]["qty"] == -1.0
    assert document["items"][0]["rate"] == 310.0


class SuccessfulERPClient:
    def __init__(self) -> None:
        self.calls = 0

    def sync_retail_sale(self, **kwargs):
        self.calls += 1
        return {"invoice_id": "ACC-SINV-2026-00001", "payment_id": "ACC-PAY-2026-00001"}


class MemoryDB:
    def __init__(self) -> None:
        self.events = []
        self.commits = 0

    def add(self, value) -> None:
        self.events.append(value)

    def commit(self) -> None:
        self.commits += 1

    def scalars(self, _statement):
        return []


def test_sale_sync_persists_result_and_does_not_duplicate() -> None:
    sale = sale_fixture()
    client = SuccessfulERPClient()
    db = MemoryDB()
    settings = Settings(
        frappe_base_url="https://erp.example",
        frappe_api_key=SecretStr("key"),
        frappe_api_secret=SecretStr("secret"),
        frappe_company="SmartDiag504 Demo",
    )
    warehouse = SimpleNamespace(code="MAIN-STOCK")

    synchronize_retail_sale(db, sale, warehouse, settings, client=client)
    synchronize_retail_sale(db, sale, warehouse, settings, client=client)

    assert sale.sync_status == "SYNCED"
    assert sale.erpnext_invoice_id == "ACC-SINV-2026-00001"
    assert sale.erpnext_payment_id == "ACC-PAY-2026-00001"
    assert sale.sync_attempts == 1
    assert sale.sync_error is None
    assert client.calls == 1
