from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import require_admin, require_heartbeat_token
from app.db import get_db
from app.models import LeaderLease
from app.schemas import (
    HeartbeatRead,
    HeartbeatRequest,
    LeaseAcquireRequest,
    LeaseRead,
)
from app.services.heartbeat import acquire_or_renew_lease, list_heartbeats, record_heartbeat

router = APIRouter(prefix="/api/v1/cluster", tags=["cluster"])
legacy_router = APIRouter(prefix="/api/v1", tags=["cluster-compat"])


class LegacyHeartbeatRequest(BaseModel):
    """Backward-compatible payload used by the v0.3 agents and smoke tests."""

    node_id: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=80)
    healthy: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class LegacyLeaderAcquireRequest(BaseModel):
    lease_name: str = Field(min_length=2, max_length=120)
    node_id: str = Field(min_length=2, max_length=120)
    ttl_seconds: int = Field(default=30, ge=5, le=300)


@router.post(
    "/heartbeats",
    response_model=HeartbeatRead,
    dependencies=[Depends(require_heartbeat_token)],
)
def heartbeat(data: HeartbeatRequest, db: Session = Depends(get_db)):
    return record_heartbeat(db, data)


@router.get(
    "/heartbeats",
    response_model=list[HeartbeatRead],
    dependencies=[Depends(require_admin)],
)
def heartbeats(db: Session = Depends(get_db)):
    return list_heartbeats(db)


@router.post(
    "/leases/{lease_name}",
    response_model=LeaseRead,
    dependencies=[Depends(require_heartbeat_token)],
)
def acquire_lease(
    lease_name: str,
    data: LeaseAcquireRequest,
    db: Session = Depends(get_db),
):
    lease = acquire_or_renew_lease(
        db,
        lease_name=lease_name,
        node_id=data.node_id,
        ttl_seconds=data.ttl_seconds,
    )
    if lease is None:
        raise HTTPException(status_code=409, detail="Lease is held by another healthy node")
    return lease


@legacy_router.post(
    "/internal/heartbeat",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin)],
)
def legacy_heartbeat(
    data: LegacyHeartbeatRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    version = str(data.details.get("version") or "legacy")
    record_heartbeat(
        db,
        HeartbeatRequest(
            node_id=data.node_id,
            role=data.role,
            status="HEALTHY" if data.healthy else "UNHEALTHY",
            version=version[:50],
            metadata=data.details,
        ),
    )
    return {"status": "accepted", "node_id": data.node_id}


@legacy_router.get(
    "/ha/status",
    dependencies=[Depends(require_admin)],
)
def legacy_ha_status(db: Session = Depends(get_db)) -> dict[str, object]:
    nodes = [
        {
            "node_id": node.node_id,
            "role": node.role,
            "healthy": node.status == "HEALTHY",
            "status": node.status,
            "version": node.version,
            "details": node.metadata_json,
            "last_seen_at": node.last_seen_at,
        }
        for node in list_heartbeats(db)
    ]
    return {"nodes": nodes}


@legacy_router.post(
    "/ha/leader/acquire",
    dependencies=[Depends(require_admin)],
)
def legacy_acquire_leader(
    data: LegacyLeaderAcquireRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    lease = acquire_or_renew_lease(
        db,
        lease_name=data.lease_name,
        node_id=data.node_id,
        ttl_seconds=data.ttl_seconds,
    )
    if lease is not None:
        return {
            "is_leader": True,
            "lease_name": lease.lease_name,
            "leader_node_id": lease.holder_node_id,
            "expires_at": lease.expires_at,
            "fencing_token": lease.fencing_token,
        }

    current = db.get(LeaderLease, data.lease_name)
    return {
        "is_leader": False,
        "lease_name": data.lease_name,
        "leader_node_id": current.holder_node_id if current else None,
        "expires_at": current.expires_at if current else None,
        "fencing_token": current.fencing_token if current else None,
    }
