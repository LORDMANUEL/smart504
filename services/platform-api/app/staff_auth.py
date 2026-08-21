from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users.jwt import decode_jwt, generate_jwt
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, get_async_db
from app.models import NotificationDelivery, StaffAccessEvent, StaffUser
from app.request_context import set_staff_identity
from app.services.staff_security import decrypt_totp_secret, verify_totp

settings = get_settings()


async def get_staff_user_db(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, StaffUser)


class StaffUserManager(UUIDIDMixin, BaseUserManager[StaffUser, uuid.UUID]):
    reset_password_token_secret = settings.staff_signing_secret
    verification_token_secret = settings.staff_signing_secret

    async def authenticate(self, credentials):
        try:
            user = await self.get_by_email(credentials.username)
        except exceptions.UserNotExists:
            return await super().authenticate(credentials)

        now = datetime.now(UTC)
        locked_until = user.locked_until
        if locked_until is not None and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)
        if locked_until and locked_until > now:
            await self._record_access(user, "LOGIN", "LOCKED", "Cuenta bloqueada temporalmente")
            return None

        authenticated = await super().authenticate(credentials)
        mfa_valid = True
        if authenticated and user.mfa_enabled:
            supplied_code = getattr(credentials, "client_secret", None) or ""
            try:
                secret = decrypt_totp_secret(user.mfa_secret_encrypted or "", settings)
                mfa_valid = verify_totp(secret, supplied_code)
            except Exception:
                mfa_valid = False
        if authenticated is None or not mfa_valid:
            attempts = int(user.failed_login_attempts or 0) + 1
            updates = {"failed_login_attempts": attempts}
            if attempts >= settings.staff_login_max_attempts:
                updates["locked_until"] = now + timedelta(minutes=settings.staff_login_lock_minutes)
            await self.user_db.update(user, updates)
            await self._record_access(
                user,
                "LOGIN",
                "FAILED",
                "Credenciales o segundo factor incorrectos",
            )
            return None

        if user.failed_login_attempts or user.locked_until:
            authenticated = await self.user_db.update(
                user, {"failed_login_attempts": 0, "locked_until": None}
            )
        return authenticated

    async def _record_access(
        self, user: StaffUser, action: str, result: str, detail: str
    ) -> None:
        set_staff_identity(
            actor=user.employee_code,
            organization_id=user.organization_id,
            branch_id=user.branch_id,
        )
        self.user_db.session.add(
            StaffAccessEvent(
                user_id=user.id,
                organization_id=user.organization_id,
                action=action,
                result=result,
                detail=detail,
            )
        )
        await self.user_db.session.commit()

    async def on_after_login(
        self,
        user: StaffUser,
        request: Request | None = None,
        response=None,
    ) -> None:
        set_staff_identity(
            actor=user.employee_code,
            organization_id=user.organization_id,
            branch_id=user.branch_id,
        )
        with SessionLocal() as db:
            persisted = db.get(StaffUser, user.id)
            if persisted:
                persisted.last_login_at = datetime.now(UTC)
            db.add(StaffAccessEvent(
                user_id=user.id,
                organization_id=user.organization_id,
                action="LOGIN",
                result="SUCCESS",
                detail="Inicio de sesion del personal",
            ))
            db.commit()

    async def on_after_forgot_password(
        self,
        user: StaffUser,
        token: str,
        request: Request | None = None,
    ) -> None:
        """Queue a real reset link without revealing whether an email exists."""
        set_staff_identity(
            actor=user.employee_code,
            organization_id=user.organization_id,
            branch_id=user.branch_id,
        )
        fingerprint = hashlib.sha256(token.encode()).hexdigest()[:24]
        reset_url = (
            f"{settings.approval_public_base_url.rstrip('/')}/tallerv1/login"
            f"?reset_token={quote(token, safe='')}"
        )
        self.user_db.session.add(
            NotificationDelivery(
                organization_id=user.organization_id,
                channel="EMAIL",
                recipient=user.email,
                subject="Restablecer contraseña de SmartDiag504",
                body_text=(
                    "Se solicitó restablecer su contraseña de SmartDiag504. "
                    f"Abra este enlace temporal: {reset_url}\n\n"
                    "Si usted no hizo la solicitud, ignore este mensaje y avise al administrador."
                ),
                template_key="STAFF_PASSWORD_RESET",
                aggregate_type="STAFF_USER",
                aggregate_id=str(user.id),
                idempotency_key=f"staff-password-reset:{user.id}:{fingerprint}",
                payload_json={"purpose": "PASSWORD_RESET", "token_fingerprint": fingerprint},
            )
        )
        self.user_db.session.add(
            StaffAccessEvent(
                user_id=user.id,
                organization_id=user.organization_id,
                action="PASSWORD_RESET_REQUESTED",
                result="QUEUED",
                detail="Enlace de recuperación enviado al outbox transaccional",
            )
        )
        await self.user_db.session.commit()


async def get_staff_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_staff_user_db),
) -> AsyncGenerator[StaffUserManager, None]:
    yield StaffUserManager(user_db)


cookie_transport = CookieTransport(
    cookie_name="smartdiag_staff_session",
    cookie_max_age=settings.staff_session_hours * 3600,
    cookie_path="/",
    cookie_secure=settings.environment.lower() not in {"test", "development"},
    cookie_httponly=True,
    cookie_samesite="lax",
)


class RevocableJWTStrategy(JWTStrategy):
    async def write_token(self, user: StaffUser) -> str:
        data = {
            "sub": str(user.id),
            "aud": self.token_audience,
            "sv": int(user.session_version),
        }
        return generate_jwt(data, self.encode_key, self.lifetime_seconds, algorithm=self.algorithm)

    async def read_token(self, token, user_manager):
        if token is None:
            return None
        try:
            data = decode_jwt(
                token, self.decode_key, self.token_audience, algorithms=[self.algorithm]
            )
            user_id = data.get("sub")
            token_version = int(data.get("sv", 0))
            if user_id is None:
                return None
            user = await user_manager.get(user_manager.parse_id(user_id))
            if int(user.session_version) != token_version:
                return None
            return user
        except Exception:
            return None


def get_jwt_strategy() -> JWTStrategy:
    return RevocableJWTStrategy(
        secret=settings.staff_signing_secret,
        lifetime_seconds=settings.staff_session_hours * 3600,
    )


staff_auth_backend = AuthenticationBackend(
    name="staff-cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_staff_users = FastAPIUsers[StaffUser, uuid.UUID](
    get_staff_user_manager,
    [staff_auth_backend],
)
optional_staff_user = fastapi_staff_users.current_user(optional=True, active=True)
current_staff_user = fastapi_staff_users.current_user(active=True)


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "OWNER": {"*"},
    "ADMIN": {"*"},
    "MANAGER": {
        "WORK_ORDERS", "BOOKINGS", "ORDERS", "CATALOG", "QUOTES", "CASHIER",
        "WAREHOUSE", "PROCESSES", "CRM", "MARKETING", "DOCUMENTS", "REPORTS",
        "SETTINGS", "SYSTEM",
        "PROCUREMENT", "HR", "USED_VEHICLES", "SOCIAL", "ENTERPRISE",
    },
    "ACCOUNTANT": {"REPORTS", "QUOTES", "CASHIER", "DOCUMENTS", "MANAGEMENT", "PROCUREMENT", "HR", "ENTERPRISE"},
    "TECHNICIAN": {"WORK_ORDERS", "CATALOG", "DOCUMENTS"},
    "CASHIER": {"CASHIER", "QUOTES", "WORK_ORDERS", "DOCUMENTS"},
    "WAREHOUSE": {"WAREHOUSE", "WORK_ORDERS", "CATALOG", "DOCUMENTS"},
    "RECEPTION": {"BOOKINGS", "QUOTES", "WORK_ORDERS", "ORDERS", "CRM"},
    "MARKETING": {"MARKETING", "CRM", "SOCIAL", "ENTERPRISE"},
    "AUDITOR": {"REPORTS", "WORK_ORDERS", "QUOTES", "CASHIER", "WAREHOUSE", "PROCESSES"},
}


def effective_permissions(user: StaffUser) -> set[str]:
    return ROLE_PERMISSIONS.get(user.role, set()) | set(user.permissions_json or [])


def has_permission(user: StaffUser, permission: str, method: str = "GET") -> bool:
    if permission == "AUTHENTICATED":
        return True
    permissions = effective_permissions(user)
    if "*" in permissions or permission in permissions:
        normalized_method = method.upper()
        if user.role == "AUDITOR" and normalized_method != "GET":
            return False
        # Operational roles need to read/print documents and inspect the
        # catalog, but publishing invoice templates or mutating the item
        # master changes company-wide financial output. Keep those writes in
        # the roles that own configuration and inventory governance.
        if normalized_method != "GET" and permission == "DOCUMENTS":
            return user.role in {"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT"}
        if normalized_method != "GET" and permission == "CATALOG":
            return user.role in {"OWNER", "ADMIN", "MANAGER", "WAREHOUSE"}
        return True
    return False
