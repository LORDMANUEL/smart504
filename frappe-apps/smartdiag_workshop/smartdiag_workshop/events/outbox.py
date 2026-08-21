from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import frappe
from smartdiag_domain.events import DomainEvent


def enqueue_event(*, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict[str, Any]) -> str:
    actor = frappe.session.user if getattr(frappe, "session", None) else None
    event = DomainEvent.create(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        actor_id=actor,
    )
    if frappe.db.exists("SmartDiag Event Outbox", {"event_key": event.event_key}):
        return event.event_key
    doc = frappe.get_doc(
        {
            "doctype": "SmartDiag Event Outbox",
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "event_key": event.event_key,
            "payload_json": json.dumps(event.payload, ensure_ascii=False, default=str),
            "actor_id": event.actor_id,
            "occurred_at": event.occurred_at.astimezone(UTC).replace(tzinfo=None),
            "status": "PENDING",
        }
    )
    doc.insert(ignore_permissions=True)
    return event.event_key


def publish_pending_events() -> None:
    settings = frappe.get_single("SmartDiag Settings")
    if not settings.event_webhook_url:
        return
    rows = frappe.get_all(
        "SmartDiag Event Outbox",
        filters={"status": ["in", ["PENDING", "FAILED"]], "attempts": ["<", 10]},
        fields=["name"],
        order_by="occurred_at asc",
        limit_page_length=100,
    )
    for row in rows:
        frappe.enqueue(
            "smartdiag_workshop.events.outbox.publish_one_event",
            queue="short",
            outbox_name=row.name,
            enqueue_after_commit=True,
        )


def publish_one_event(outbox_name: str) -> None:
    import hashlib
    import hmac

    import requests

    settings = frappe.get_single("SmartDiag Settings")
    doc = frappe.get_doc("SmartDiag Event Outbox", outbox_name)
    body = doc.payload_envelope().encode("utf-8")
    signature = hmac.new(settings.get_password("event_webhook_secret").encode(), body, hashlib.sha256).hexdigest()
    try:
        response = requests.post(
            settings.event_webhook_url,
            data=body,
            headers={"Content-Type": "application/json", "X-SmartDiag-Signature": signature},
            timeout=20,
        )
        response.raise_for_status()
        doc.status = "PUBLISHED"
        doc.published_at = datetime.now(UTC).replace(tzinfo=None)
        doc.last_error = None
    except Exception as exc:
        doc.status = "FAILED"
        doc.last_error = str(exc)[:1000]
    finally:
        doc.attempts = (doc.attempts or 0) + 1
        doc.save(ignore_permissions=True)
