from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select

from app.config import Settings
from app.models import FlowEvent, InventoryMovement
from app.services.frappe import FrappeWriteClient


def _money(value: Any) -> float:
    return float(value)


def build_sales_invoice_document(
    sale,
    *,
    company: str,
    customer: str,
    warehouse: str,
    tax_account: str | None = None,
) -> dict[str, Any]:
    if sale.tax and not tax_account:
        raise ValueError("Configure FRAPPE_TAX_ACCOUNT before synchronizing taxable sales")
    document: dict[str, Any] = {
        "company": company,
        "customer": customer,
        "currency": sale.currency,
        "selling_price_list": "Standard Selling",
        "posting_date": sale.completed_at.date().isoformat(),
        "due_date": sale.completed_at.date().isoformat(),
        "update_stock": 1,
        "set_warehouse": warehouse,
        "po_no": sale.sale_number,
        "apply_discount_on": "Net Total",
        "discount_amount": _money(sale.discount),
        "remarks": f"Venta por mostrador SmartDiag504 {sale.sale_number}",
        "items": [
            {
                "item_code": item.sku,
                "item_name": item.name,
                "qty": _money(item.quantity),
                "rate": _money(item.unit_price),
                "warehouse": warehouse,
            }
            for item in sale.items
        ],
    }
    if sale.tax:
        document["taxes"] = [
            {
                "charge_type": "Actual",
                "account_head": tax_account,
                "description": "Impuesto venta mostrador",
                "tax_amount": _money(sale.tax),
            }
        ]
    return document


def build_credit_note_document(
    sale,
    return_record,
    *,
    company: str,
    customer: str,
    warehouse: str,
    erpnext_invoice_id: str,
) -> dict[str, Any]:
    sale_items = {item.id: item for item in sale.items}
    return {
        "company": company,
        "customer": customer,
        "currency": sale.currency,
        "posting_date": return_record.created_at.date().isoformat(),
        "due_date": return_record.created_at.date().isoformat(),
        "is_return": 1,
        "return_against": erpnext_invoice_id,
        "update_stock": 1,
        "set_warehouse": warehouse,
        "po_no": return_record.return_number,
        "remarks": f"Devolucion SmartDiag504 {return_record.return_number}: {return_record.reason}",
        "items": [
            {
                "item_code": sale_items[item.sale_item_id].sku,
                "item_name": sale_items[item.sale_item_id].name,
                "qty": -_money(item.quantity),
                "rate": _money(item.unit_refund),
                "warehouse": warehouse,
            }
            for item in return_record.items
        ],
    }


def _failure_detail(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)[:500]
    if isinstance(exc, ValueError):
        return str(exc)[:500]
    return "Unexpected ERPNext synchronization failure"


def synchronize_retail_sale(db, sale, warehouse, settings: Settings, *, client=None):
    if sale.sync_status == "SYNCED" and sale.erpnext_invoice_id and sale.erpnext_payment_id:
        return sale
    sale.sync_status = "SYNCING"
    sale.sync_error = None
    sale.sync_attempts += 1
    sale.last_sync_at = datetime.now(UTC)
    db.commit()
    expected_warehouse = f"{warehouse.code} - {settings.frappe_warehouse_suffix}"
    try:
        erp_client = client or FrappeWriteClient(settings)
        document = build_sales_invoice_document(
            sale,
            company=settings.frappe_company,
            customer=settings.frappe_customer,
            warehouse=expected_warehouse,
            tax_account=settings.frappe_tax_account,
        )
        result = erp_client.sync_retail_sale(
            invoice_document=document,
            warehouse_code=warehouse.code,
            company=settings.frappe_company,
            warehouse_suffix=settings.frappe_warehouse_suffix,
            customer_name=settings.frappe_customer,
            payment_method=sale.payment_method,
            payment_reference=sale.payment_reference,
        )
    except Exception as exc:
        sale.sync_status = "FAILED"
        sale.sync_error = _failure_detail(exc)
        sale.last_sync_at = datetime.now(UTC)
        db.add(
            FlowEvent(
                module="COUNTER_SALES",
                action="COUNTER_SALE_ERP_SYNC_FAILED",
                item_reference=sale.sale_number,
                actor="erp-sync",
                result="FAILED",
                metadata_json={"detail": sale.sync_error, "attempt": sale.sync_attempts},
            )
        )
        db.commit()
        return sale
    sale.erpnext_invoice_id = result["invoice_id"]
    sale.erpnext_payment_id = result["payment_id"]
    sale.sync_status = "SYNCED"
    sale.sync_error = None
    sale.last_sync_at = datetime.now(UTC)
    for movement in db.scalars(
        select(InventoryMovement).where(InventoryMovement.reference == sale.sale_number)
    ):
        movement.erpnext_stock_entry_id = result["invoice_id"]
        movement.sync_status = "SYNCED"
    db.add(
        FlowEvent(
            module="COUNTER_SALES",
            action="COUNTER_SALE_ERP_SYNCED",
            item_reference=sale.sale_number,
            actor="erp-sync",
            result="SUCCESS",
            metadata_json=result,
        )
    )
    db.commit()
    return sale


def synchronize_retail_return(
    db, sale, return_record, warehouse, settings: Settings, *, client=None
):
    if (
        return_record.sync_status == "SYNCED"
        and return_record.erpnext_credit_note_id
        and return_record.erpnext_payment_id
    ):
        return return_record
    if not sale.erpnext_invoice_id:
        return_record.sync_status = "BLOCKED"
        return_record.sync_error = "Synchronize the original sale before its return"
        db.commit()
        return return_record
    return_record.sync_status = "SYNCING"
    return_record.sync_error = None
    return_record.sync_attempts += 1
    return_record.last_sync_at = datetime.now(UTC)
    db.commit()
    expected_warehouse = f"{warehouse.code} - {settings.frappe_warehouse_suffix}"
    try:
        erp_client = client or FrappeWriteClient(settings)
        document = build_credit_note_document(
            sale,
            return_record,
            company=settings.frappe_company,
            customer=settings.frappe_customer,
            warehouse=expected_warehouse,
            erpnext_invoice_id=sale.erpnext_invoice_id,
        )
        result = erp_client.sync_retail_sale(
            invoice_document=document,
            warehouse_code=warehouse.code,
            company=settings.frappe_company,
            warehouse_suffix=settings.frappe_warehouse_suffix,
            customer_name=settings.frappe_customer,
            payment_method=return_record.method,
            payment_reference=return_record.reference,
        )
    except Exception as exc:
        return_record.sync_status = "FAILED"
        return_record.sync_error = _failure_detail(exc)
        return_record.last_sync_at = datetime.now(UTC)
        db.add(
            FlowEvent(
                module="COUNTER_SALES",
                action="COUNTER_RETURN_ERP_SYNC_FAILED",
                item_reference=return_record.return_number,
                actor="erp-sync",
                result="FAILED",
                metadata_json={"detail": return_record.sync_error},
            )
        )
        db.commit()
        return return_record
    return_record.erpnext_credit_note_id = result["invoice_id"]
    return_record.erpnext_payment_id = result["payment_id"]
    return_record.sync_status = "SYNCED"
    return_record.sync_error = None
    return_record.last_sync_at = datetime.now(UTC)
    for movement in db.scalars(
        select(InventoryMovement).where(InventoryMovement.reference == return_record.return_number)
    ):
        movement.erpnext_stock_entry_id = result["invoice_id"]
        movement.sync_status = "SYNCED"
    db.add(
        FlowEvent(
            module="COUNTER_SALES",
            action="COUNTER_RETURN_ERP_SYNCED",
            item_reference=return_record.return_number,
            actor="erp-sync",
            result="SUCCESS",
            metadata_json=result,
        )
    )
    db.commit()
    return return_record
