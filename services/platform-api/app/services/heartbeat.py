from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LeaderLease, NodeHeartbeat
from app.schemas import HeartbeatRequest


def record_heartbeat(db: Session, data: HeartbeatRequest) -> NodeHeartbeat:
    now = datetime.now(timezone.utc)
    heartbeat = db.get(NodeHeartbeat, data.node_id)
    if heartbeat is None:
        heartbeat = NodeHeartbeat(node_id=data.node_id)
        db.add(heartbeat)
    heartbeat.role = data.role
    heartbeat.status = data.status
    heartbeat.version = data.version
    heartbeat.metadata_json = data.metadata
    heartbeat.last_seen_at = now
    db.commit()
    db.refresh(heartbeat)
    return heartbeat


def list_heartbeats(db: Session) -> list[NodeHeartbeat]:
    return list(db.scalars(select(NodeHeartbeat).order_by(NodeHeartbeat.node_id)))


def acquire_or_renew_lease(
    db: Session,
    *,
    lease_name: str,
    node_id: str,
    ttl_seconds: int,
) -> LeaderLease | None:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)
    lease = db.scalar(
        select(LeaderLease).where(LeaderLease.lease_name == lease_name).with_for_update()
    )
    if lease is None:
        lease = LeaderLease(
            lease_name=lease_name,
            holder_node_id=node_id,
            expires_at=expires_at,
            fencing_token=1,
        )
        db.add(lease)
        db.commit()
        db.refresh(lease)
        return lease
    lease_expiry = lease.expires_at
    if lease_expiry.tzinfo is None:
        lease_expiry = lease_expiry.replace(tzinfo=timezone.utc)
    if lease.holder_node_id != node_id and lease_expiry > now:
        db.rollback()
        return None
    if lease.holder_node_id != node_id:
        lease.fencing_token += 1
    lease.holder_node_id = node_id
    lease.expires_at = expires_at
    db.commit()
    db.refresh(lease)
    return lease
