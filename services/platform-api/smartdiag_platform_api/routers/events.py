from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from smartdiag_domain.events import DomainEvent

from ..dependencies import get_repository, get_settings
from ..models import AcceptedEvent, IncomingEvent
from ..repositories import InMemoryRepository
from ..security import verify_body_signature
from ..settings import Settings

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=AcceptedEvent, status_code=status.HTTP_202_ACCEPTED)
async def accept_event(
    request: Request,
    signature: str | None = Header(default=None, alias="X-SmartDiag-Signature"),
    settings: Settings = Depends(get_settings),
    repository: InMemoryRepository = Depends(get_repository),
) -> AcceptedEvent:
    body = await request.body()
    if not verify_body_signature(body, signature, settings.webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid event signature")
    try:
        payload = IncomingEvent.model_validate_json(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid event payload") from exc
    event = DomainEvent.create(
        event_type=payload.event_type,
        aggregate_type=payload.aggregate_type,
        aggregate_id=payload.aggregate_id,
        payload=payload.payload,
        actor_id=payload.actor_id,
    )
    accepted = repository.accept_event(event)
    return AcceptedEvent(accepted=True, event_id=accepted.event_id, event_key=accepted.event_key)
