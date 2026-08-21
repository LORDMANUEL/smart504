from __future__ import annotations

import uuid
import hashlib
from decimal import Decimal
from datetime import UTC, datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError
from smartdiag_domain.work_orders import WorkOrderStatus, status_label
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.db import get_db
from app.config import get_settings
from app.models import (
    Booking,
    CatalogProduct,
    Customer,
    FlowEvent,
    LaborCatalogItem,
    StaffCompensationProfile,
    StaffUser,
    Vehicle,
    WorkOrder,
    WorkOrderEvent,
    WorkOrderLaborEntry,
)
from app.request_context import audit_actor, current_identity
from app.services.media import read_private_evidence, store_private_evidence
from app.schemas import (
    BookingAdminRead,
    BookingCreate,
    BookingStatusUpdate,
    CustomerCreate,
    CustomerRead,
    VehicleCreate,
    VehicleRead,
    WorkOrderBoardColumn,
    WorkOrderCreate,
    WorkOrderLaborCreate,
    WorkOrderLaborRead,
    WorkOrderCheckInCreate,
    WorkOrderTimerAction,
    WorkOrderQualityCreate,
    LaborCatalogRead,
    WorkOrderPartDelivery,
    WorkOrderPartRequestCreate,
    WorkOrderPartStatusUpdate,
    WorkOrderRead,
    WorkOrderTransition,
    WorkOrderUpdate,
)

from app.services.work_orders import (
    create_work_order,
    confirm_work_order_projection,
    get_work_order,
    queue_work_order_projection,
    reconcile_work_order,
    transition,
    update_work_order,
)
from app.services.branch_scope import operational_branch_id

router = APIRouter(
    prefix="/api/v1/operations",
    tags=["operations"],
    dependencies=[Depends(require_admin)],
)


def _require_operational_role(
    principal: StaffUser | None,
    allowed: set[str],
    detail: str,
) -> None:
    """Enforce segregation of duties after the permission-level gate."""
    if principal is not None and principal.role not in allowed:
        raise HTTPException(status_code=403, detail=detail)


def _append_operational_event(
    db: Session, work_order: WorkOrder, *, event_type: str, actor: str,
    reason: str, payload: dict[str, object], key: str,
) -> WorkOrder:
    work_order.events.append(WorkOrderEvent(
        event_type=event_type, from_status=work_order.status, to_status=work_order.status,
        actor=actor, reason=reason, idempotency_key=key, payload=payload,
    ))
    db.add(FlowEvent(module="WORK_ORDER", action=event_type,
                     item_reference=work_order.number, actor=actor,
                     result="SUCCESS", metadata_json=payload))
    job = queue_work_order_projection(db, work_order, change_key=key)
    db.commit()
    confirm_work_order_projection(db, job)
    return get_work_order(db, work_order.id)


@router.post("/work-orders/{work_order_id}/check-in", response_model=WorkOrderRead)
def register_work_order_check_in(
    work_order_id: str, data: WorkOrderCheckInCreate,
    principal: StaffUser | None = Depends(require_admin), db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(principal, {"OWNER", "ADMIN", "MANAGER", "RECEPTION"},
                              "Solo recepción puede completar el ingreso 360")
    if not data.customer_accepted:
        raise HTTPException(status_code=422, detail="El cliente debe aceptar el registro de ingreso")
    work_order = get_work_order(db, work_order_id)
    actor = audit_actor(data.actor)
    payload = data.model_dump(exclude={"actor"}) | {"accepted_at": datetime.now(UTC).isoformat()}
    return _append_operational_event(db, work_order, event_type="VEHICLE_CHECK_IN_COMPLETED",
        actor=actor, reason="Ingreso 360 aceptado por el cliente", payload=payload,
        key=f"check-in:{work_order.id}")


@router.post("/work-orders/{work_order_id}/timer", response_model=WorkOrderRead)
def update_work_order_timer(
    work_order_id: str, data: WorkOrderTimerAction,
    principal: StaffUser | None = Depends(require_admin), db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(principal, {"OWNER", "ADMIN", "MANAGER", "TECHNICIAN"},
                              "Solo el equipo técnico puede registrar tiempo")
    work_order = get_work_order(db, work_order_id)
    actor = audit_actor(data.actor)
    timer_events = [event for event in work_order.events if event.event_type.startswith("WORK_TIMER_")]
    current = timer_events[-1].event_type.removeprefix("WORK_TIMER_") if timer_events else "STOPPED"
    allowed = {"STOPPED": {"START"}, "START": {"PAUSE", "STOP"},
               "RESUME": {"PAUSE", "STOP"}, "PAUSE": {"RESUME", "STOP"}}
    if data.action not in allowed.get(current, set()):
        raise HTTPException(status_code=409, detail=f"Acción {data.action} no permitida desde {current}")
    now = datetime.now(UTC)
    payload: dict[str, object] = {"action": data.action, "occurred_at": now.isoformat(), "note": data.note}
    if data.action == "STOP":
        elapsed = 0
        active_since: datetime | None = None
        for event in timer_events:
            occurred = event.created_at if event.created_at.tzinfo else event.created_at.replace(tzinfo=UTC)
            state = event.event_type.removeprefix("WORK_TIMER_")
            if state in {"START", "RESUME"}: active_since = occurred
            elif state in {"PAUSE", "STOP"} and active_since:
                elapsed += max(0, int((occurred - active_since).total_seconds())); active_since = None
        if active_since: elapsed += max(0, int((now - active_since).total_seconds()))
        payload["elapsed_seconds"] = elapsed
    return _append_operational_event(db, work_order, event_type=f"WORK_TIMER_{data.action}",
        actor=actor, reason=data.note or f"Cronómetro {data.action.lower()}", payload=payload,
        key=f"timer:{work_order.id}:{data.action}:{uuid.uuid4()}")


@router.post("/work-orders/{work_order_id}/quality", response_model=WorkOrderRead)
def register_work_order_quality(
    work_order_id: str, data: WorkOrderQualityCreate,
    principal: StaffUser | None = Depends(require_admin), db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(principal, {"OWNER", "ADMIN", "MANAGER"},
                              "El técnico que ejecuta no puede autoaprobar calidad")
    if data.result == "PASS" and not all(data.checklist.values()):
        raise HTTPException(status_code=422, detail="No puede aprobar calidad con controles pendientes")
    if data.road_test_required and data.road_test_result != data.result:
        raise HTTPException(status_code=422, detail="El resultado de prueba de ruta no coincide")
    work_order = get_work_order(db, work_order_id)
    actor = audit_actor(data.actor)
    payload = data.model_dump(exclude={"actor"}) | {"inspected_at": datetime.now(UTC).isoformat()}
    return _append_operational_event(db, work_order, event_type=f"QUALITY_CONTROL_{data.result}",
        actor=actor, reason=data.notes or f"Control de calidad {data.result}", payload=payload,
        key=f"quality:{work_order.id}:{uuid.uuid4()}")


@router.get("/labor-catalog", response_model=list[LaborCatalogRead])
def list_labor_catalog(
    vehicle_id: str | None = Query(default=None), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    """Return active tenant services without exposing their internal cost."""
    identity = current_identity()
    vehicle = db.get(Vehicle, vehicle_id) if vehicle_id else None
    if vehicle_id and (vehicle is None or vehicle.organization_id != identity.organization_id):
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    items = db.scalars(
        select(LaborCatalogItem)
        .where(
            LaborCatalogItem.organization_id == identity.organization_id,
            LaborCatalogItem.is_active.is_(True),
        )
        .order_by(LaborCatalogItem.code)
    ).all()

    def compatible(item: LaborCatalogItem) -> bool:
        if vehicle is None or not item.vehicle_rules:
            return True
        for rule in item.vehicle_rules:
            make = str(rule.get("make") or "").casefold()
            model = str(rule.get("model") or "").casefold()
            year_from = int(rule.get("year_from") or 0)
            year_to = int(rule.get("year_to") or 9999)
            if (
                (not make or make == vehicle.make.casefold())
                and (not model or model == vehicle.model.casefold())
                and year_from <= (vehicle.model_year or 0) <= year_to
            ):
                return True
        return False

    return [
        {
            "code": item.code,
            "description": item.description,
            "hours": item.standard_hours,
            "price": item.sale_price,
        }
        for item in items
        if compatible(item)
    ]


def _evidence_payloads(work_order: WorkOrder) -> list[dict[str, object]]:
    return [
        {key: value for key, value in dict(event.payload).items() if key != "storage_key"}
        for event in work_order.events
        if event.event_type == "DIAGNOSTIC_EVIDENCE_ADDED"
    ]


def _evidence_event(work_order: WorkOrder, evidence_id: str) -> WorkOrderEvent:
    for event in work_order.events:
        if (
            event.event_type == "DIAGNOSTIC_EVIDENCE_ADDED"
            and event.payload.get("id") == evidence_id
        ):
            return event
    raise HTTPException(status_code=404, detail="Evidencia no encontrada")


@router.get("/work-orders/{work_order_id}/evidence")
def list_work_order_evidence(
    work_order_id: str, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    return _evidence_payloads(get_work_order(db, work_order_id))


@router.get("/work-orders/{work_order_id}/evidence/{evidence_id}/content")
def read_work_order_evidence(
    work_order_id: str, evidence_id: str, db: Session = Depends(get_db)
) -> Response:
    work_order = get_work_order(db, work_order_id)
    event = _evidence_event(work_order, evidence_id)
    storage_key = str(event.payload.get("storage_key") or "")
    if not storage_key:
        raise HTTPException(status_code=404, detail="Archivo de evidencia no disponible")
    settings = get_settings()
    headers = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
    if event.payload.get("storage_backend") == "s3":
        return Response(
            read_private_evidence(object_key=storage_key, settings=settings),
            media_type=str(event.payload.get("mime_type") or "application/octet-stream"),
            headers=headers,
        )
    if "/" in storage_key or "\\" in storage_key:
        raise HTTPException(status_code=404, detail="Archivo de evidencia no disponible")
    path = settings.private_evidence_root / work_order.id / storage_key
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Archivo de evidencia no disponible")
    return FileResponse(
        path,
        media_type=str(event.payload.get("mime_type") or "application/octet-stream"),
        headers=headers,
    )


@router.get("/work-orders/{work_order_id}/labor-entries", response_model=list[WorkOrderLaborRead])
def list_work_order_labor(work_order_id: str, db: Session = Depends(get_db)) -> list[WorkOrderLaborEntry]:
    get_work_order(db, work_order_id)
    return list(
        db.scalars(
            select(WorkOrderLaborEntry)
            .where(WorkOrderLaborEntry.work_order_id == work_order_id)
            .order_by(WorkOrderLaborEntry.created_at)
        )
    )


@router.post(
    "/work-orders/{work_order_id}/labor-entries",
    response_model=WorkOrderLaborRead,
    status_code=status.HTTP_201_CREATED,
)
def record_work_order_labor(
    work_order_id: str,
    data: WorkOrderLaborCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrderLaborEntry:
    if principal is not None and principal.role not in {"OWNER", "ADMIN", "MANAGER", "TECHNICIAN"}:
        raise HTTPException(status_code=403, detail="Solo taller o gerencia puede registrar mano de obra")
    work_order = get_work_order(db, work_order_id)
    identity = current_identity()
    catalog_item = db.scalar(
        select(LaborCatalogItem).where(
            LaborCatalogItem.organization_id == identity.organization_id,
            LaborCatalogItem.code == data.service_code.upper(),
            LaborCatalogItem.is_active.is_(True),
        )
    )
    if catalog_item is None:
        raise HTTPException(status_code=422, detail="Seleccione una mano de obra activa del catalogo")
    technician = db.get(StaffUser, data.technician_id)
    if (
        technician is None
        or technician.organization_id != identity.organization_id
        or work_order.organization_id != identity.organization_id
        or not technician.is_active
        or technician.role != "TECHNICIAN"
    ):
        raise HTTPException(status_code=422, detail="Seleccione un tecnico activo")
    profile = db.scalar(
        select(StaffCompensationProfile).where(
            StaffCompensationProfile.staff_user_id == data.technician_id
        )
    )
    if profile is None:
        raise HTTPException(status_code=409, detail="El tecnico no tiene configuracion de costos y tarifas")
    hourly_cost = profile.hourly_cost(data.rate_kind)
    hourly_sale_rate = (
        profile.specialized_sale_rate if data.rate_kind == "SPECIALIZED" else profile.standard_sale_rate
    )
    if hourly_sale_rate < hourly_cost:
        raise HTTPException(status_code=409, detail="La tarifa de venta quedo bajo el costo real por hora")
    actual_actor = audit_actor(data.actor)
    entry = WorkOrderLaborEntry(
        organization_id=technician.organization_id,
        work_order_id=work_order.id,
        technician_user_id=technician.id,
        technician_name=technician.full_name,
        service_code=data.service_code.upper(),
        description=catalog_item.description,
        rate_kind=data.rate_kind,
        hours=catalog_item.standard_hours,
        hourly_cost_snapshot=hourly_cost,
        hourly_sale_rate=hourly_sale_rate,
        actor=actual_actor,
    )
    db.add(entry)
    db.flush()
    work_order.events.append(
        WorkOrderEvent(
            event_type="LABOR_RECORDED",
            from_status=work_order.status,
            to_status=work_order.status,
            actor=actual_actor,
            reason=f"{catalog_item.description}: {catalog_item.standard_hours} horas",
            idempotency_key=f"labor:{entry.id}",
            payload={
                "labor_entry_id": entry.id,
                "technician": technician.full_name,
                "service_code": entry.service_code,
                "rate_kind": entry.rate_kind,
                "hours": str(entry.hours),
                "sale_total": str(entry.sale_total),
            },
        )
    )
    db.add(
        FlowEvent(
            module="WORK_ORDER",
            action="LABOR_RECORDED",
            item_reference=work_order.number,
            actor=actual_actor,
            result="SUCCESS",
            metadata_json={"labor_entry_id": entry.id, "hours": str(entry.hours)},
        )
    )
    job = queue_work_order_projection(db, work_order, change_key=f"labor:{entry.id}")
    db.commit()
    confirm_work_order_projection(db, job)
    db.refresh(entry)
    return entry


@router.post("/work-orders/{work_order_id}/evidence", status_code=status.HTTP_201_CREATED)
async def upload_work_order_evidence(
    work_order_id: str,
    category: str = Form(..., pattern=r"^(DIAGNOSIS|PART|DAMAGE|BEFORE|AFTER|QUALITY)$"),
    caption: str = Form(..., min_length=3, max_length=500),
    actor: str = Form(..., min_length=2, max_length=120),
    file: UploadFile = File(...),
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "TECHNICIAN"},
        "Solo el equipo tecnico puede registrar evidencia",
    )
    work_order = get_work_order(db, work_order_id)
    actual_actor = audit_actor(actor)
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Use JPG, PNG o WebP")
    raw = await file.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La imagen supera 8 MB")
    try:
        with Image.open(BytesIO(raw)) as image:
            image.verify()
        with Image.open(BytesIO(raw)) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise HTTPException(status_code=422, detail="La imagen no es valida") from exc
    if width > 12000 or height > 12000 or width * height > 40_000_000:
        raise HTTPException(status_code=422, detail="Las dimensiones de la imagen no son seguras")
    evidence_id = str(uuid.uuid4())
    digest = hashlib.sha256(raw).hexdigest()[:16]
    settings = get_settings()
    filename = f"{evidence_id}-{digest}{allowed[file.content_type]}"
    storage_backend = settings.private_evidence_backend.lower()
    if storage_backend == "s3":
        storage_key = f"evidence/{work_order.organization_id}/{work_order.id}/{filename}"
        store_private_evidence(
            content=raw,
            object_key=storage_key,
            mime_type=file.content_type,
            sha256=hashlib.sha256(raw).hexdigest(),
            settings=settings,
        )
    else:
        folder = settings.private_evidence_root / work_order.id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / filename).write_bytes(raw)
        storage_key = filename
    payload: dict[str, object] = {
        "id": evidence_id,
        "category": category,
        "caption": caption.strip(),
        "actor": actual_actor,
        "media_url": f"/api/v1/operations/work-orders/{work_order.id}/evidence/{evidence_id}/content",
        "storage_key": storage_key,
        "storage_backend": storage_backend,
        "mime_type": file.content_type,
        "created_at": datetime.now(UTC).isoformat(),
    }
    work_order.events.append(
        WorkOrderEvent(
            event_type="DIAGNOSTIC_EVIDENCE_ADDED",
            from_status=work_order.status,
            to_status=work_order.status,
            actor=actual_actor,
            reason=caption.strip(),
            idempotency_key=f"evidence:{evidence_id}",
            payload=payload,
        )
    )
    db.add(
        FlowEvent(
            module="WORK_ORDER",
            action="DIAGNOSTIC_EVIDENCE_ADDED",
            item_reference=work_order.number,
            actor=actual_actor,
            result="SUCCESS",
            metadata_json={"evidence_id": evidence_id, "category": category},
        )
    )
    job = queue_work_order_projection(db, work_order, change_key=f"evidence:{evidence_id}")
    db.commit()
    confirm_work_order_projection(db, job)
    return {key: value for key, value in payload.items() if key != "storage_key"}


@router.get("/bookings", response_model=list[BookingAdminRead])
def list_bookings(db: Session = Depends(get_db)) -> list[Booking]:
    return list(db.scalars(select(Booking).where(
        Booking.organization_id == current_identity().organization_id
    ).order_by(Booking.created_at.desc())))


@router.post("/bookings", response_model=BookingAdminRead, status_code=status.HTTP_201_CREATED)
def create_internal_booking(
    data: BookingCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Booking:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "RECEPTION"},
        "Solo recepcion o gerencia puede crear citas internas",
    )
    actor = audit_actor(principal.email if principal is not None else "recepcion")
    booking = Booking(**data.model_dump(), organization_id=current_identity().organization_id,
                      branch_id=operational_branch_id(db),
                      source="KANBAN", status="CONFIRMED")
    db.add(booking)
    db.flush()
    db.add(FlowEvent(module="RECEPTION", action="BOOKING_CREATED_FROM_KANBAN", item_reference=booking.id, actor=actor, result="SUCCESS", metadata_json={"vehicle": booking.vehicle_summary, "service": booking.service_requested}))
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/bookings/{booking_id}", response_model=BookingAdminRead)
def update_booking_status(
    booking_id: str,
    data: BookingStatusUpdate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Booking:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "RECEPTION"},
        "Solo recepcion o gerencia puede cambiar citas",
    )
    booking = db.scalar(select(Booking).where(
        Booking.id == booking_id,
        Booking.organization_id == current_identity().organization_id,
    ))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = data.status
    actual_actor = audit_actor(data.actor)
    db.add(
        FlowEvent(
            module="RECEPTION",
            action=f"BOOKING_{data.status}",
            item_reference=booking.id,
            actor=actual_actor,
            result="CANCELLED" if data.status == "CANCELLED" else "SUCCESS",
            metadata_json={
                "vehicle": booking.vehicle_summary,
                "service": booking.service_requested,
            },
        )
    )
    if booking.email:
        db.add(
            FlowEvent(
                module="NOTIFICATIONS",
                action=f"BOOKING_{data.status}",
                item_reference=booking.id,
                actor=actual_actor,
                result="SUCCESS",
                metadata_json={
                    "recipient": booking.email,
                    "channel": "PORTAL",
                    "delivery_status": "DELIVERED",
                    "title": f"Estado de cita: {data.status}",
                    "message": f"Su solicitud para {booking.service_requested} cambio a {data.status}.",
                },
            )
        )
    db.commit()
    db.refresh(booking)
    return booking


@router.post("/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Customer:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "RECEPTION"},
        "Solo recepcion o gerencia puede crear clientes del taller",
    )
    customer = Customer(**data.model_dump(), organization_id=current_identity().organization_id)
    db.add(customer)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Customer could not be created") from exc
    db.refresh(customer)
    return customer


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)) -> list[Customer]:
    return list(db.scalars(select(Customer).where(
        Customer.organization_id == current_identity().organization_id
    ).order_by(Customer.full_name)))


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Vehicle:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "RECEPTION"},
        "Solo recepcion o gerencia puede crear vehiculos",
    )
    organization_id = current_identity().organization_id
    if db.scalar(select(Customer.id).where(
        Customer.id == data.customer_id, Customer.organization_id == organization_id
    )) is None:
        raise HTTPException(status_code=422, detail="Customer does not exist")
    vehicle = Vehicle(**data.model_dump(), organization_id=organization_id)
    if vehicle.vin:
        vehicle.vin = vehicle.vin.strip().upper()
    if vehicle.plate:
        vehicle.plate = vehicle.plate.strip().upper()
    db.add(vehicle)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="VIN already exists") from exc
    db.refresh(vehicle)
    return vehicle


@router.get("/vehicles", response_model=list[VehicleRead])
def list_vehicles(
    customer_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[Vehicle]:
    statement = select(Vehicle).where(
        Vehicle.organization_id == current_identity().organization_id
    ).order_by(Vehicle.make, Vehicle.model)
    if customer_id:
        statement = statement.where(Vehicle.customer_id == customer_id)
    return list(db.scalars(statement))


@router.post("/work-orders", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_ot(
    data: WorkOrderCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "RECEPTION"},
        "Solo recepcion o gerencia puede abrir una OT",
    )
    return create_work_order(
        db, data.model_copy(update={"actor": audit_actor(data.actor)})
    )


@router.get("/work-orders", response_model=list[WorkOrderRead])
def list_work_orders(
    current_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[WorkOrder]:
    statement = (
        select(WorkOrder)
        .where(WorkOrder.organization_id == current_identity().organization_id)
        .options(selectinload(WorkOrder.events))
        .order_by(WorkOrder.updated_at.desc())
    )
    if current_status:
        try:
            normalized = WorkOrderStatus(current_status).value
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Unknown work-order status") from exc
        statement = statement.where(WorkOrder.status == normalized)
    return list(db.scalars(statement).unique())


@router.get("/work-orders/board", response_model=list[WorkOrderBoardColumn])
def work_order_board(db: Session = Depends(get_db)) -> list[WorkOrderBoardColumn]:
    work_orders = list(
        db.scalars(
            select(WorkOrder)
            .where(WorkOrder.organization_id == current_identity().organization_id)
            .options(selectinload(WorkOrder.events))
            .order_by(WorkOrder.updated_at.desc())
        ).unique()
    )
    return [
        WorkOrderBoardColumn(
            status=work_order_status.value,
            label=status_label(work_order_status),
            work_orders=[item for item in work_orders if item.status == work_order_status.value],
        )
        for work_order_status in WorkOrderStatus
    ]


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderRead)
def read_work_order(work_order_id: str, db: Session = Depends(get_db)) -> WorkOrder:
    return get_work_order(db, work_order_id)


@router.patch("/work-orders/{work_order_id}", response_model=WorkOrderRead)
def patch_work_order(
    work_order_id: str,
    data: WorkOrderUpdate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "TECHNICIAN"},
        "Solo el equipo tecnico puede editar el diagnostico de la OT",
    )
    return update_work_order(db, work_order_id, data)


@router.post("/work-orders/{work_order_id}/reconcile", response_model=WorkOrderRead)
def reconcile_ot(
    work_order_id: str,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrder:
    """Pull the authoritative Service Order back into the operational projection."""
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER"},
        "Solo gerencia puede conciliar una OT con ERP",
    )
    return reconcile_work_order(db, work_order_id)


@router.post("/work-orders/{work_order_id}/transitions", response_model=WorkOrderRead)
def transition_ot(
    work_order_id: str,
    data: WorkOrderTransition,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "RECEPTION", "TECHNICIAN"},
        "Su rol no puede cambiar el estado general de una OT",
    )
    return transition(
        db, work_order_id, data.model_copy(update={"actor": audit_actor(data.actor)})
    )


@router.post(
    "/work-orders/{work_order_id}/part-requests",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
)
def request_work_order_part(
    work_order_id: str,
    data: WorkOrderPartRequestCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "TECHNICIAN"},
        "Solo el equipo tecnico puede solicitar repuestos",
    )
    work_order = get_work_order(db, work_order_id)
    product = db.get(CatalogProduct, data.product_id)
    if product is None or not product.active:
        raise HTTPException(status_code=422, detail="Catalog product does not exist")
    requested_at = datetime.now(UTC)
    actual_actor = audit_actor(data.actor)
    request_id = str(uuid.uuid4())
    request_payload: dict[str, object] = {
        "request_id": request_id,
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "quantity": data.quantity,
        "note": data.note or "",
        "status": "REQUESTED",
        "actor": actual_actor,
        "requested_at": requested_at.isoformat(),
        "stock_status": product.stock_status,
        "location": "Por asignar en bodega",
    }
    work_order.parts_required = [*(work_order.parts_required or []), request_payload]
    work_order.events.append(
        WorkOrderEvent(
            event_type="PART_REQUESTED",
            from_status=work_order.status,
            to_status=work_order.status,
            actor=actual_actor,
            reason=data.note or f"Solicitud de {product.sku}",
            idempotency_key=f"part:{request_id}",
            payload=request_payload,
        )
    )
    db.add(
        FlowEvent(
            module="TECHNICIAN",
            action="PART_REQUESTED",
            item_reference=work_order.number,
            actor=actual_actor,
            result="SUCCESS",
            metadata_json=request_payload,
        )
    )
    job = queue_work_order_projection(db, work_order, change_key=f"part-request:{request_id}")
    db.commit()
    confirm_work_order_projection(db, job)
    return get_work_order(db, work_order_id)


@router.patch(
    "/work-orders/{work_order_id}/part-requests/{request_id}/delivery",
    response_model=WorkOrderRead,
)
def deliver_work_order_part(
    work_order_id: str,
    request_id: str,
    data: WorkOrderPartDelivery,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkOrder:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "WAREHOUSE"},
        "Solo bodega puede entregar repuestos",
    )
    work_order = get_work_order(db, work_order_id)
    actual_actor = audit_actor(data.actor)
    updated_parts: list[dict[str, object]] = []
    delivered_part: dict[str, object] | None = None
    for part in work_order.parts_required or []:
        current = dict(part)
        if current.get("request_id") == request_id:
            if current.get("status") == "DELIVERED":
                raise HTTPException(status_code=409, detail="Part request was already delivered")
            current.update(
                {
                    "status": "DELIVERED",
                    "location": data.location,
                    "delivered_by": actual_actor,
                    "delivered_at": datetime.now(UTC).isoformat(),
                }
            )
            delivered_part = current
        updated_parts.append(current)
    if delivered_part is None:
        raise HTTPException(status_code=404, detail="Part request does not exist")

    work_order.parts_required = updated_parts
    work_order.events.append(
        WorkOrderEvent(
            event_type="PART_DELIVERED",
            from_status=work_order.status,
            to_status=work_order.status,
            actor=actual_actor,
            reason=f"Entrega desde {data.location}",
            idempotency_key=f"part-delivery:{request_id}",
            payload=delivered_part,
        )
    )
    db.add(
        FlowEvent(
            module="WAREHOUSE",
            action="PART_DELIVERED",
            item_reference=work_order.number,
            actor=actual_actor,
            result="SUCCESS",
            metadata_json=delivered_part,
        )
    )
    job = queue_work_order_projection(db, work_order, change_key=f"part-delivery:{request_id}")
    db.commit()
    confirm_work_order_projection(db, job)
    return get_work_order(db, work_order_id)


@router.patch("/work-orders/{work_order_id}/part-requests/{request_id}/status", response_model=WorkOrderRead)
def update_work_order_part_status(work_order_id: str, request_id: str, data: WorkOrderPartStatusUpdate,
                                  principal: StaffUser | None = Depends(require_admin),
                                  db: Session = Depends(get_db)) -> WorkOrder:
    _require_operational_role(
        principal,
        {"OWNER", "ADMIN", "MANAGER", "WAREHOUSE"},
        "Solo bodega puede cambiar el estado de un repuesto",
    )
    work_order = get_work_order(db, work_order_id)
    actual_actor = audit_actor(data.actor)
    transitions = {"REQUESTED": {"PICKING"}, "PICKING": {"READY", "REQUESTED"},
                   "READY": {"DELIVERED", "REQUESTED"}, "DELIVERED": {"RETURN_REQUESTED"},
                   "RETURN_REQUESTED": {"RETURNED"}, "RETURNED": {"RECEIVED"}, "RECEIVED": set()}
    updated: list[dict[str, object]] = []; found: dict[str, object] | None = None
    for part in work_order.parts_required or []:
        current = dict(part)
        if current.get("request_id") == request_id:
            previous = str(current.get("status", "REQUESTED"))
            if data.status != previous and data.status not in transitions.get(previous, set()):
                raise HTTPException(status_code=409, detail="Transicion de bodega no permitida")
            current.update({"status": data.status, "location": data.location, "warehouse_actor": actual_actor,
                            "warehouse_note": data.note or "", "status_updated_at": datetime.now(UTC).isoformat()})
            found = current
        updated.append(current)
    if found is None:
        raise HTTPException(status_code=404, detail="Solicitud de repuesto no encontrada")
    work_order.parts_required = updated
    work_order.events.append(WorkOrderEvent(event_type=f"PART_{data.status}", from_status=work_order.status,
        to_status=work_order.status, actor=actual_actor, reason=data.note or f"Bodega: {data.status}",
        idempotency_key=f"part-status:{request_id}:{data.status}", payload=found))
    db.add(FlowEvent(module="WAREHOUSE", action=f"PART_{data.status}", item_reference=work_order.number,
                     actor=actual_actor, result="SUCCESS", metadata_json=found))
    job = queue_work_order_projection(db, work_order, change_key=f"part-status:{request_id}:{data.status}")
    db.commit()
    confirm_work_order_projection(db, job)
    return get_work_order(db, work_order_id)
