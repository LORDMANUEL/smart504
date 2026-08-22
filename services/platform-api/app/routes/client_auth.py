from __future__ import annotations

import re
import unicodedata
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users.password import PasswordHelper
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.client_auth import require_client
from app.db import get_async_db
from app.config import get_settings
from app.models import ClientUser, Customer, FlowEvent, NotificationDelivery
from app.request_context import set_staff_identity
from app.services.public_abuse import enforce_public_limit, reject_honeypot

router = APIRouter(prefix="/api/v1/client-auth", tags=["client-auth"])
settings = get_settings()


class ClientRegistration(BaseModel):
    full_name: str = Field(min_length=3, max_length=180)
    phone: str = Field(min_length=8, max_length=40)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    username: str | None = Field(default=None, min_length=3, max_length=80)
    website: str | None = Field(default=None, max_length=200)


def _username(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9._-]+", ".", normalized).strip(".-_")[:64] or "cliente"


@router.get("/registration-options")
async def registration_options() -> dict[str, object]:
    return {
        "self_registration": True,
        "managed_mail_domain": settings.managed_mail_domain,
        "managed_mailbox_enabled": settings.managed_mailbox_enabled,
        "social_login": {
            "enabled": settings.frappe_social_login_enabled,
            "configuration_source": "ERPNext / Social Login Key",
            "login_url": f"{settings.frappe_base_url.rstrip('/')}/login" if settings.frappe_base_url and settings.frappe_social_login_enabled else None,
        },
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_client(data: ClientRegistration, request: Request, session: AsyncSession = Depends(get_async_db)) -> dict[str, object]:
    enforce_public_limit(request, settings, surface="client-registration", limit=settings.public_client_registration_limit_per_minute)
    reject_honeypot(data.website)
    organization_id = "SMARTDIAG504"
    set_staff_identity(actor="client-registration", organization_id=organization_id, branch_id=None)
    email = str(data.email).lower().strip()
    duplicate = await session.scalar(select(ClientUser.id).where(ClientUser.email == email))
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo.")
    base = _username(data.username or data.full_name)
    username = base
    suffix = 1
    while await session.scalar(select(ClientUser.id).where(ClientUser.organization_id == organization_id, ClientUser.username == username)):
        suffix += 1
        username = f"{base[:70]}-{suffix}"
    managed_email = f"{username}@{settings.managed_mail_domain.lower()}"
    if await session.scalar(select(ClientUser.id).where(ClientUser.managed_email == managed_email)):
        managed_email = f"{base[:56]}.{uuid.uuid4().hex[:8]}@{settings.managed_mail_domain.lower()}"
    customer = Customer(organization_id=organization_id, full_name=data.full_name.strip(), phone=data.phone.strip(), email=email)
    session.add(customer)
    await session.flush()
    user = ClientUser(
        email=email, notification_email=email, managed_email=managed_email,
        mailbox_status="QUEUED" if settings.managed_mailbox_enabled else "PENDING_CONFIGURATION",
        hashed_password=PasswordHelper().hash(data.password), is_active=True, is_verified=False,
        is_superuser=False, organization_id=organization_id, customer_id=customer.id,
        username=username, full_name=data.full_name.strip(),
    )
    session.add(user)
    await session.flush()
    session.add(FlowEvent(
        organization_id=organization_id, module="CLIENT_PORTAL", action="CLIENT_ACCOUNT_CREATED",
        item_reference=str(user.id), actor="client-registration", result="SUCCESS",
        metadata_json={"username": username, "mailbox_status": user.mailbox_status},
    ))
    session.add(NotificationDelivery(
        organization_id=organization_id, channel="EMAIL", recipient=email,
        subject="Cuenta SmartDiag504 creada",
        body_text=f"Hola {data.full_name.strip()}, su usuario es {username}. Su correo SmartDiag504 reservado es {managed_email}.",
        template_key="CLIENT_ACCOUNT_CREATED", aggregate_type="CLIENT_USER", aggregate_id=str(user.id),
        idempotency_key=f"client-account-created:{user.id}", payload_json={"username": username},
    ))
    await session.commit()
    return {
        "username": username, "notification_email": email, "managed_email": managed_email,
        "mailbox_status": user.mailbox_status,
        "message": "Cuenta creada. Ya puede ingresar con su correo personal.",
    }


@router.get("/session")
async def client_session(user: ClientUser = Depends(require_client)) -> dict[str, object]:
    return {"id": str(user.id), "email": user.email, "notification_email": user.notification_email,
            "managed_email": user.managed_email, "mailbox_status": user.mailbox_status, "full_name": user.full_name,
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
