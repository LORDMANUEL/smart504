from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from fastapi import HTTPException
from smartdiag_domain.work_orders import WorkOrderStatus, transition_work_order
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import Customer, ErpIntegrationJob, FlowEvent, Vehicle, WorkOrder, WorkOrderEvent
from app.schemas import WorkOrderCreate, WorkOrderTransition, WorkOrderUpdate
from app.services.frappe import FrappeReadClient, verify_invoice_reference
from app.services.erp_outbox import enqueue_erp_job
from app.services.branch_scope import operational_branch_id
from app.request_context import audit_actor, current_identity


def _next_number(db: Session, organization_id: str) -> str:
    year = datetime.now(UTC).year
    count = db.scalar(select(func.count()).select_from(WorkOrder).where(
        WorkOrder.organization_id == organization_id
    )) or 0
    return f"OT-{year}-{count + 1:06d}"


def get_work_order(db: Session, work_order_id: str) -> WorkOrder:
    organization_id = current_identity().organization_id
    work_order = db.scalar(
        select(WorkOrder)
        .where(WorkOrder.id == work_order_id, WorkOrder.organization_id == organization_id)
        .options(selectinload(WorkOrder.events))
    )
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    return work_order


def queue_work_order_projection(
    db: Session, work_order: WorkOrder, *, change_key: str
) -> ErpIntegrationJob:
    """Mark the local read model stale and enqueue one idempotent ERP upsert."""
    work_order.erp_sync_status = "PENDING"
    work_order.erp_sync_error = None
    return enqueue_erp_job(
        db,
        aggregate_type="WORK_ORDER",
        aggregate_id=work_order.id,
        operation="UPSERT_SERVICE_ORDER",
        idempotency_key=f"work-order:projection:{work_order.id}:{change_key}"[:128],
        payload={"work_order_number": work_order.number, "change_key": change_key},
    )


def confirm_work_order_projection(db: Session, job: ErpIntegrationJob) -> None:
    """In strict runtime, do not report a successful write before ERP confirms it."""
    settings = get_settings()
    if not settings.frappe_required:
        return
    from app.services.erp_sync import process_erp_jobs

    process_erp_jobs(db, settings, limit=1, job_ids={job.id})
    db.refresh(job)
    if job.status != "SYNCED" or not job.target_reference:
        raise HTTPException(
            status_code=503,
            detail="ERPNext no confirmo la OT; el cambio quedo auditado para reintento",
        )


def create_work_order(db: Session, data: WorkOrderCreate) -> WorkOrder:
    actor = audit_actor(data.actor)
    organization_id = current_identity().organization_id
    customer = db.scalar(select(Customer).where(
        Customer.id == data.customer_id, Customer.organization_id == organization_id
    ))
    vehicle = db.scalar(select(Vehicle).where(
        Vehicle.id == data.vehicle_id, Vehicle.organization_id == organization_id
    ))
    if not customer:
        raise HTTPException(status_code=422, detail="Customer does not exist")
    if not vehicle or vehicle.customer_id != customer.id:
        raise HTTPException(status_code=422, detail="Vehicle does not belong to the customer")
    work_order = WorkOrder(
        organization_id=organization_id,
        branch_id=operational_branch_id(db),
        number=data.number or _next_number(db, organization_id),
        customer_id=data.customer_id,
        vehicle_id=data.vehicle_id,
        status=WorkOrderStatus.CREATED.value,
        title=data.title.strip(),
        concern=data.concern.strip(),
        assigned_technicians=data.assigned_technicians,
        bay_code=data.bay_code,
        promised_at=data.promised_at,
    )
    event = WorkOrderEvent(
        organization_id=organization_id,
        work_order=work_order,
        event_type="WORK_ORDER_CREATED",
        from_status=None,
        to_status=WorkOrderStatus.CREATED.value,
        actor=actor,
        reason="Orden de trabajo creada",
        idempotency_key=f"create:{work_order.number}",
        payload={},
    )
    db.add_all(
        [
            work_order,
            event,
            FlowEvent(
                organization_id=organization_id,
                module="WORK_ORDER",
                action="WORK_ORDER_CREATED",
                item_reference=work_order.number,
                actor=actor,
                result="SUCCESS",
                metadata_json={"status": WorkOrderStatus.CREATED.value},
            ),
        ]
    )
    db.flush()
    job = enqueue_erp_job(
        db,
        aggregate_type="WORK_ORDER",
        aggregate_id=work_order.id,
        operation="UPSERT_SERVICE_ORDER",
        idempotency_key=f"work-order:create:{work_order.id}",
        payload={
            "work_order_number": work_order.number,
            "customer_id": work_order.customer_id,
            "vehicle_id": work_order.vehicle_id,
            "status": work_order.status,
            "title": work_order.title,
            "concern": work_order.concern,
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Work order number already exists") from exc
    confirm_work_order_projection(db, job)
    return get_work_order(db, work_order.id)


def update_work_order(db: Session, work_order_id: str, data: WorkOrderUpdate) -> WorkOrder:
    work_order = get_work_order(db, work_order_id)
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(work_order, field, value)
    digest = hashlib.sha256(
        json.dumps(changes, sort_keys=True, default=str).encode()
    ).hexdigest()[:20]
    job = queue_work_order_projection(db, work_order, change_key=f"update:{digest}")
    db.commit()
    confirm_work_order_projection(db, job)
    return get_work_order(db, work_order_id)


def reconcile_work_order(
    db: Session,
    work_order_id: str,
    *,
    client: FrappeReadClient | None = None,
) -> WorkOrder:
    """Refresh the operational read model from the authoritative ERP document."""
    work_order = get_work_order(db, work_order_id)
    client = client or FrappeReadClient(get_settings())
    source = client.get_service_order_by_external_reference(work_order.number)
    if source is None:
        raise HTTPException(status_code=409, detail="La Service Order no existe en ERPNext")
    source_state = str(source.get("sd_workflow_state") or "").strip()
    try:
        normalized_state = WorkOrderStatus(source_state).value
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="ERPNext devolvio un estado de OT no soportado") from exc
    previous = work_order.status
    work_order.status = normalized_state
    work_order.title = str(source.get("title") or work_order.title)
    work_order.concern = str(source.get("preference_note") or work_order.concern)
    work_order.diagnosis = str(source.get("sd_platform_diagnosis") or "") or None
    technicians = str(source.get("sd_platform_assigned_technicians") or "")
    work_order.assigned_technicians = [item.strip() for item in technicians.splitlines() if item.strip()]
    work_order.bay_code = str(source.get("sd_platform_bay_code") or "") or None
    try:
        parts = json.loads(source.get("sd_platform_parts_json") or "[]")
        if isinstance(parts, list):
            work_order.parts_required = parts
    except (TypeError, ValueError):
        pass
    work_order.erpnext_service_order_id = str(source["name"])
    work_order.erp_sync_status = "SYNCED"
    work_order.erp_sync_error = None
    work_order.erp_last_synced_at = datetime.now(UTC)
    modified = str(source.get("modified") or "unknown")
    key = hashlib.sha256(f"{work_order.id}:{modified}".encode()).hexdigest()[:24]
    existing = db.scalar(select(WorkOrderEvent.id).where(
        WorkOrderEvent.work_order_id == work_order.id,
        WorkOrderEvent.idempotency_key == f"erp-reconcile:{key}",
    ))
    if existing is None:
        work_order.events.append(WorkOrderEvent(
            event_type="ERP_RECONCILED", from_status=previous, to_status=normalized_state,
            actor="erpnext", reason="Proyeccion actualizada desde Service Order autoritativa",
            idempotency_key=f"erp-reconcile:{key}",
            payload={"erpnext_service_order_id": work_order.erpnext_service_order_id, "erp_modified": modified},
        ))
        db.add(FlowEvent(module="WORK_ORDER", action="ERP_RECONCILED",
                         item_reference=work_order.number, actor="erpnext", result="SUCCESS",
                         metadata_json={"erp_modified": modified, "from_status": previous, "to_status": normalized_state}))
    db.commit()
    return get_work_order(db, work_order_id)


def transition(db: Session, work_order_id: str, data: WorkOrderTransition) -> WorkOrder:
    actor = audit_actor(data.actor)
    existing_event = db.scalar(
        select(WorkOrderEvent).where(
            WorkOrderEvent.organization_id == current_identity().organization_id,
            WorkOrderEvent.work_order_id == work_order_id,
            WorkOrderEvent.idempotency_key == data.idempotency_key,
        )
    )
    if existing_event:
        return get_work_order(db, work_order_id)

    work_order = db.scalar(select(WorkOrder).where(
        WorkOrder.id == work_order_id,
        WorkOrder.organization_id == current_identity().organization_id,
    ).with_for_update())
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    if data.to_status == WorkOrderStatus.READY_TO_INVOICE.value:
        event_types = {event.event_type for event in db.scalars(select(WorkOrderEvent).where(
            WorkOrderEvent.work_order_id == work_order.id
        ))}
        blockers: list[str] = []
        if "VEHICLE_CHECK_IN_COMPLETED" not in event_types:
            blockers.append("ingreso 360")
        if "QUALITY_CONTROL_PASS" not in event_types:
            blockers.append("control de calidad aprobado")
        timer_events = list(db.scalars(select(WorkOrderEvent).where(
            WorkOrderEvent.work_order_id == work_order.id,
            WorkOrderEvent.event_type.like("WORK_TIMER_%"),
        ).order_by(WorkOrderEvent.created_at)))
        if timer_events and timer_events[-1].event_type != "WORK_TIMER_STOP":
            blockers.append("cronómetro detenido")
        pending_parts = [part for part in work_order.parts_required or []
                         if part.get("status") not in {"DELIVERED", "RECEIVED", "RETURNED"}]
        if pending_parts:
            blockers.append("repuestos entregados o devueltos")
        if blockers:
            raise HTTPException(status_code=409, detail="Faltan controles: " + ", ".join(blockers))
    try:
        decision = transition_work_order(
            current_status=WorkOrderStatus(work_order.status),
            requested_status=WorkOrderStatus(data.to_status),
            actor=actor,
            reason=data.reason,
            invoice_reference=data.invoice_reference,
            idempotency_key=data.idempotency_key,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    verification: dict[str, object] | None = None
    if decision.next_status == WorkOrderStatus.INVOICED and decision.invoice_reference:
        verification = verify_invoice_reference(
            invoice_reference=decision.invoice_reference, settings=get_settings()
        )

    work_order.status = decision.next_status.value
    if decision.invoice_reference:
        work_order.invoice_reference = decision.invoice_reference
        work_order.erpnext_invoice_id = decision.invoice_reference
    event = WorkOrderEvent(
        work_order_id=work_order.id,
        event_type="WORK_ORDER_STATUS_CHANGED",
        from_status=decision.previous_status.value,
        to_status=decision.next_status.value,
        actor=decision.actor,
        reason=decision.reason,
        idempotency_key=decision.idempotency_key,
        payload={
            "invoice_reference": decision.invoice_reference,
            "erpnext_verification": verification,
        },
        created_at=decision.occurred_at,
    )
    db.add_all(
        [
            event,
            FlowEvent(
                module="WORK_ORDER",
                action="STATUS_CHANGED",
                item_reference=work_order.number,
                actor=decision.actor,
                result="SUCCESS",
                metadata_json={
                    "from_status": decision.previous_status.value,
                    "to_status": decision.next_status.value,
                },
                created_at=decision.occurred_at,
            ),
        ]
    )
    work_order.erp_sync_status = "PENDING"
    work_order.erp_sync_error = None
    job = enqueue_erp_job(
        db,
        aggregate_type="WORK_ORDER",
        aggregate_id=work_order.id,
        operation="TRANSITION_SERVICE_ORDER",
        idempotency_key=f"work-order:transition:{work_order.id}:{decision.idempotency_key}",
        payload={
            "work_order_number": work_order.number,
            "erpnext_service_order_id": work_order.erpnext_service_order_id,
            "from_status": decision.previous_status.value,
            "to_status": decision.next_status.value,
            "reason": decision.reason,
            "invoice_reference": decision.invoice_reference,
        },
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    else:
        confirm_work_order_projection(db, job)
    return get_work_order(db, work_order_id)
