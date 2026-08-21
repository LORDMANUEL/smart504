from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.client_auth import require_client
from app.db import get_async_db
from app.models import ClientUser

router = APIRouter(prefix="/api/v1/client-auth", tags=["client-auth"])


@router.get("/session")
async def client_session(user: ClientUser = Depends(require_client)) -> dict[str, object]:
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name,
            "username": user.username, "organization_id": user.organization_id,
            "customer_id": user.customer_id, "mfa_enabled": user.mfa_enabled}


@router.post("/revoke-sessions")
async def revoke_client_sessions(
    user: ClientUser = Depends(require_client), session: AsyncSession = Depends(get_async_db)
) -> dict[str, str]:
    await session.execute(
        update(ClientUser)
        .where(ClientUser.id == user.id)
        .values(session_version=int(user.session_version) + 1)
    )
    await session.commit()
    return {"status": "revoked"}
