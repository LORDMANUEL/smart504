from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApprovalRequest


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def load_approval_by_token(db: Session, token: str, *, for_update: bool = False) -> ApprovalRequest:
    statement = select(ApprovalRequest).where(ApprovalRequest.token_hash == token_digest(token))
    if for_update:
        statement = statement.with_for_update()
    approval = db.scalar(statement)
    if approval is None:
        raise HTTPException(status_code=404, detail="Enlace de autorizacion no valido")
    expires_at = approval.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC) and approval.status == "PENDING":
        approval.status = "EXPIRED"
        db.commit()
    return approval
