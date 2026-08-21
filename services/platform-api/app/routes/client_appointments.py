from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Booking, ClientUser, Customer, FlowEvent, Vehicle
from app.client_auth import require_client
from app.schemas import ClientAppointmentCreate, ClientAppointmentRead
from app.services.notifications import enqueue_notification
from app.services.branch_scope import operational_branch_id

router = APIRouter(prefix="/api/v1/client-appointments", tags=["client-appointments"])
WORKSHOP_TZ = ZoneInfo("America/Tegucigalpa")
SLOT_TIMES = (time(8, 0), time(9, 30), time(11, 0), time(13, 30), time(15, 0))


@router.get("/availability")
def availability(
    day: date = Query(alias="date"),
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    slots = [datetime.combine(day, slot, WORKSHOP_TZ) for slot in SLOT_TIMES]
    reserved_values = db.scalars(
        select(Booking.scheduled_at).where(
            Booking.scheduled_at >= slots[0].astimezone(UTC),
            Booking.scheduled_at <= slots[-1].astimezone(UTC),
            Booking.status != "CANCELLED",
            Booking.source == "CLIENT_PORTAL",
            Booking.organization_id == client_user.organization_id,
        )
    )
    reserved = {
        (value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)).isoformat()
        for value in reserved_values
        if value is not None
    }
    return {
        "date": day.isoformat(),
        "slots": [
            {
                "starts_at": slot.isoformat(),
                "available": slot.astimezone(UTC).isoformat() not in reserved,
            }
            for slot in slots
        ],
    }


@router.get("", response_model=list[ClientAppointmentRead])
def list_client_appointments(
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> list[Booking]:
    return list(
        db.scalars(
            select(Booking)
            .where(Booking.customer_id == client_user.customer_id, Booking.source == "CLIENT_PORTAL")
            .order_by(Booking.scheduled_at.desc())
        )
    )


@router.post("", response_model=ClientAppointmentRead, status_code=status.HTTP_201_CREATED)
def create_client_appointment(
    data: ClientAppointmentCreate,
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> Booking:
    starts_at = data.scheduled_at
    customer = db.scalar(select(Customer).where(Customer.id == client_user.customer_id))
    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == data.vehicle_id, Vehicle.customer_id == client_user.customer_id
        )
    )
    if customer is None or vehicle is None:
        raise HTTPException(status_code=404, detail="Vehículo del cliente no encontrado")
    if starts_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="La fecha debe incluir zona horaria")
    local_start = starts_at.astimezone(WORKSHOP_TZ)
    if local_start.time().replace(tzinfo=None) not in SLOT_TIMES:
        raise HTTPException(
            status_code=422, detail="El horario no pertenece al calendario disponible"
        )
    if starts_at.astimezone(UTC) <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="La cita debe ser futura")
    conflict = db.scalar(
        select(Booking).where(
            Booking.scheduled_at == starts_at.astimezone(UTC),
            Booking.status != "CANCELLED",
            Booking.source == "CLIENT_PORTAL",
            Booking.organization_id == client_user.organization_id,
        )
    )
    if conflict:
        raise HTTPException(status_code=409, detail="El horario ya fue reservado")
    booking = Booking(
        full_name=customer.full_name,
        phone=customer.phone,
        email=client_user.email,
        customer_id=client_user.customer_id,
        vehicle_id=data.vehicle_id,
        vehicle_summary=data.vehicle_summary,
        service_requested=data.service_requested,
        preferred_date=local_start.date().isoformat(),
        scheduled_at=starts_at.astimezone(UTC),
        duration_minutes=90,
        concern=data.concern,
        status="CONFIRMED",
        source="CLIENT_PORTAL",
        branch_id=operational_branch_id(db),
    )
    db.add(booking)
    db.flush()
    db.add(
        FlowEvent(
            module="CLIENT_PORTAL",
            action="APPOINTMENT_CREATED",
            item_reference=booking.id,
            actor=f"client:{client_user.id}",
            result="SUCCESS",
            metadata_json={
                "vehicle_id": data.vehicle_id,
                "service": data.service_requested,
                "scheduled_at": starts_at.isoformat(),
            },
        )
    )
    message = f"Su cita para {data.service_requested} quedo confirmada para {local_start.isoformat()}."
    enqueue_notification(
        db,
        channel="EMAIL",
        recipient=client_user.email,
        subject="Cita confirmada - SmartDiag504",
        body_text=message,
        template_key="APPOINTMENT_CONFIRMED",
        aggregate_type="BOOKING",
        aggregate_id=booking.id,
        idempotency_key=f"booking:{booking.id}:confirmed:email",
        payload={"scheduled_at": local_start.isoformat()},
    )
    db.add(
        FlowEvent(
            module="NOTIFICATIONS",
            action="APPOINTMENT_CONFIRMED",
            item_reference=booking.id,
            actor="sistema",
            result="SUCCESS",
            metadata_json={
                "recipient": client_user.email,
                "channel": "EMAIL",
                "delivery_status": "PENDING",
                "title": "Cita confirmada",
                "message": message,
            },
        )
    )
    db.commit()
    db.refresh(booking)
    return booking
