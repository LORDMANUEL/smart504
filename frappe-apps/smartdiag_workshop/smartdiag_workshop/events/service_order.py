from __future__ import annotations

import frappe
from smartdiag_domain.work_orders import WorkOrderStatus, transition_work_order

from .outbox import enqueue_event


def validate_service_order(doc, method=None) -> None:
    del method
    if not doc.get("sd_vehicle"):
        frappe.throw("Vehicle is required for SmartDiag service orders")
    target_raw = doc.get("sd_workflow_state") or WorkOrderStatus.CREATED.value
    if isinstance(doc, dict):
        doc["sd_workflow_state"] = target_raw
    else:
        doc.sd_workflow_state = target_raw
    before = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
    previous_raw = before.get("sd_workflow_state") if before else None
    if not previous_raw or previous_raw == target_raw:
        return
    try:
        transition_work_order(
            current_status=WorkOrderStatus(previous_raw),
            requested_status=WorkOrderStatus(target_raw),
            actor=getattr(getattr(frappe, "session", None), "user", "system"),
            reason=doc.get("sd_transition_reason") or "Actualización de Service Order",
            invoice_reference=doc.get("sd_invoice_reference"),
        )
    except ValueError as exc:
        frappe.throw(str(exc))


def after_insert(doc, method=None) -> None:
    del method
    enqueue_event(
        event_type="WORK_ORDER_CREATED",
        aggregate_type=doc.doctype,
        aggregate_id=doc.name,
        payload={"vehicle": doc.get("sd_vehicle"), "status": doc.get("sd_workflow_state")},
    )


def on_update(doc, method=None) -> None:
    del method
    if doc.has_value_changed("sd_workflow_state"):
        enqueue_event(
            event_type="WORK_ORDER_STATUS_CHANGED",
            aggregate_type=doc.doctype,
            aggregate_id=doc.name,
            payload={"status": doc.get("sd_workflow_state"), "promised_at": doc.get("sd_promised_at")},
        )


def on_submit(doc, method=None) -> None:
    del method
    enqueue_event(
        event_type="WORK_ORDER_SUBMITTED", aggregate_type=doc.doctype, aggregate_id=doc.name, payload={}
    )


def on_cancel(doc, method=None) -> None:
    del method
    enqueue_event(
        event_type="WORK_ORDER_CANCELLED", aggregate_type=doc.doctype, aggregate_id=doc.name, payload={}
    )


def on_quotation_update(doc, method=None) -> None:
    del method
    if doc.has_value_changed("sd_approval_status"):
        enqueue_event(
            event_type="QUOTE_STATUS_CHANGED",
            aggregate_type=doc.doctype,
            aggregate_id=doc.name,
            payload={"status": doc.get("sd_approval_status"), "vehicle": doc.get("sd_vehicle")},
        )


def on_quotation_submit(doc, method=None) -> None:
    del method
    enqueue_event(
        event_type="QUOTE_SENT",
        aggregate_type=doc.doctype,
        aggregate_id=doc.name,
        payload={"vehicle": doc.get("sd_vehicle"), "grand_total": doc.get("grand_total")},
    )
