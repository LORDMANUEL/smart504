from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def uuid_str() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class TenantMixin:
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )


class StaffUser(SQLAlchemyBaseUserTableUUID, TimestampMixin, Base):
    __tablename__ = "staff_users"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_code", name="uq_staff_org_employee_code"),
        Index("ix_staff_org_role_active", "organization_id", "role", "is_active"),
        Index("ix_staff_branch_active", "branch_id", "is_active"),
    )

    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    employee_code: Mapped[str] = mapped_column(String(40), nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(30), default="TECHNICIAN", nullable=False, index=True)
    permissions_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(500))
    session_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ClientUser(SQLAlchemyBaseUserTableUUID, TimestampMixin, Base):
    """Authenticated customer account linked to one tenant-owned customer."""

    __tablename__ = "client_users"
    __table_args__ = (
        UniqueConstraint("organization_id", "customer_id", name="uq_client_user_org_customer"),
        UniqueConstraint("organization_id", "username", name="uq_client_user_org_username"),
        Index("ix_client_user_org_active", "organization_id", "is_active"),
    )

    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(500))
    session_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    loyalty_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credit_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requested_credit_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    credit_status: Mapped[str] = mapped_column(
        String(30), default="NO_SOLICITADO", nullable=False
    )


class StaffAccessEvent(Base):
    __tablename__ = "staff_access_events"
    __table_args__ = (
        Index("ix_staff_access_user_created", "user_id", "created_at"),
        Index("ix_staff_access_action_created", "action", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("staff_users.id", ondelete="SET NULL"), index=True
    )
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )


class StaffCompensationProfile(TimestampMixin, Base):
    __tablename__ = "staff_compensation_profiles"
    __table_args__ = (
        CheckConstraint("productive_hours_monthly > 0", name="ck_staff_comp_productive_hours"),
        CheckConstraint("employer_burden_percent >= 0", name="ck_staff_comp_burden"),
        Index("ix_staff_comp_org_effective", "organization_id", "effective_from"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    staff_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff_users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    fixed_monthly_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    productive_hours_monthly: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    base_hourly_wage: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    specialized_hourly_wage: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    employer_burden_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"), nullable=False)
    standard_sale_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    specialized_sale_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    source_system: Mapped[str] = mapped_column(String(30), default="LOCAL_PROJECTION", nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(180), index=True)

    @property
    def fixed_hourly_allocation(self) -> Decimal:
        return self.fixed_monthly_salary / self.productive_hours_monthly

    def hourly_cost(self, rate_kind: str) -> Decimal:
        variable = self.specialized_hourly_wage if rate_kind == "SPECIALIZED" else self.base_hourly_wage
        return (self.fixed_hourly_allocation + variable) * (
            Decimal("1") + self.employer_burden_percent / Decimal("100")
        )

    @property
    def standard_hourly_cost(self) -> Decimal:
        return self.hourly_cost("STANDARD")

    @property
    def specialized_hourly_cost(self) -> Decimal:
        return self.hourly_cost("SPECIALIZED")


class CatalogCategory(TenantMixin, TimestampMixin, Base):
    __tablename__ = "catalog_categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_catalog_category_org_name"),
        UniqueConstraint("organization_id", "slug", name="uq_catalog_category_org_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    products: Mapped[list[CatalogProduct]] = relationship(back_populates="category")


class CatalogProduct(TenantMixin, TimestampMixin, Base):
    __tablename__ = "catalog_products"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_catalog_product_org_sku"),
        UniqueConstraint("organization_id", "slug", name="uq_catalog_product_org_slug"),
        Index("ix_catalog_product_active_category", "active", "category_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    sku: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(String(320))
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("catalog_categories.id", ondelete="SET NULL"), index=True
    )
    brand: Mapped[str | None] = mapped_column(String(100), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    landed_cost_factor: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("1.0000"), nullable=False)
    target_markup_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("30.00"), nullable=False)
    minimum_markup_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0.00"), nullable=False)
    abc_class: Mapped[str] = mapped_column(String(1), default="C", nullable=False, index=True)
    xyz_class: Mapped[str] = mapped_column(String(1), default="Z", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    stock_qty: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0.000"))
    stock_status: Mapped[str] = mapped_column(String(30), default="IN_STOCK", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    compatibility_notes: Mapped[str | None] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(String(30), default="LOCAL", nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    category: Mapped[CatalogCategory | None] = relationship(back_populates="products")
    images: Mapped[list[CatalogProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="CatalogProductImage.sort_order",
    )


class CatalogProductImage(TenantMixin, TimestampMixin, Base):
    __tablename__ = "catalog_product_images"
    __table_args__ = (UniqueConstraint("product_id", "sha256", name="uq_product_image_sha256"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(String(700), nullable=False)
    alt_text: Mapped[str] = mapped_column(String(240), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_page_url: Mapped[str | None] = mapped_column(String(1000))
    attribution_text: Mapped[str | None] = mapped_column(String(500))
    license_name: Mapped[str | None] = mapped_column(String(120))
    license_url: Mapped[str | None] = mapped_column(String(1000))
    mime_type: Mapped[str] = mapped_column(String(60), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped[CatalogProduct] = relationship(back_populates="images")


class Customer(TenantMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    tax_id: Mapped[str | None] = mapped_column(String(80), index=True)
    erpnext_customer_id: Mapped[str | None] = mapped_column(String(180), index=True)

    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="customer")


class Vehicle(TenantMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("organization_id", "vin", name="uq_vehicle_org_vin"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vin: Mapped[str | None] = mapped_column(String(40), index=True)
    plate: Mapped[str | None] = mapped_column(String(30), index=True)
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_year: Mapped[int | None] = mapped_column(Integer)
    engine: Mapped[str | None] = mapped_column(String(120))
    transmission: Mapped[str | None] = mapped_column(String(120))
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    photo_url: Mapped[str | None] = mapped_column(String(1000))

    customer: Mapped[Customer] = relationship(back_populates="vehicles")


class Booking(TenantMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(254))
    vehicle_summary: Mapped[str] = mapped_column(String(240), nullable=False)
    service_requested: Mapped[str] = mapped_column(String(180), nullable=False)
    preferred_date: Mapped[str | None] = mapped_column(String(30))
    concern: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False)
    source: Mapped[str] = mapped_column(String(30), default="WEB", nullable=False)
    customer_id: Mapped[str | None] = mapped_column(String(36), index=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(80), index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )


class StoreOrder(TenantMixin, TimestampMixin, Base):
    __tablename__ = "store_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "order_number", name="uq_store_order_org_number"),
        UniqueConstraint("organization_id", "idempotency_key", name="uq_store_order_org_idempotency"),
        Index("ix_store_orders_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    order_number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(254))
    vehicle_vin: Mapped[str | None] = mapped_column(String(40), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(40), default="PENDING_CONFIRMATION", nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(30), default="WEB", nullable=False)
    erpnext_sales_order_id: Mapped[str | None] = mapped_column(String(180), index=True)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_cashier: Mapped[str | None] = mapped_column(String(120), index=True)
    fulfillment_status: Mapped[str] = mapped_column(
        String(40), default="AWAITING_REVIEW", nullable=False, index=True
    )
    reservation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    whatsapp_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )

    items: Mapped[list[StoreOrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="StoreOrderItem.created_at",
    )


class StoreOrderItem(TenantMixin, Base):
    __tablename__ = "store_order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("store_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    order: Mapped[StoreOrder] = relationship(back_populates="items")
    product: Mapped[CatalogProduct] = relationship()


class WorkshopSetting(TimestampMixin, Base):
    __tablename__ = "workshop_settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class WorkOrder(TenantMixin, TimestampMixin, Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_work_order_org_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    concern: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(Text)
    technician_quote: Mapped[dict[str, object] | None] = mapped_column(JSON)
    parts_required: Mapped[list[dict[str, object]] | None] = mapped_column(JSON)
    assigned_technicians: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    bay_code: Mapped[str | None] = mapped_column(String(40), index=True)
    promised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invoice_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    erpnext_service_order_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erpnext_invoice_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False, index=True
    )
    erp_sync_error: Mapped[str | None] = mapped_column(String(500))
    erp_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    customer: Mapped[Customer] = relationship()
    vehicle: Mapped[Vehicle] = relationship()
    events: Mapped[list[WorkOrderEvent]] = relationship(
        back_populates="work_order",
        cascade="all, delete-orphan",
        order_by="WorkOrderEvent.created_at",
    )

    @property
    def external_reference(self) -> str:
        return self.number

    @property
    def customer_name(self) -> str:
        return self.customer.full_name if self.customer else self.customer_id

    @property
    def vehicle_label(self) -> str:
        if not self.vehicle:
            return self.vehicle_id
        year = f" {self.vehicle.model_year}" if self.vehicle.model_year else ""
        plate = f" · {self.vehicle.plate}" if self.vehicle.plate else ""
        return f"{self.vehicle.make} {self.vehicle.model}{year}{plate}".strip()

    @property
    def technician_name(self) -> str | None:
        return self.assigned_technicians[0] if self.assigned_technicians else None

    @property
    def quote_total(self) -> str | None:
        quote = self.technician_quote or {}
        value = quote.get("grand_total", quote.get("total"))
        return str(value) if value is not None else None

    @property
    def version(self) -> int:
        return 1


class WorkOrderEvent(TenantMixin, Base):
    __tablename__ = "work_order_events"
    __table_args__ = (
        UniqueConstraint("work_order_id", "idempotency_key", name="uq_work_order_event_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    work_order_id: Mapped[str] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(50))
    to_status: Mapped[str | None] = mapped_column(String(50))
    actor: Mapped[str] = mapped_column(String(180), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    work_order: Mapped[WorkOrder] = relationship(back_populates="events")


class LaborCatalogItem(TenantMixin, TimestampMixin, Base):
    __tablename__ = "labor_catalog_items"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_labor_catalog_org_code"),
        CheckConstraint("standard_hours > 0", name="ck_labor_catalog_hours"),
        CheckConstraint("sale_price >= 0", name="ck_labor_catalog_sale_price"),
        CheckConstraint("internal_cost >= 0", name="ck_labor_catalog_internal_cost"),
        Index("ix_labor_catalog_org_active", "organization_id", "is_active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    standard_hours: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    internal_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Empty rules mean that the service applies to every vehicle. Rules are
    # persisted so each company can limit a service by make/model/year.
    vehicle_rules: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    erp_item_code: Mapped[str | None] = mapped_column(String(140), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkOrderLaborEntry(Base):
    __tablename__ = "work_order_labor_entries"
    __table_args__ = (
        CheckConstraint("hours > 0", name="ck_work_order_labor_hours"),
        Index("ix_work_order_labor_technician_created", "technician_user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    work_order_id: Mapped[str] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technician_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff_users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    technician_name: Mapped[str] = mapped_column(String(180), nullable=False)
    service_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    rate_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    hourly_cost_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    hourly_sale_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    @property
    def cost_total(self) -> Decimal:
        return self.hours * self.hourly_cost_snapshot

    @property
    def sale_total(self) -> Decimal:
        return self.hours * self.hourly_sale_rate


class Quote(TenantMixin, TimestampMixin, Base):
    __tablename__ = "quotes"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_quote_org_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    work_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), index=True)
    converted_work_order_id: Mapped[str | None] = mapped_column(ForeignKey("work_orders.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(120))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erpnext_quotation_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False, index=True
    )
    erp_sync_error: Mapped[str | None] = mapped_column(String(500))
    erp_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lines: Mapped[list[QuoteLine]] = relationship(
        back_populates="quote", cascade="all, delete-orphan", order_by="QuoteLine.created_at"
    )

    @property
    def subtotal(self) -> Decimal:
        return sum((line.line_total for line in self.lines), Decimal("0.00"))

    @property
    def total(self) -> Decimal:
        return self.subtotal - self.discount + self.tax


class QuoteLine(TenantMixin, Base):
    __tablename__ = "quote_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    quote_id: Mapped[str] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_type: Mapped[str] = mapped_column(String(30), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    approval_status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False, index=True
    )
    source_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    quote: Mapped[Quote] = relationship(back_populates="lines")

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


class CashSession(TenantMixin, TimestampMixin, Base):
    __tablename__ = "cash_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    opened_by: Mapped[str] = mapped_column(String(120), nullable=False)
    closed_by: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False, index=True)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    counted_cash: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_cash: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    difference: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Payment(TenantMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("organization_id", "receipt_number", name="uq_payment_org_receipt"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    receipt_number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cash_session_id: Mapped[str] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    work_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    quote_id: Mapped[str | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"), index=True
    )
    retail_sale_id: Mapped[str | None] = mapped_column(
        ForeignKey("retail_sales.id", ondelete="RESTRICT"), index=True
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(30), default="CAPTURED", nullable=False)
    received_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_branch_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(40))
    email_domain: Mapped[str | None] = mapped_column(String(180))
    timezone: Mapped[str] = mapped_column(String(80), default="America/Tegucigalpa", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WarehouseLocation(TenantMixin, TimestampMixin, Base):
    __tablename__ = "warehouse_locations"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouse_org_code"),
        Index("ix_warehouse_branch_type", "branch_id", "warehouse_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    warehouse_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InventoryBalance(TimestampMixin, Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_inventory_balance_warehouse_product"),
        Index("ix_inventory_balance_org_product", "organization_id", "product_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_on_hand: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), default=Decimal("0.000"), nullable=False
    )
    quantity_reserved: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), default=Decimal("0.000"), nullable=False
    )
    source_system: Mapped[str] = mapped_column(String(30), default="LOCAL_PROJECTION", nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(180), index=True)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (Index("ix_inventory_movement_reference_created", "reference", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reference: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    erpnext_stock_entry_id: Mapped[str | None] = mapped_column(String(180), index=True)
    sync_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CounterItemRequest(TenantMixin, TimestampMixin, Base):
    """Demanda de mostrador que compras debe atender sin crear artículos improvisados."""

    __tablename__ = "counter_item_requests"
    __table_args__ = (
        Index("ix_counter_item_request_org_status", "organization_id", "status"),
        Index("ix_counter_item_request_branch_created", "branch_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[str | None] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("catalog_products.id", ondelete="SET NULL"), index=True)
    search_query: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), index=True)
    vehicle_vin: Mapped[str | None] = mapped_column(String(40), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)


class RetailSale(TimestampMixin, Base):
    __tablename__ = "retail_sales"
    __table_args__ = (
        UniqueConstraint("organization_id", "sale_number", name="uq_retail_sale_org_number"),
        UniqueConstraint("organization_id", "invoice_number", name="uq_retail_sale_org_invoice"),
        Index("ix_retail_sale_org_created", "organization_id", "created_at"),
        Index("ix_retail_sale_branch_status", "branch_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cash_session_id: Mapped[str] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), index=True)
    tax_id: Mapped[str | None] = mapped_column(String(80), index=True)
    vehicle_vin: Mapped[str | None] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    payment_reference: Mapped[str | None] = mapped_column(String(180))
    erpnext_invoice_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erpnext_payment_id: Mapped[str | None] = mapped_column(String(180), index=True)
    sync_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    sync_error: Mapped[str | None] = mapped_column(String(500))
    sync_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    items: Mapped[list[RetailSaleItem]] = relationship(
        back_populates="sale", cascade="all, delete-orphan", order_by="RetailSaleItem.created_at"
    )
    returns: Mapped[list[RetailReturn]] = relationship(
        back_populates="sale", cascade="all, delete-orphan", order_by="RetailReturn.created_at"
    )


class RetailSaleItem(TenantMixin, Base):
    __tablename__ = "retail_sale_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    sale_id: Mapped[str] = mapped_column(
        ForeignKey("retail_sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    returned_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), default=Decimal("0.000"), nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    sale: Mapped[RetailSale] = relationship(back_populates="items")
    product: Mapped[CatalogProduct] = relationship()


class RetailReturn(TenantMixin, TimestampMixin, Base):
    __tablename__ = "retail_returns"
    __table_args__ = (
        UniqueConstraint("organization_id", "return_number", name="uq_retail_return_org_number"),
        Index("ix_retail_return_sale_created", "sale_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    sale_id: Mapped[str] = mapped_column(
        ForeignKey("retail_sales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    return_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(180))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    erpnext_credit_note_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erpnext_payment_id: Mapped[str | None] = mapped_column(String(180), index=True)
    sync_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    sync_error: Mapped[str | None] = mapped_column(String(500))
    sync_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    sale: Mapped[RetailSale] = relationship(back_populates="returns")
    items: Mapped[list[RetailReturnItem]] = relationship(
        back_populates="return_record", cascade="all, delete-orphan"
    )

    @property
    def sale_status(self) -> str:
        return self.sale.status


class RetailReturnItem(TenantMixin, Base):
    __tablename__ = "retail_return_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    return_id: Mapped[str] = mapped_column(
        ForeignKey("retail_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sale_item_id: Mapped[str] = mapped_column(
        ForeignKey("retail_sale_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_refund: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    return_record: Mapped[RetailReturn] = relationship(back_populates="items")


class ApprovalRequest(TenantMixin, TimestampMixin, Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        Index("ix_approval_request_status_created", "status", "created_at"),
        Index("ix_approval_request_sale_type", "sale_id", "request_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    sale_id: Mapped[str] = mapped_column(
        ForeignKey("retail_sales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    request_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    delivery_status: Mapped[str] = mapped_column(String(40), default="PENDING", nullable=False)
    delivery_error: Mapped[str | None] = mapped_column(String(500))
    decided_by: Mapped[str | None] = mapped_column(String(254))
    decision_comment: Mapped[str | None] = mapped_column(String(500))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InventoryReservation(TenantMixin, TimestampMixin, Base):
    __tablename__ = "inventory_reservations"
    __table_args__ = (
        UniqueConstraint("organization_id", "reference", name="uq_inventory_reservation_org_ref"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    reference: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    store_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("store_orders.id", ondelete="CASCADE"), index=True
    )
    work_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="RESERVED", nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)


class InventoryTransfer(TenantMixin, TimestampMixin, Base):
    __tablename__ = "inventory_transfers"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_inventory_transfer_org_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    from_warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="REQUESTED", nullable=False, index=True)
    items_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    carrier: Mapped[str | None] = mapped_column(String(160))
    tracking_number: Mapped[str | None] = mapped_column(String(180), index=True)
    guide_image_url: Mapped[str | None] = mapped_column(String(1000))
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    erpnext_stock_entry_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(
        String(30), default="NOT_REQUIRED", nullable=False, index=True
    )
    erp_sync_error: Mapped[str | None] = mapped_column(String(500))
    erp_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Shipment(TenantMixin, TimestampMixin, Base):
    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_shipment_org_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    store_order_id: Mapped[str] = mapped_column(
        ForeignKey("store_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="PREPARING", nullable=False, index=True)
    carrier: Mapped[str] = mapped_column(String(160), nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(String(180), index=True)
    guide_image_url: Mapped[str | None] = mapped_column(String(1000))
    recipient_name: Mapped[str] = mapped_column(String(180), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(40), nullable=False)
    delivery_notes: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)


class QualityCase(TenantMixin, TimestampMixin, Base):
    __tablename__ = "quality_cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_quality_case_org_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    case_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    vehicle_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), index=True
    )
    work_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="SET NULL"), index=True
    )
    store_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("store_orders.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str | None] = mapped_column(Text)
    evidence_url: Mapped[str | None] = mapped_column(String(1000))
    actor: Mapped[str] = mapped_column(String(120), nullable=False)


class VehicleHistoryEvent(TenantMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_history_events"
    __table_args__ = (Index("ix_vehicle_history_vin_created", "vin", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    vehicle_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), index=True
    )
    vin: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    reference: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    quality_result: Mapped[str | None] = mapped_column(String(60))
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class SalesLead(TenantMixin, TimestampMixin, Base):
    __tablename__ = "sales_leads"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_sales_lead_org_number"),
        Index("ix_sales_leads_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    interest: Mapped[str] = mapped_column(String(500), nullable=False)
    vehicle_summary: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False, index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(120), index=True)
    chat_session_id: Mapped[str | None] = mapped_column(String(36), index=True)
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class ManagementDocument(TenantMixin, TimestampMixin, Base):
    __tablename__ = "management_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    branch_id: Mapped[str] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(180), nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    file_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class DocumentTemplate(TimestampMixin, Base):
    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_document_template_org_code"),
        Index("ix_document_template_scope_type", "organization_id", "branch_id", "document_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    document_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    published_version: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    versions: Mapped[list[DocumentTemplateVersion]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="DocumentTemplateVersion.version.desc()",
    )


class DocumentTemplateVersion(TenantMixin, Base):
    __tablename__ = "document_template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_document_template_version"),
        Index("ix_document_template_version_status", "template_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    template_id: Mapped[str] = mapped_column(
        ForeignKey("document_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    paper_size: Mapped[str] = mapped_column(String(20), default="LETTER", nullable=False)
    print_profile_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)
    css_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    variables_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    template: Mapped[DocumentTemplate] = relationship(back_populates="versions")


class DocumentRender(Base):
    __tablename__ = "document_renders"
    __table_args__ = (
        Index("ix_document_render_reference_created", "business_reference", "created_at"),
        Index("ix_document_render_type_created", "document_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(60), default="SMARTDIAG504", nullable=False, index=True
    )
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), index=True
    )
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), index=True
    )
    template_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_template_versions.id", ondelete="SET NULL"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    business_reference: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    html_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )


class NodeHeartbeat(Base):
    __tablename__ = "node_heartbeats"

    node_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )


class LeaderLease(Base):
    __tablename__ = "leader_leases"

    lease_name: Mapped[str] = mapped_column(String(120), primary_key=True)
    holder_node_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fencing_token: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class FlowEvent(TenantMixin, Base):
    __tablename__ = "flow_events"
    __table_args__ = (
        Index("ix_flow_events_module_created", "module", "created_at"),
        Index("ix_flow_events_item_created", "item_reference", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    item_reference: Mapped[str] = mapped_column(String(120), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False, default="SUCCESS")
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )


class ErpIntegrationJob(TenantMixin, TimestampMixin, Base):
    __tablename__ = "erp_integration_jobs"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "idempotency_key", name="uq_erp_job_org_idempotency"
        ),
        Index("ix_erp_job_org_status_created", "organization_id", "status", "created_at"),
        Index("ix_erp_job_aggregate", "aggregate_type", "aggregate_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    aggregate_type: Mapped[str] = mapped_column(String(40), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(120), nullable=False)
    operation: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    last_error: Mapped[str | None] = mapped_column(String(500))
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class NotificationDelivery(TenantMixin, TimestampMixin, Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_notification_org_idempotency"),
        Index("ix_notification_org_status_scheduled", "organization_id", "status", "scheduled_at"),
        Index("ix_notification_aggregate", "aggregate_type", "aggregate_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(240))
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    template_key: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(40), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    last_error: Mapped[str | None] = mapped_column(String(500))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ChatSession(TenantMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (Index("ix_chat_sessions_status_expires", "status", "expires_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    channel: Mapped[str] = mapped_column(String(30), default="PUBLIC_WEB", nullable=False)
    locale: Mapped[str] = mapped_column(String(20), default="es-HN", nullable=False)
    page_url: Mapped[str | None] = mapped_column(String(1000))
    referrer: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False, index=True)
    accepted_privacy_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    rate_window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    rate_window_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(TenantMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "client_message_id", name="uq_chat_message_client_id"),
        UniqueConstraint("reply_to_message_id", name="uq_chat_message_reply"),
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(128))
    reply_to_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(120))
    mode: Mapped[str | None] = mapped_column(String(40))
    audit_id: Mapped[str | None] = mapped_column(String(80), index=True)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suggested_actions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sources: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class Supplier(TenantMixin, TimestampMixin, Base):
    """Operational supplier directory; ERPNext remains authoritative after sync."""

    __tablename__ = "suppliers"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_supplier_org_code"),
        Index("ix_supplier_org_active_name", "organization_id", "active", "name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(80), index=True)
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(40))
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    erpnext_supplier_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    erp_sync_error: Mapped[str | None] = mapped_column(String(500))


class PurchaseOrder(TenantMixin, TimestampMixin, Base):
    """Purchasing workflow projection. It never represents accounts payable locally."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_purchase_order_org_number"),
        Index("ix_purchase_order_org_status_created", "organization_id", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(14, 6), default=Decimal("1"), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    expected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    items_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    erpnext_purchase_order_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(String(30), default="NOT_REQUIRED", nullable=False, index=True)
    erp_sync_error: Mapped[str | None] = mapped_column(String(500))
    erp_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportCase(TenantMixin, TimestampMixin, Base):
    __tablename__ = "import_cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_import_case_org_number"),
        Index("ix_import_case_org_status_eta", "organization_id", "status", "eta"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    purchase_order_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PLANNED", nullable=False, index=True)
    incoterm: Mapped[str] = mapped_column(String(10), nullable=False)
    origin_country: Mapped[str] = mapped_column(String(80), nullable=False)
    destination_port: Mapped[str] = mapped_column(String(120), nullable=False)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    costs_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    documents_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    additional_cost_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    allocation_method: Mapped[str] = mapped_column(String(30), default="BY_VALUE", nullable=False)
    landed_cost_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    erpnext_landed_cost_id: Mapped[str | None] = mapped_column(String(180), index=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)


class EmployeeContract(TenantMixin, TimestampMixin, Base):
    __tablename__ = "employee_contracts"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_code", name="uq_employee_contract_org_code"),
        Index("ix_employee_contract_org_status", "organization_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    staff_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_users.id", ondelete="SET NULL"), index=True)
    employee_code: Mapped[str] = mapped_column(String(60), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(180), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    national_id: Mapped[str | None] = mapped_column(String(80), index=True)
    address: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    social_security_number: Mapped[str | None] = mapped_column(String(80))
    insurance_provider: Mapped[str | None] = mapped_column(String(120))
    insurance_member_number: Mapped[str | None] = mapped_column(String(120))
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    monthly_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(30), default="MONTHLY", nullable=False)
    base_pay_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    standard_hours_weekly: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="HNL", nullable=False)
    benefits_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    schedule_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    erpnext_employee_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)


class AttendanceEntry(TenantMixin, TimestampMixin, Base):
    __tablename__ = "attendance_entries"
    __table_args__ = (
        UniqueConstraint("organization_id", "contract_id", "work_date", name="uq_attendance_contract_date"),
        Index("ix_attendance_org_date", "organization_id", "work_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    contract_id: Mapped[str] = mapped_column(ForeignKey("employee_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    overtime_status: Mapped[str] = mapped_column(String(30), default="NOT_REQUIRED", nullable=False, index=True)
    overtime_approved_by: Mapped[str | None] = mapped_column(String(120))
    overtime_approval_note: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="PRESENT", nullable=False)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(String(500))
    recorded_by: Mapped[str] = mapped_column(String(120), nullable=False)


class LeaveRequest(TenantMixin, TimestampMixin, Base):
    __tablename__ = "leave_requests"
    __table_args__ = (Index("ix_leave_org_status_start", "organization_id", "status", "start_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    contract_id: Mapped[str] = mapped_column(ForeignKey("employee_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(40), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(120))


class PayrollRun(TenantMixin, TimestampMixin, Base):
    """Payroll review projection. Journal and payment entries are created only in ERPNext."""

    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("organization_id", "number", name="uq_payroll_run_org_number"),
        Index("ix_payroll_org_status_period", "organization_id", "status", "period_start"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    lines_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    gross_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    deduction_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    net_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(120))
    approved_by: Mapped[str | None] = mapped_column(String(120))
    posted_by: Mapped[str | None] = mapped_column(String(120))
    erpnext_payroll_entry_id: Mapped[str | None] = mapped_column(String(180), index=True)
    erp_sync_status: Mapped[str] = mapped_column(String(30), default="NOT_REQUIRED", nullable=False, index=True)


class PayrollPolicy(TenantMixin, TimestampMixin, Base):
    """Versioned payroll inputs approved by the accountant; never a hidden legal constant."""

    __tablename__ = "payroll_policies"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", "effective_from", name="uq_payroll_policy_org_code_effective"),
        Index("ix_payroll_policy_org_active_effective", "organization_id", "active", "effective_from"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date)
    rules_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    approved_by: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PayrollVoucher(TenantMixin, TimestampMixin, Base):
    __tablename__ = "payroll_vouchers"
    __table_args__ = (
        UniqueConstraint("payroll_run_id", "contract_id", name="uq_payroll_voucher_run_contract"),
        UniqueConstraint("organization_id", "number", name="uq_payroll_voucher_org_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    payroll_run_id: Mapped[str] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("employee_contracts.id", ondelete="RESTRICT"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    employer_contributions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    net: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsedVehicle(TenantMixin, TimestampMixin, Base):
    __tablename__ = "used_vehicles"
    __table_args__ = (
        UniqueConstraint("organization_id", "vin", name="uq_used_vehicle_org_vin"),
        Index("ix_used_vehicle_org_status", "organization_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    vin: Mapped[str] = mapped_column(String(32), nullable=False)
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_year: Mapped[int] = mapped_column(Integer, nullable=False)
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    acquisition_type: Mapped[str] = mapped_column(String(30), nullable=False)
    acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reconditioning_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    target_sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="APPRAISAL", nullable=False, index=True)
    owner_name: Mapped[str | None] = mapped_column(String(180))
    inspection_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    media_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erpnext_item_id: Mapped[str | None] = mapped_column(String(180), index=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)


class SocialChannel(TenantMixin, TimestampMixin, Base):
    __tablename__ = "social_channels"
    __table_args__ = (
        UniqueConstraint("organization_id", "channel_type", "external_account_id", name="uq_social_channel_account"),
        Index("ix_social_channel_org_active", "organization_id", "active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(180), nullable=False)
    credential_reference: Mapped[str] = mapped_column(String(300), nullable=False)
    webhook_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SocialConversation(TenantMixin, TimestampMixin, Base):
    __tablename__ = "social_conversations"
    __table_args__ = (Index("ix_social_conversation_org_status_updated", "organization_id", "status", "updated_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    channel_id: Mapped[str] = mapped_column(ForeignKey("social_channels.id", ondelete="RESTRICT"), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(180), nullable=False)
    contact_handle: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False, index=True)
    consent_status: Mapped[str] = mapped_column(String(30), default="UNKNOWN", nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(120), index=True)
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("sales_leads.id", ondelete="SET NULL"), index=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SocialMessage(TenantMixin, Base):
    __tablename__ = "social_messages"
    __table_args__ = (Index("ix_social_message_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("social_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)
    human_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    sent_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
