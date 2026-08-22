from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.password import PasswordHelper
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import CatalogProduct, ClientUser, Customer, FlowEvent, Payment, Quote, Vehicle, VehicleHistoryEvent, WorkOrder
from app.client_auth import require_client
from app.schemas import ProductRead
from app.services.vehicle_fitment import compatible_products

router = APIRouter(prefix="/api/v1/client-portal", tags=["client-portal"])


class ClientVehicleCreate(BaseModel):
    vin: str = Field(min_length=11, max_length=40)
    plate: str | None = Field(default=None, max_length=30)
    make: str = Field(min_length=2, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    model_year: int = Field(ge=1900, le=2100)
    engine: str | None = Field(default=None, max_length=120)
    mileage_km: int = Field(default=0, ge=0)


class ClientProfileUpdate(BaseModel):
    full_name: str = Field(min_length=3, max_length=180)
    email: EmailStr
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    credit_requested: bool = False
    credit_amount: int | None = Field(default=None, ge=1000, le=1000000)
    new_password: str | None = Field(default=None, min_length=10, max_length=128)


def _profile(user: ClientUser) -> dict[str, object]:
    return {
        "full_name": user.full_name, "email": user.email, "notification_email": user.notification_email,
        "managed_email": user.managed_email, "mailbox_status": user.mailbox_status, "username": user.username,
        "mfa_enabled": user.mfa_enabled, "loyalty_enabled": user.loyalty_enabled,
        "loyalty_points": user.loyalty_points, "credit_requested": user.credit_requested,
        "credit_amount": f"{user.requested_credit_amount:.2f}" if user.requested_credit_amount is not None else None,
        "credit_status": user.credit_status,
    }


def _customer(db: Session, user: ClientUser) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.id == user.customer_id))
    if customer is None:
        raise HTTPException(status_code=409, detail="La cuenta no está vinculada a un cliente")
    return customer


def _vehicle_payload(vehicle: Vehicle, histories: list[VehicleHistoryEvent]) -> dict[str, object]:
    image_map = {
        ("Ford", "Escape", 2020): "/vehicles/ford-escape-2020.png",
        ("Ford", "F-150", 2020): "/vehicles/ford-f150-2020.png",
        ("Honda", "Civic", 2008): "/vehicles/honda-civic-2008.png",
    }
    vehicle_history = [event for event in histories if event.vehicle_id == vehicle.id or event.vin == vehicle.vin]
    return {
        "id": vehicle.id, "label": f"{vehicle.make} {vehicle.model} {vehicle.model_year or ''}".strip(),
        "make": vehicle.make, "model": vehicle.model, "model_year": vehicle.model_year,
        "engine": vehicle.engine, "plate": vehicle.plate, "vin": vehicle.vin,
        "mileage_km": vehicle.mileage_km or 0,
        "photo_url": vehicle.photo_url or image_map.get((vehicle.make, vehicle.model, vehicle.model_year)),
        "maintenance": {"status": "PRÓXIMO", "next_service_km": (vehicle.mileage_km or 0) + 800,
                        "oil_last_km": max(0, (vehicle.mileage_km or 0) - 4200), "oil_next_km": (vehicle.mileage_km or 0) + 800},
        "history": [{"id": item.id, "type": item.event_type, "reference": item.reference, "summary": item.summary,
                     "mileage_km": item.mileage_km, "date": item.created_at.isoformat()} for item in vehicle_history[:8]],
        "advice": ["Revise la presión de llantas cada 15 días.", "No posponga alertas de frenos o temperatura.",
                   "Use el aceite indicado para el motor y registre cada cambio."],
    }


@router.get("/dashboard")
def dashboard(client_user: ClientUser = Depends(require_client), db: Session = Depends(get_db)) -> dict[str, object]:
    customer = _customer(db, client_user)
    vehicles = list(db.scalars(select(Vehicle).where(Vehicle.customer_id == customer.id).order_by(Vehicle.created_at)))
    histories = list(db.scalars(select(VehicleHistoryEvent).where(VehicleHistoryEvent.vehicle_id.in_([v.id for v in vehicles])).order_by(VehicleHistoryEvent.created_at.desc()))) if vehicles else []
    work_orders = list(db.scalars(select(WorkOrder).where(WorkOrder.customer_id == customer.id).options(selectinload(WorkOrder.events))))
    order_ids = [item.id for item in work_orders]
    quote_scope = Quote.customer_id == customer.id
    if order_ids:
        quote_scope = or_(quote_scope, Quote.work_order_id.in_(order_ids))
    quotes = list(db.scalars(select(Quote).where(quote_scope).options(selectinload(Quote.lines)).order_by(Quote.created_at.desc())).unique())
    payments = list(db.scalars(select(Payment).where(Payment.work_order_id.in_(order_ids)).order_by(Payment.created_at.desc()))) if order_ids else []
    quote_items = [{
        "id": quote.id, "number": quote.number, "work_order_id": quote.work_order_id, "status": quote.status,
        "notes": quote.notes, "subtotal": str(quote.subtotal), "discount": str(quote.discount), "tax": str(quote.tax),
        "total": str(quote.total), "created_at": quote.created_at.isoformat(),
        "lines": [{"id": line.id, "code": line.code, "description": line.description, "quantity": str(line.quantity),
                   "unit_price": str(line.unit_price), "line_total": str(line.line_total), "approval_status": line.approval_status}
                  for line in quote.lines],
    } for quote in quotes]
    alerts = []
    for quote in quotes:
        pending = sum(1 for line in quote.lines if line.approval_status == "PENDING")
        if quote.status == "SENT" or pending:
            alerts.append({"id": quote.id, "kind": "APPROVAL", "title": f"{quote.number} espera su decisión",
                           "detail": f"{pending} conceptos por aprobar o rechazar", "status": quote.status, "quote_id": quote.id})
    alerts.append({"id": "maintenance", "kind": "MAINTENANCE", "title": "Revisión preventiva próxima",
                   "detail": "Revise frenos, aceite y niveles en los próximos 800 km.", "status": "PENDIENTE"})
    invoices = [{"number": wo.invoice_reference or payment.receipt_number, "work_order_id": wo.id, "total": str(payment.amount),
                 "created_at": payment.created_at.isoformat()} for payment in payments for wo in work_orders if wo.id == payment.work_order_id]
    notification_events = list(db.scalars(select(FlowEvent).where(FlowEvent.module == "NOTIFICATIONS").order_by(FlowEvent.created_at.desc()).limit(200)))
    notifications = [{"id": event.id, "event": event.action, "reference": event.item_reference,
                      "title": event.metadata_json.get("title", event.action), "message": event.metadata_json.get("message", ""),
                      "channel": event.metadata_json.get("channel", "PORTAL"), "delivery_status": event.metadata_json.get("delivery_status", "DELIVERED"),
                      "created_at": event.created_at.isoformat()}
                     for event in notification_events if str(event.metadata_json.get("recipient", "")).lower() in {client_user.email.lower(), customer.id.lower()}]
    alerts.extend({"id": item["id"], "kind": "NOTIFICATION", "title": item["title"],
                   "detail": item["message"], "status": item["delivery_status"]} for item in notifications)
    return {"profile": _profile(client_user), "vehicles": [_vehicle_payload(v, histories) for v in vehicles],
            "alerts": alerts, "quotes": quote_items, "invoices": invoices, "notifications": notifications}


@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def add_vehicle(data: ClientVehicleCreate, client_user: ClientUser = Depends(require_client), db: Session = Depends(get_db)) -> dict[str, object]:
    customer = _customer(db, client_user)
    vehicle = Vehicle(customer_id=customer.id, vin=data.vin.strip().upper(), plate=data.plate.strip().upper() if data.plate else None,
                      make=data.make.strip(), model=data.model.strip(), model_year=data.model_year, engine=data.engine, mileage_km=data.mileage_km)
    db.add(vehicle)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="El VIN ya está registrado") from exc
    db.refresh(vehicle)
    return _vehicle_payload(vehicle, [])


@router.get("/vehicles/{vehicle_id}/compatible-parts", response_model=list[ProductRead])
def client_compatible_parts(
    vehicle_id: str,
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> list[CatalogProduct]:
    """Return persisted, published fitment only for a vehicle owned by this account."""
    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.customer_id == client_user.customer_id,
            Vehicle.organization_id == client_user.organization_id,
        )
    )
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehículo del cliente no encontrado")
    return compatible_products(db, vehicle)


@router.put("/profile")
def update_profile(data: ClientProfileUpdate, client_user: ClientUser = Depends(require_client), db: Session = Depends(get_db)) -> dict[str, object]:
    customer = _customer(db, client_user)
    persisted_user = db.get(ClientUser, client_user.id)
    if persisted_user is None:
        raise HTTPException(status_code=404, detail="Cuenta de cliente no encontrada")
    customer.full_name = data.full_name
    customer.email = str(data.email)
    persisted_user.full_name = data.full_name
    persisted_user.email = str(data.email)
    persisted_user.notification_email = persisted_user.email
    persisted_user.username = data.username
    persisted_user.credit_requested = data.credit_requested
    persisted_user.requested_credit_amount = data.credit_amount if data.credit_requested else None
    persisted_user.credit_status = "EN_REVISION" if data.credit_requested else "NO_SOLICITADO"
    password_changed = bool(data.new_password)
    if data.new_password:
        persisted_user.hashed_password = PasswordHelper().hash(data.new_password)
    db.add_all([customer, persisted_user])
    db.add(FlowEvent(module="CLIENT_PORTAL", action="PROFILE_UPDATED", item_reference=customer.id, actor=f"client:{client_user.id}",
                     result="SUCCESS", metadata_json={"credit_requested": data.credit_requested,
                                                       "credit_amount": data.credit_amount,
                                                       "password_changed": password_changed}))
    db.commit()
    return _profile(persisted_user)


@router.patch("/quotes/{quote_id}/lines/{line_id}")
def decide_quote_line(quote_id: str, line_id: str, decision: str, client_user: ClientUser = Depends(require_client), db: Session = Depends(get_db)) -> dict[str, str]:
    if decision not in {"APPROVED", "REJECTED"}: raise HTTPException(status_code=422, detail="Decisión no válida")
    customer = _customer(db, client_user)
    quote = db.scalar(
        select(Quote)
        .outerjoin(WorkOrder, Quote.work_order_id == WorkOrder.id)
        .where(Quote.id == quote_id, or_(Quote.customer_id == customer.id, WorkOrder.customer_id == customer.id))
        .options(selectinload(Quote.lines))
    )
    if quote is None: raise HTTPException(status_code=404, detail="Cotización no encontrada")
    line = next((item for item in quote.lines if item.id == line_id), None)
    if line is None: raise HTTPException(status_code=404, detail="Concepto no encontrado")
    line.approval_status = decision
    if all(item.approval_status != "PENDING" for item in quote.lines):
        quote.status = "APPROVED" if any(item.approval_status == "APPROVED" for item in quote.lines) else "REJECTED"
        quote.approved_by = client_user.email; quote.approved_at = datetime.now(UTC)
    db.add(FlowEvent(module="CLIENT_PORTAL", action=f"QUOTE_LINE_{decision}", item_reference=quote.number,
                     actor=f"client:{client_user.id}", result="SUCCESS", metadata_json={"line_id": line.id}))
    db.commit()
    return {"status": quote.status, "line_status": line.approval_status}
