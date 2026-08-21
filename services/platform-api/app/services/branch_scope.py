from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Branch
from app.request_context import current_identity


def operational_branch_id(db: Session, requested_branch_id: str | None = None) -> str:
    """Resolve a concrete, active branch for every operational transaction."""
    identity = current_identity()
    if (
        identity.enforce_branch_scope
        and requested_branch_id
        and requested_branch_id != identity.branch_id
    ):
        raise HTTPException(status_code=403, detail="La sucursal solicitada no pertenece a la sesión")
    candidate = requested_branch_id or identity.branch_id
    if candidate:
        exists = db.scalar(
            select(Branch.id).where(
                Branch.id == candidate,
                Branch.organization_id == identity.organization_id,
                Branch.active.is_(True),
            )
        )
        if exists:
            return exists
        raise HTTPException(status_code=422, detail="La sucursal no existe o está inactiva")
    fallback = db.scalar(
        select(Branch.id)
        .where(
            Branch.organization_id == identity.organization_id,
            Branch.active.is_(True),
        )
        .order_by(Branch.code != "MAIN", Branch.created_at, Branch.id)
    )
    if fallback:
        return fallback
    raise HTTPException(status_code=409, detail="Configure una sucursal activa antes de operar")
