from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_staff_manager
from app.config import get_settings
from app.db import get_db
from app.models import ErpIntegrationJob
from app.request_context import audit_actor
from app.services.erp_sync import process_erp_jobs


router = APIRouter(
    prefix="/api/v1/operations/integrations/erp",
    tags=["erp-integration"],
    dependencies=[Depends(require_staff_manager)],
)


def _job_payload(job: ErpIntegrationJob) -> dict[str, object]:
    return {
        "id": job.id,
        "organization_id": job.organization_id,
        "aggregate_type": job.aggregate_type,
        "aggregate_id": job.aggregate_id,
        "operation": job.operation,
        "status": job.status,
        "attempts": job.attempts,
        "target_reference": job.target_reference,
        "last_error": job.last_error,
        "next_attempt_at": job.next_attempt_at,
        "processed_at": job.processed_at,
        "created_at": job.created_at,
    }


@router.get("/jobs")
def list_jobs(status: str | None = None, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = select(ErpIntegrationJob).order_by(ErpIntegrationJob.created_at.desc()).limit(200)
    if status:
        query = query.where(ErpIntegrationJob.status == status.upper())
    return [_job_payload(job) for job in db.scalars(query)]


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    job = db.get(ErpIntegrationJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Trabajo de integracion no encontrado")
    if job.status == "SYNCED":
        raise HTTPException(status_code=409, detail="El documento ya fue confirmado por ERPNext")
    job.status = "PENDING"
    job.last_error = None
    job.next_attempt_at = None
    payload = dict(job.payload_json)
    payload["retried_by"] = audit_actor()
    job.payload_json = payload
    db.commit()
    return _job_payload(job)


@router.post("/process")
def process_now(db: Session = Depends(get_db)) -> dict[str, int]:
    return process_erp_jobs(db, get_settings(), limit=25)
