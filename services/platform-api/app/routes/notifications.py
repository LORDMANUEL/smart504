from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_staff_manager
from app.config import get_settings
from app.db import get_db
from app.models import NotificationDelivery
from app.services.notifications import deliver_notifications


router = APIRouter(
    prefix="/api/v1/operations/notifications",
    tags=["notifications"],
    dependencies=[Depends(require_staff_manager)],
)


def _payload(item: NotificationDelivery) -> dict[str, object]:
    return {
        "id": item.id,
        "channel": item.channel,
        "recipient": item.recipient,
        "subject": item.subject,
        "template_key": item.template_key,
        "aggregate_type": item.aggregate_type,
        "aggregate_id": item.aggregate_id,
        "status": item.status,
        "attempts": item.attempts,
        "provider_reference": item.provider_reference,
        "last_error": item.last_error,
        "scheduled_at": item.scheduled_at,
        "sent_at": item.sent_at,
        "created_at": item.created_at,
    }


@router.get("")
def list_deliveries(status: str | None = None, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = select(NotificationDelivery).order_by(NotificationDelivery.created_at.desc()).limit(250)
    if status:
        query = query.where(NotificationDelivery.status == status.upper())
    return [_payload(item) for item in db.scalars(query)]


@router.post("/{delivery_id}/retry")
def retry_delivery(delivery_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    item = db.get(NotificationDelivery, delivery_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    if item.status == "SENT":
        raise HTTPException(status_code=409, detail="La notificacion ya fue enviada")
    item.status = "PENDING"
    item.last_error = None
    db.commit()
    return _payload(item)


@router.post("/process")
def process_now(db: Session = Depends(get_db)) -> dict[str, int]:
    return deliver_notifications(db, get_settings())
