from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi_users import schemas as user_schemas
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_authenticated_staff, require_staff_manager
from app.db import get_async_db
from app.models import Branch, EmployeeContract, StaffAccessEvent, StaffCompensationProfile, StaffUser
from app.staff_auth import current_staff_user, get_staff_user_manager, optional_staff_user
from app.config import get_settings
from app.services.staff_security import (
    create_totp_secret,
    decrypt_totp_secret,
    encrypt_totp_secret,
    totp_uri,
    verify_totp,
)

StaffRole = Literal["OWNER", "ADMIN", "MANAGER", "ACCOUNTANT", "TECHNICIAN", "CASHIER", "WAREHOUSE", "RECEPTION", "MARKETING", "AUDITOR"]


class StaffUserRead(user_schemas.BaseUser[uuid.UUID]):
    organization_id: str
    branch_id: str | None
    employee_code: str
    full_name: str
    job_title: str | None
    role: StaffRole
    permissions_json: list[str]
    phone: str | None
    last_login_at: datetime | None
    failed_login_attempts: int
    locked_until: datetime | None
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime


class StaffUserCreate(user_schemas.BaseUserCreate):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    organization_id: str = "SMARTDIAG504"
    branch_id: str | None = None
    employee_code: str | None = Field(default=None, min_length=2, max_length=40, pattern=r"^[A-Z0-9_-]+$")
    full_name: str = Field(min_length=3, max_length=180)
    job_title: str | None = Field(default=None, max_length=120)
    role: StaffRole
    permissions_json: list[str] = Field(default_factory=list)
    phone: str | None = Field(default=None, max_length=40)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = True


class StaffUserUpdate(user_schemas.BaseUserUpdate):
    branch_id: str | None = None
    employee_code: str | None = Field(default=None, min_length=2, max_length=40, pattern=r"^[A-Z0-9_-]+$")
    full_name: str | None = Field(default=None, min_length=3, max_length=180)
    job_title: str | None = Field(default=None, max_length=120)
    role: StaffRole | None = None
    permissions_json: list[str] | None = None
    phone: str | None = Field(default=None, max_length=40)


class StaffAccessEventRead(BaseModel):
    id: str
    user_id: uuid.UUID | None
    action: str
    result: str
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StaffCompensationWrite(BaseModel):
    fixed_monthly_salary: Decimal = Field(ge=0, le=10000000)
    productive_hours_monthly: Decimal = Field(gt=0, le=744)
    base_hourly_wage: Decimal = Field(default=Decimal("0"), ge=0, le=100000)
    specialized_hourly_wage: Decimal = Field(default=Decimal("0"), ge=0, le=100000)
    employer_burden_percent: Decimal = Field(default=Decimal("0"), ge=0, le=300)
    standard_sale_rate: Decimal = Field(gt=0, le=1000000)
    specialized_sale_rate: Decimal = Field(gt=0, le=1000000)
    currency: str = Field(default="HNL", min_length=3, max_length=3)
    effective_from: date
    source_system: str = Field(default="LOCAL_PROJECTION", max_length=30)
    source_reference: str | None = Field(default=None, max_length=180)


class StaffCompensationRead(StaffCompensationWrite):
    id: str
    staff_user_id: uuid.UUID
    organization_id: str
    fixed_hourly_allocation: Decimal
    standard_hourly_cost: Decimal
    specialized_hourly_cost: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StaffTechnicianRead(BaseModel):
    id: uuid.UUID
    employee_code: str
    full_name: str
    job_title: str | None

    model_config = {"from_attributes": True}


class MfaEnrollmentRead(BaseModel):
    secret: str
    provisioning_uri: str


class MfaCode(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


router = APIRouter(prefix="/api/v1/staff", tags=["staff-identity"])


@router.get("/me", response_model=StaffUserRead)
async def me(user: StaffUser = Depends(current_staff_user)) -> StaffUser:
    return user


@router.get("/session", response_model=StaffUserRead, responses={204: {"description": "Sin sesión"}})
async def current_session(user: StaffUser | None = Depends(optional_staff_user)) -> StaffUser | Response:
    """Probe the cookie without turning the expected signed-out state into an HTTP error."""
    if user is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return user


@router.post("/me/mfa/enroll", response_model=MfaEnrollmentRead)
async def enroll_mfa(
    user: StaffUser = Depends(current_staff_user),
    db: AsyncSession = Depends(get_async_db),
) -> MfaEnrollmentRead:
    persisted = await db.get(StaffUser, user.id)
    if persisted is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if persisted.mfa_enabled:
        raise HTTPException(
            status_code=409,
            detail="MFA ya esta activo; desactivelo con su codigo actual antes de volver a enrolar",
        )
    secret = create_totp_secret()
    persisted.mfa_secret_encrypted = encrypt_totp_secret(secret, get_settings())
    persisted.mfa_enabled = False
    await db.commit()
    return MfaEnrollmentRead(
        secret=secret,
        provisioning_uri=totp_uri(secret=secret, email=user.email),
    )


@router.post("/me/mfa/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_mfa(
    data: MfaCode,
    user: StaffUser = Depends(current_staff_user),
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    persisted = await db.get(StaffUser, user.id)
    if persisted is None or not persisted.mfa_secret_encrypted:
        raise HTTPException(status_code=409, detail="Primero inicie la configuracion MFA")
    secret = decrypt_totp_secret(persisted.mfa_secret_encrypted, get_settings())
    if not verify_totp(secret, data.code):
        raise HTTPException(status_code=422, detail="Codigo MFA incorrecto")
    persisted.mfa_enabled = True
    persisted.session_version += 1
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/mfa", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    data: MfaCode,
    user: StaffUser = Depends(current_staff_user),
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    persisted = await db.get(StaffUser, user.id)
    if persisted is None or not persisted.mfa_enabled or not persisted.mfa_secret_encrypted:
        raise HTTPException(status_code=409, detail="MFA no esta activo")
    secret = decrypt_totp_secret(persisted.mfa_secret_encrypted, get_settings())
    if not verify_totp(secret, data.code):
        raise HTTPException(status_code=422, detail="Codigo MFA incorrecto")
    persisted.mfa_enabled = False
    persisted.mfa_secret_encrypted = None
    persisted.session_version += 1
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/sessions/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_sessions(
    user: StaffUser = Depends(current_staff_user),
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    persisted = await db.get(StaffUser, user.id)
    if persisted is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    persisted.session_version += 1
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users", response_model=list[StaffUserRead])
async def list_users(
    principal: StaffUser | None = Depends(require_staff_manager),
    db: AsyncSession = Depends(get_async_db),
) -> list[StaffUser]:
    statement = select(StaffUser)
    if principal is not None:
        statement = statement.where(StaffUser.organization_id == principal.organization_id)
    result = await db.scalars(statement.order_by(StaffUser.full_name))
    return list(result)


@router.get("/technicians", response_model=list[StaffTechnicianRead])
async def list_active_technicians(
    principal: StaffUser | None = Depends(require_authenticated_staff),
    db: AsyncSession = Depends(get_async_db),
) -> list[StaffUser]:
    statement = select(StaffUser).where(
        StaffUser.role == "TECHNICIAN", StaffUser.is_active.is_(True)
    )
    if principal is not None:
        statement = statement.where(StaffUser.organization_id == principal.organization_id)
    result = await db.scalars(statement.order_by(StaffUser.full_name))
    return list(result)


@router.post("/users", response_model=StaffUserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: StaffUserCreate,
    principal: StaffUser | None = Depends(require_staff_manager),
    manager=Depends(get_staff_user_manager),
    db: AsyncSession = Depends(get_async_db),
) -> StaffUser:
    organization_id = principal.organization_id if principal is not None else data.organization_id
    default_branch_id = await db.scalar(
        select(Branch.id)
        .where(Branch.organization_id == organization_id, Branch.active.is_(True))
        .order_by(Branch.code != "MAIN", Branch.created_at, Branch.id)
    )
    if default_branch_id is None:
        default_branch = Branch(
            organization_id=organization_id,
            code="MAIN",
            name="Sucursal principal",
            active=True,
        )
        db.add(default_branch)
        await db.flush()
        default_branch_id = default_branch.id
    if data.branch_id is not None:
        requested_branch = await db.scalar(
            select(Branch.id).where(
                Branch.id == data.branch_id,
                Branch.organization_id == organization_id,
                Branch.active.is_(True),
            )
        )
        if requested_branch is None:
            raise HTTPException(status_code=422, detail="La sucursal no pertenece a la empresa")
    elif data.role not in {"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT", "AUDITOR"}:
        data = data.model_copy(update={"branch_id": default_branch_id})
    if not data.employee_code:
        staff_codes = await db.scalars(select(StaffUser.employee_code).where(
            StaffUser.organization_id == organization_id, StaffUser.employee_code.like("EMP-%")
        ))
        contract_codes = await db.scalars(select(EmployeeContract.employee_code).where(
            EmployeeContract.organization_id == organization_id,
            EmployeeContract.employee_code.like("EMP-%"),
        ))
        codes = [*staff_codes, *contract_codes]
        sequence = max((int(code.removeprefix("EMP-")) for code in codes if code.removeprefix("EMP-").isdigit()), default=0) + 1
        data = data.model_copy(update={"employee_code": f"EMP-{sequence:06d}"})
    if principal is not None:
        data = data.model_copy(update={"organization_id": principal.organization_id})
    try:
        return await manager.create(data, safe=False)
    except Exception as exc:
        if "unique" in str(exc).lower() or "already" in str(exc).lower():
            raise HTTPException(status_code=409, detail="El correo o codigo de empleado ya existe") from exc
        raise


@router.patch("/users/{user_id}", response_model=StaffUserRead)
async def update_user(
    user_id: uuid.UUID,
    data: StaffUserUpdate,
    principal: StaffUser | None = Depends(require_staff_manager),
    manager=Depends(get_staff_user_manager),
) -> StaffUser:
    user = await manager.user_db.get(user_id)
    if user is None or (
        principal is not None and user.organization_id != principal.organization_id
    ):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return await manager.update(data, user, safe=False)


@router.put("/users/{user_id}/compensation", response_model=StaffCompensationRead)
async def upsert_compensation(
    user_id: uuid.UUID,
    data: StaffCompensationWrite,
    principal: StaffUser | None = Depends(require_staff_manager),
    db: AsyncSession = Depends(get_async_db),
) -> StaffCompensationProfile:
    user = await db.get(StaffUser, user_id)
    if user is None or (
        principal is not None and user.organization_id != principal.organization_id
    ):
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    result = await db.scalars(
        select(StaffCompensationProfile).where(StaffCompensationProfile.staff_user_id == user_id)
    )
    profile = result.first()
    values = data.model_dump()
    if profile is None:
        profile = StaffCompensationProfile(
            staff_user_id=user_id,
            organization_id=user.organization_id,
            **values,
        )
    else:
        for field, value in values.items():
            setattr(profile, field, value)
    if profile.standard_sale_rate < profile.standard_hourly_cost:
        raise HTTPException(status_code=422, detail="La tarifa normal no puede quedar bajo el costo real por hora")
    if profile.specialized_sale_rate < profile.specialized_hourly_cost:
        raise HTTPException(status_code=422, detail="La tarifa especializada no puede quedar bajo el costo real por hora")
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/compensation-profiles", response_model=list[StaffCompensationRead])
async def list_compensation_profiles(
    principal: StaffUser | None = Depends(require_staff_manager),
    db: AsyncSession = Depends(get_async_db),
) -> list[StaffCompensationProfile]:
    statement = select(StaffCompensationProfile)
    if principal is not None:
        statement = statement.where(
            StaffCompensationProfile.organization_id == principal.organization_id
        )
    result = await db.scalars(statement.order_by(StaffCompensationProfile.updated_at.desc()))
    return list(result)


@router.get("/access-events", response_model=list[StaffAccessEventRead])
async def access_events(
    principal: StaffUser | None = Depends(require_staff_manager),
    db: AsyncSession = Depends(get_async_db),
) -> list[StaffAccessEvent]:
    statement = select(StaffAccessEvent)
    if principal is not None:
        statement = statement.where(StaffAccessEvent.organization_id == principal.organization_id)
    result = await db.scalars(statement.order_by(StaffAccessEvent.created_at.desc()).limit(100))
    return list(result)
