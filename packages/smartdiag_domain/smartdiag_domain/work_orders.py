from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256


class WorkOrderStatus(StrEnum):
    CREATED = "CREATED"
    QUOTED_BY_TECHNICIAN = "QUOTED_BY_TECHNICIAN"
    PENDING_CUSTOMER_APPROVAL = "PENDING_CUSTOMER_APPROVAL"
    PENDING_PARTS = "PENDING_PARTS"
    READY_TO_INVOICE = "READY_TO_INVOICE"
    INVOICED = "INVOICED"


_STATUS_LABELS: dict[WorkOrderStatus, str] = {
    WorkOrderStatus.CREATED: "OT creada",
    WorkOrderStatus.QUOTED_BY_TECHNICIAN: "OT cotizada por técnico",
    WorkOrderStatus.PENDING_CUSTOMER_APPROVAL: "OT pendiente aprobación cliente",
    WorkOrderStatus.PENDING_PARTS: "OT pendiente de repuestos",
    WorkOrderStatus.READY_TO_INVOICE: "OT finalizada para facturar",
    WorkOrderStatus.INVOICED: "OT facturada",
}

_TRANSITIONS: dict[WorkOrderStatus, frozenset[WorkOrderStatus]] = {
    WorkOrderStatus.CREATED: frozenset({WorkOrderStatus.QUOTED_BY_TECHNICIAN}),
    WorkOrderStatus.QUOTED_BY_TECHNICIAN: frozenset(
        {WorkOrderStatus.PENDING_CUSTOMER_APPROVAL}
    ),
    WorkOrderStatus.PENDING_CUSTOMER_APPROVAL: frozenset(
        {
            WorkOrderStatus.QUOTED_BY_TECHNICIAN,
            WorkOrderStatus.PENDING_PARTS,
            WorkOrderStatus.READY_TO_INVOICE,
        }
    ),
    WorkOrderStatus.PENDING_PARTS: frozenset(
        {
            WorkOrderStatus.QUOTED_BY_TECHNICIAN,
            WorkOrderStatus.READY_TO_INVOICE,
        }
    ),
    WorkOrderStatus.READY_TO_INVOICE: frozenset(
        {
            WorkOrderStatus.PENDING_PARTS,
            WorkOrderStatus.INVOICED,
        }
    ),
    WorkOrderStatus.INVOICED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class TransitionDecision:
    previous_status: WorkOrderStatus
    next_status: WorkOrderStatus
    label: str
    actor: str
    reason: str
    invoice_reference: str | None
    idempotency_key: str
    occurred_at: datetime


def status_label(status: WorkOrderStatus) -> str:
    return _STATUS_LABELS[status]


def allowed_transitions(status: WorkOrderStatus) -> tuple[WorkOrderStatus, ...]:
    return tuple(sorted(_TRANSITIONS[status], key=lambda value: value.value))


def transition_work_order(
    *,
    current_status: WorkOrderStatus,
    requested_status: WorkOrderStatus,
    actor: str,
    reason: str,
    invoice_reference: str | None = None,
    idempotency_key: str | None = None,
    occurred_at: datetime | None = None,
) -> TransitionDecision:
    actor = actor.strip()
    reason = reason.strip()
    invoice_reference = invoice_reference.strip() if invoice_reference else None

    if not actor:
        raise ValueError("actor is required")
    if not reason:
        raise ValueError("reason is required")
    if requested_status == current_status:
        raise ValueError("requested status is already active")
    if requested_status not in _TRANSITIONS[current_status]:
        raise ValueError(
            f"transition {current_status.value} -> {requested_status.value} is not allowed"
        )
    if requested_status == WorkOrderStatus.INVOICED and not invoice_reference:
        raise ValueError("invoice_reference is required to mark an OT as invoiced")

    timestamp = occurred_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    key = (idempotency_key or "").strip()
    if not key:
        material = "|".join(
            [
                current_status.value,
                requested_status.value,
                actor,
                reason,
                invoice_reference or "",
                timestamp.isoformat(),
            ]
        )
        key = sha256(material.encode("utf-8")).hexdigest()

    return TransitionDecision(
        previous_status=current_status,
        next_status=requested_status,
        label=status_label(requested_status),
        actor=actor,
        reason=reason,
        invoice_reference=invoice_reference,
        idempotency_key=key,
        occurred_at=timestamp,
    )
