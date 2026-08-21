from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_async_db
from app.models import ClientUser, NotificationDelivery
from app.request_context import set_staff_identity
from app.staff_auth import RevocableJWTStrategy

settings = get_settings()


async def get_client_user_db(session: AsyncSession = Depends(get_async_db)) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, ClientUser)


class ClientUserManager(UUIDIDMixin, BaseUserManager[ClientUser, uuid.UUID]):
    reset_password_token_secret = settings.client_signing_secret
    verification_token_secret = settings.client_signing_secret

    async def authenticate(self, credentials):
        try:
            user = await self.get_by_email(credentials.username)
        except exceptions.UserNotExists:
            return await super().authenticate(credentials)
        set_staff_identity(actor=f"client:{user.id}", organization_id=user.organization_id, branch_id=None)
        now = datetime.now(UTC)
        locked_until = user.locked_until
        if locked_until is not None and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)
        if locked_until and locked_until > now:
            return None
        authenticated = await super().authenticate(credentials)
        if authenticated is None:
            attempts = int(user.failed_login_attempts or 0) + 1
            updates: dict[str, object] = {"failed_login_attempts": attempts}
            if attempts >= settings.staff_login_max_attempts:
                updates["locked_until"] = now + timedelta(minutes=settings.staff_login_lock_minutes)
            await self.user_db.update(user, updates)
            return None
        if user.failed_login_attempts or user.locked_until:
            authenticated = await self.user_db.update(user, {"failed_login_attempts": 0, "locked_until": None})
        return authenticated

    async def on_after_login(self, user: ClientUser, request: Request | None = None, response=None):
        set_staff_identity(actor=f"client:{user.id}", organization_id=user.organization_id, branch_id=None)
        await self.user_db.update(user, {"last_login_at": datetime.now(UTC)})

    async def on_after_forgot_password(self, user: ClientUser, token: str, request: Request | None = None) -> None:
        set_staff_identity(actor=f"client:{user.id}", organization_id=user.organization_id, branch_id=None)
        fingerprint = hashlib.sha256(token.encode()).hexdigest()[:24]
        reset_url = f"{settings.approval_public_base_url.rstrip('/')}/lading/loginclie?reset_token={quote(token, safe='')}"
        self.user_db.session.add(NotificationDelivery(
            organization_id=user.organization_id, channel="EMAIL", recipient=user.email,
            subject="Restablecer acceso de cliente SmartDiag504",
            body_text=f"Abra este enlace temporal para restablecer su contraseña: {reset_url}\n\nSi no hizo la solicitud, ignore el mensaje.",
            template_key="CLIENT_PASSWORD_RESET", aggregate_type="CLIENT_USER", aggregate_id=str(user.id),
            idempotency_key=f"client-password-reset:{user.id}:{fingerprint}",
            payload_json={"purpose": "PASSWORD_RESET", "token_fingerprint": fingerprint},
        ))
        await self.user_db.session.commit()


async def get_client_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_client_user_db)) -> AsyncGenerator[ClientUserManager, None]:
    yield ClientUserManager(user_db)


client_cookie_transport = CookieTransport(
    cookie_name="smartdiag_client_session", cookie_max_age=settings.client_session_ttl_minutes * 60,
    cookie_path="/", cookie_secure=settings.environment.lower() not in {"test", "development"},
    cookie_httponly=True, cookie_samesite="lax",
)


def get_client_jwt_strategy() -> RevocableJWTStrategy:
    return RevocableJWTStrategy(secret=settings.client_signing_secret, lifetime_seconds=settings.client_session_ttl_minutes * 60)


client_auth_backend = AuthenticationBackend(name="client-cookie", transport=client_cookie_transport, get_strategy=get_client_jwt_strategy)
fastapi_client_users = FastAPIUsers[ClientUser, uuid.UUID](get_client_user_manager, [client_auth_backend])
current_client_user = fastapi_client_users.current_user(active=True)


async def require_client(user: ClientUser = Depends(current_client_user)) -> ClientUser:
    set_staff_identity(actor=f"client:{user.id}", organization_id=user.organization_id, branch_id=None)
    return user
