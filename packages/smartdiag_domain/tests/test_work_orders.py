from datetime import datetime, timezone

import pytest

from smartdiag_domain.work_orders import (
    WorkOrderStatus,
    allowed_transitions,
    status_label,
    transition_work_order,
)


def test_exact_six_operational_labels_are_preserved() -> None:
    assert [status_label(status) for status in WorkOrderStatus] == [
        "OT creada",
        "OT cotizada por técnico",
        "OT pendiente aprobación cliente",
        "OT pendiente de repuestos",
        "OT finalizada para facturar",
        "OT facturada",
    ]


def test_created_can_only_be_quoted_by_technician() -> None:
    assert allowed_transitions(WorkOrderStatus.CREATED) == (
        WorkOrderStatus.QUOTED_BY_TECHNICIAN,
    )


def test_invoiced_requires_invoice_reference() -> None:
    with pytest.raises(ValueError, match="invoice_reference"):
        transition_work_order(
            current_status=WorkOrderStatus.READY_TO_INVOICE,
            requested_status=WorkOrderStatus.INVOICED,
            actor="caja@smartdiag504.com",
            reason="Cliente pagó",
        )


def test_transition_records_auditable_fields() -> None:
    occurred_at = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    decision = transition_work_order(
        current_status=WorkOrderStatus.READY_TO_INVOICE,
        requested_status=WorkOrderStatus.INVOICED,
        actor="caja@smartdiag504.com",
        reason="Factura emitida en ERPNext",
        invoice_reference="ACC-SINV-2026-00001",
        idempotency_key="invoice-00001",
        occurred_at=occurred_at,
    )

    assert decision.invoice_reference == "ACC-SINV-2026-00001"
    assert decision.idempotency_key == "invoice-00001"
    assert decision.occurred_at == occurred_at


def test_invalid_skip_is_rejected() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        transition_work_order(
            current_status=WorkOrderStatus.CREATED,
            requested_status=WorkOrderStatus.READY_TO_INVOICE,
            actor="admin",
            reason="Intento de salto",
        )
