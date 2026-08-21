from __future__ import annotations

from .outbox import enqueue_event


def on_sales_invoice_submit(doc, method=None) -> None:
    del method
    service_order = doc.get("custom_service_order") or doc.get("sd_service_order")
    if service_order:
        enqueue_event(
            event_type="INVOICE_POSTED",
            aggregate_type=doc.doctype,
            aggregate_id=doc.name,
            payload={"service_order": service_order, "grand_total": doc.grand_total},
        )


def on_sales_invoice_cancel(doc, method=None) -> None:
    del method
    enqueue_event(event_type="INVOICE_CANCELLED", aggregate_type=doc.doctype, aggregate_id=doc.name, payload={})


def on_stock_entry_submit(doc, method=None) -> None:
    del method
    service_order = doc.get("custom_service_order") or doc.get("sd_service_order")
    if service_order:
        enqueue_event(
            event_type="PART_MOVEMENT_POSTED",
            aggregate_type=doc.doctype,
            aggregate_id=doc.name,
            payload={"service_order": service_order, "stock_entry_type": doc.stock_entry_type},
        )
