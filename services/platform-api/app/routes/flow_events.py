from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_db
from app.models import FlowEvent
from app.schemas import FlowEventCreate, FlowEventRead, FlowHeatmapCell
from app.request_context import audit_actor

router = APIRouter(
    prefix="/api/v1/operations/flow-events",
    tags=["flow-events"],
    dependencies=[Depends(require_admin)],
)


@router.post("", response_model=FlowEventRead, status_code=status.HTTP_201_CREATED)
def create_flow_event(payload: FlowEventCreate, db: Session = Depends(get_db)) -> FlowEvent:
    event = FlowEvent(
        module=payload.module,
        action=payload.action,
        item_reference=payload.item_reference.strip(),
        actor=audit_actor(payload.actor),
        result=payload.result,
        metadata_json=payload.metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=list[FlowEventRead])
def list_flow_events(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
) -> list[FlowEvent]:
    return list(db.scalars(select(FlowEvent).order_by(desc(FlowEvent.created_at)).limit(limit)))


@router.get("/heatmap", response_model=list[FlowHeatmapCell])
def flow_heatmap(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = db.execute(
        select(
            FlowEvent.module,
            FlowEvent.action,
            func.count(FlowEvent.id),
            func.max(FlowEvent.created_at),
        )
        .group_by(FlowEvent.module, FlowEvent.action)
        .order_by(desc(func.count(FlowEvent.id)))
    ).all()
    return [
        {"module": module, "action": action, "count": count, "last_seen_at": last_seen_at}
        for module, action, count, last_seen_at in rows
    ]
