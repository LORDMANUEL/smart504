from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ErpIntegrationJob
from app.request_context import current_identity


def enqueue_erp_job(
    db: Session,
    *,
    aggregate_type: str,
    aggregate_id: str,
    operation: str,
    idempotency_key: str,
    payload: dict[str, object],
) -> ErpIntegrationJob:
    identity = current_identity()
    existing = db.scalar(
        select(ErpIntegrationJob).where(
            ErpIntegrationJob.organization_id == identity.organization_id,
            ErpIntegrationJob.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing
    job = ErpIntegrationJob(
        organization_id=identity.organization_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        operation=operation,
        idempotency_key=idempotency_key,
        payload_json=payload,
    )
    db.add(job)
    return job
