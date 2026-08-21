from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, or_
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, with_loader_criteria

from app.config import get_settings
from app.request_context import current_identity


# These records represent branch-owned operational transactions. Shared masters
# (catalog, customers and document templates) remain organization scoped.
_STRICT_BRANCH_MODELS = {
    "Booking", "StoreOrder", "WorkOrder", "Quote", "CashSession", "Payment",
    "WarehouseLocation", "CounterItemRequest", "RetailSale", "ManagementDocument",
    "DocumentRender", "PurchaseOrder", "EmployeeContract", "UsedVehicle", "StaffUser",
}
_SHARED_BRANCH_MODELS = {"DocumentTemplate"}


class Base(DeclarativeBase):
    pass


def _connect_args(url: str) -> dict[str, object]:
    return {"check_same_thread": False} if url.startswith("sqlite") else {}


settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@event.listens_for(Session, "do_orm_execute")
def _isolate_tenant_reads(execute_state) -> None:
    identity = current_identity()
    if (
        not execute_state.is_select
        or execute_state.is_column_load
        or execute_state.is_relationship_load
        or identity.is_recovery
        or execute_state.execution_options.get("include_all_tenants", False)
    ):
        return
    statement = execute_state.statement
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, "organization_id"):
            # Authentication must locate the globally unique staff email/UUID
            # before a tenant context exists. Domain data remains filtered.
            if identity.actor == "anonymous" and model.__name__ in {"StaffUser", "ClientUser"}:
                continue
            organization_id = identity.organization_id
            statement = statement.options(
                with_loader_criteria(
                    model,
                    lambda candidate: candidate.organization_id == organization_id,
                    include_aliases=True,
                )
            )
        if identity.enforce_branch_scope and identity.branch_id and model.__name__ == "Branch":
            branch_id = identity.branch_id
            statement = statement.options(
                with_loader_criteria(
                    model,
                    lambda candidate: candidate.id == branch_id,
                    include_aliases=True,
                )
            )
        elif identity.enforce_branch_scope and identity.branch_id and hasattr(model, "branch_id"):
            branch_id = identity.branch_id
            if model.__name__ in _SHARED_BRANCH_MODELS:
                statement = statement.options(
                    with_loader_criteria(
                        model,
                        lambda candidate: or_(candidate.branch_id == branch_id, candidate.branch_id.is_(None)),
                        include_aliases=True,
                    )
                )
            elif model.__name__ in _STRICT_BRANCH_MODELS:
                statement = statement.options(
                    with_loader_criteria(
                        model,
                        lambda candidate: candidate.branch_id == branch_id,
                        include_aliases=True,
                    )
                )
    execute_state.statement = statement


@event.listens_for(Session, "before_flush")
def _enforce_tenant_writes(session: Session, _flush_context, _instances) -> None:
    identity = current_identity()
    for record in session.new.union(session.dirty):
        if not hasattr(type(record), "organization_id"):
            continue
        current = getattr(record, "organization_id", None)
        if not current:
            setattr(record, "organization_id", identity.organization_id)
        elif not identity.is_recovery and current != identity.organization_id:
            raise ValueError("Cross-organization write rejected")
        if (
            identity.enforce_branch_scope
            and identity.branch_id
            and type(record).__name__ in (_STRICT_BRANCH_MODELS | _SHARED_BRANCH_MODELS)
            and hasattr(record, "branch_id")
        ):
            record_branch = getattr(record, "branch_id", None)
            if not record_branch and type(record).__name__ in _STRICT_BRANCH_MODELS:
                setattr(record, "branch_id", identity.branch_id)
            elif record_branch and record_branch != identity.branch_id:
                raise ValueError("Cross-branch write rejected")


def _async_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async_engine = create_async_engine(_async_url(settings.database_url), pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
