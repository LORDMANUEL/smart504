from __future__ import annotations

import hmac
import ipaddress

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import get_settings
from app.models import StaffUser
from app.request_context import set_staff_identity
from app.staff_auth import has_permission, optional_staff_user


def _enforce_branch_scope(staff_user: StaffUser) -> bool:
    """Owners/admins may consolidate branches; assigned operational users may not."""
    return bool(staff_user.branch_id and staff_user.role not in {"OWNER", "ADMIN"})


def _authorize_recovery_token(request: Request, candidate: str | None) -> bool:
    settings = get_settings()
    if not candidate or not hmac.compare_digest(candidate, settings.admin_api_token.get_secret_value()):
        return False
    if not settings.production:
        return True
    if not settings.recovery_token_enabled:
        raise HTTPException(status_code=403, detail="Acceso de recuperación deshabilitado")
    reason = (request.headers.get("x-recovery-reason") or "").strip()
    if len(reason) < 12:
        raise HTTPException(status_code=403, detail="La recuperación exige un motivo auditado")
    try:
        source = ipaddress.ip_address(request.client.host if request.client else "")
        allowed = any(source in ipaddress.ip_network(cidr, strict=False) for cidr in settings.recovery_token_allowed_cidrs)
    except ValueError:
        allowed = False
    if not allowed:
        raise HTTPException(status_code=403, detail="Origen no autorizado para recuperación")
    return True


def _permission_for_path(path: str) -> str:
    if "/operations/enterprise/hr/" in path:
        return "HR"
    if "/operations/enterprise/social/" in path:
        return "SOCIAL"
    if "/operations/enterprise/used-vehicles" in path:
        return "USED_VEHICLES"
    if any(part in path for part in ("/operations/enterprise/suppliers", "/operations/enterprise/purchase-orders", "/operations/enterprise/import-cases")):
        return "PROCUREMENT"
    if path.endswith("/operations/enterprise/overview"):
        return "ENTERPRISE"
    if path.endswith("/operations/control/overview"):
        return "AUTHENTICATED"
    if any(segment in path for segment in ("/finance/cash", "/finance/counter-sales", "/finance/counter-returns", "/finance/approval-requests")):
        return "CASHIER"
    if "/finance/quotes" in path:
        return "QUOTES"
    if "/finance/reporting" in path:
        return "REPORTS"
    if "/bookings" in path:
        return "BOOKINGS"
    if "/work-orders" in path:
        return "WORK_ORDERS"
    if "/store/orders" in path:
        return "ORDERS"
    if "/catalog" in path:
        return "CATALOG"
    if "/documents" in path:
        return "DOCUMENTS"
    if path.endswith("/flow-events/heatmap"):
        return "AUTHENTICATED"
    if "/flow-events" in path:
        return "PROCESSES"
    if "/marketing" in path:
        return "MARKETING"
    if "/settings" in path:
        return "SETTINGS"
    if "/cluster/" in path or "/ha/" in path:
        return "SYSTEM"
    if "/operations/control" in path:
        if "/leads" in path:
            return "CRM"
        if any(part in path for part in ("/warehouses", "/reservations", "/transfers", "/shipments")):
            return "WAREHOUSE"
        if "/quality" in path:
            return "PROCESSES"
        return "MANAGEMENT"
    return "ADMIN"


async def require_admin(
    request: Request,
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
    staff_user: StaffUser | None = Depends(optional_staff_user),
) -> StaffUser | None:
    candidate = x_admin_token
    if authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:].strip()
    if _authorize_recovery_token(request, candidate):
        set_staff_identity(
            actor="system-recovery",
            organization_id="SMARTDIAG504",
            branch_id=None,
            is_recovery=True,
        )
        return None
    if staff_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion del personal requerida")
    permission = _permission_for_path(request.url.path)
    if not has_permission(staff_user, permission, request.method):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Su rol no tiene permiso para {permission}")
    set_staff_identity(
        actor=staff_user.employee_code,
        organization_id=staff_user.organization_id,
        branch_id=staff_user.branch_id,
        enforce_branch_scope=_enforce_branch_scope(staff_user),
    )
    return staff_user


async def require_staff_manager(
    request: Request,
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
    staff_user: StaffUser | None = Depends(optional_staff_user),
) -> StaffUser | None:
    candidate = x_admin_token
    if authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:].strip()
    if _authorize_recovery_token(request, candidate):
        set_staff_identity(
            actor="system-recovery",
            organization_id="SMARTDIAG504",
            branch_id=None,
            is_recovery=True,
        )
        return None
    if staff_user and staff_user.role in {"OWNER", "ADMIN"}:
        set_staff_identity(
            actor=staff_user.employee_code,
            organization_id=staff_user.organization_id,
            branch_id=staff_user.branch_id,
            enforce_branch_scope=_enforce_branch_scope(staff_user),
        )
        return staff_user
    raise HTTPException(status_code=403 if staff_user else 401, detail="Se requiere propietario o administrador")


async def require_authenticated_staff(
    request: Request,
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
    staff_user: StaffUser | None = Depends(optional_staff_user),
) -> StaffUser | None:
    candidate = x_admin_token
    if authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:].strip()
    if _authorize_recovery_token(request, candidate):
        set_staff_identity(
            actor="system-recovery",
            organization_id="SMARTDIAG504",
            branch_id=None,
            is_recovery=True,
        )
        return None
    if staff_user is not None and staff_user.is_active:
        set_staff_identity(
            actor=staff_user.employee_code,
            organization_id=staff_user.organization_id,
            branch_id=staff_user.branch_id,
            enforce_branch_scope=_enforce_branch_scope(staff_user),
        )
        return staff_user
    raise HTTPException(status_code=401, detail="Sesion del personal requerida")


def require_heartbeat_token(
    x_heartbeat_token: str | None = Header(default=None),
) -> None:
    expected = get_settings().event_hmac_secret.get_secret_value()
    if not x_heartbeat_token or not hmac.compare_digest(x_heartbeat_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid heartbeat credentials",
        )
