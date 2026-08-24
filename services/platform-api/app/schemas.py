from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = Field(default=None, max_length=1000)
    active: bool = True
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = Field(default=None, max_length=1000)
    active: bool | None = None
    sort_order: int | None = None


class CategoryRead(ORMModel):
    id: str
    name: str
    slug: str
    description: str | None
    active: bool
    sort_order: int


class ProductImageRead(ORMModel):
    id: str
    public_url: str
    alt_text: str
    source_type: str
    source_url: str | None
    source_page_url: str | None
    attribution_text: str | None
    license_name: str | None
    license_url: str | None
    mime_type: str
    width: int
    height: int
    is_primary: bool
    sort_order: int


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=180)
    short_description: str | None = Field(default=None, max_length=320)
    description: str | None = Field(default=None, max_length=5000)
    category_id: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    price: Decimal = Field(default=Decimal("0.00"), ge=0)
    purchase_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    landed_cost_factor: Decimal = Field(default=Decimal("1.00"), ge=1, le=100)
    target_markup_percent: Decimal = Field(default=Decimal("30.00"), ge=0, le=1000)
    minimum_markup_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=1000)
    abc_class: Literal["A", "B", "C"] = "C"
    xyz_class: Literal["X", "Y", "Z"] = "Z"
    currency: str = Field(default="HNL", min_length=3, max_length=3)
    stock_qty: Decimal = Field(default=Decimal("0.000"), ge=0)
    stock_status: str = Field(default="IN_STOCK", max_length=30)
    active: bool = True
    featured: bool = False
    compatibility_notes: str | None = Field(default=None, max_length=3000)
    source_system: str = Field(default="LOCAL", max_length=30)
    source_reference: str | None = Field(default=None, max_length=180)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=180)
    short_description: str | None = Field(default=None, max_length=320)
    description: str | None = Field(default=None, max_length=5000)
    category_id: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    price: Decimal | None = Field(default=None, ge=0)
    purchase_cost: Decimal | None = Field(default=None, ge=0)
    landed_cost_factor: Decimal | None = Field(default=None, ge=1, le=100)
    target_markup_percent: Decimal | None = Field(default=None, ge=0, le=1000)
    minimum_markup_percent: Decimal | None = Field(default=None, ge=0, le=1000)
    abc_class: Literal["A", "B", "C"] | None = None
    xyz_class: Literal["X", "Y", "Z"] | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    stock_qty: Decimal | None = Field(default=None, ge=0)
    stock_status: str | None = Field(default=None, max_length=30)
    active: bool | None = None
    featured: bool | None = None
    compatibility_notes: str | None = Field(default=None, max_length=3000)
    source_system: str | None = Field(default=None, max_length=30)
    source_reference: str | None = Field(default=None, max_length=180)


class ProductRead(ORMModel):
    id: str
    sku: str
    slug: str
    name: str
    short_description: str | None
    description: str | None
    category_id: str | None
    brand: str | None
    price: Decimal
    purchase_cost: Decimal
    landed_cost_factor: Decimal
    target_markup_percent: Decimal
    minimum_markup_percent: Decimal
    abc_class: str
    xyz_class: str
    currency: str
    stock_qty: Decimal
    stock_status: str
    active: bool
    featured: bool
    compatibility_notes: str | None
    source_system: str
    source_reference: str | None
    version: int
    images: list[ProductImageRead] = []


class BookingCreate(BaseModel):
    website: str | None = Field(default=None, max_length=0, exclude=True)
    full_name: str = Field(min_length=3, max_length=180)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr | None = None
    vehicle_summary: str = Field(min_length=3, max_length=240)
    service_requested: str = Field(min_length=2, max_length=180)
    preferred_date: str | None = Field(default=None, max_length=30)
    concern: str = Field(min_length=8, max_length=3000)


class BookingRead(ORMModel):
    id: str
    status: str
    created_at: datetime


class BookingAdminRead(BookingRead):
    full_name: str
    phone: str
    email: str | None
    vehicle_summary: str
    service_requested: str
    preferred_date: str | None
    concern: str
    source: str
    customer_id: str | None
    vehicle_id: str | None
    scheduled_at: datetime | None
    duration_minutes: int | None
    updated_at: datetime


class BookingStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(NEW|CONTACTED|CONFIRMED|CANCELLED)$")
    actor: str = Field(min_length=2, max_length=120)


class LaborCatalogRead(BaseModel):
    code: str
    description: str
    hours: Decimal
    price: Decimal


class ClientAppointmentCreate(BaseModel):
    vehicle_id: str = Field(min_length=2, max_length=80)
    vehicle_summary: str = Field(min_length=3, max_length=240)
    service_requested: str = Field(min_length=2, max_length=180)
    scheduled_at: datetime
    concern: str = Field(min_length=8, max_length=3000)


class ClientAppointmentRead(ORMModel):
    id: str
    vehicle_id: str | None
    vehicle_summary: str
    service_requested: str
    scheduled_at: datetime | None
    duration_minutes: int | None
    concern: str
    status: str
    source: str
    created_at: datetime


class StoreOrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=20)


class StoreOrderCreate(BaseModel):
    website: str | None = Field(default=None, max_length=0, exclude=True)
    customer_name: str = Field(min_length=3, max_length=180)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr | None = None
    vehicle_vin: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str = Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    items: list[StoreOrderItemCreate] = Field(min_length=1, max_length=50)


class StoreOrderItemRead(ORMModel):
    id: str
    product_id: str
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class StoreOrderRead(ORMModel):
    id: str
    order_number: str
    customer_name: str
    phone: str
    email: str | None
    vehicle_vin: str | None
    notes: str | None
    status: str
    currency: str
    subtotal: Decimal
    erpnext_sales_order_id: str | None
    source: str
    branch_id: str | None
    assigned_cashier: str | None
    fulfillment_status: str
    reservation_expires_at: datetime | None
    whatsapp_status: str
    customer_id: str | None
    created_at: datetime
    updated_at: datetime
    items: list[StoreOrderItemRead] = Field(default_factory=list)


class StoreOrderStatusUpdate(BaseModel):
    status: Literal[
        "PENDING_CONFIRMATION",
        "CONTACTED",
        "CONFIRMED",
        "PAID",
        "RESERVED",
        "PREPARING",
        "SHIPPED",
        "DELIVERED",
        "RETURN_REQUESTED",
        "RETURNED",
        "SYNCED",
        "NO_RESPONSE",
        "LOST",
        "CANCELLED",
    ]
    erpnext_sales_order_id: str | None = Field(default=None, max_length=180)
    assigned_cashier: str | None = Field(default=None, max_length=120)
    whatsapp_status: Literal["PENDING", "SENT", "CONFIRMED", "FAILED"] | None = None
    actor: str = Field(default="caja", min_length=2, max_length=120)


class ImageImportRequest(BaseModel):
    image_url: HttpUrl
    alt_text: str = Field(min_length=2, max_length=240)
    source_page_url: HttpUrl | None = None
    attribution_text: str | None = Field(default=None, max_length=500)
    license_name: str | None = Field(default=None, max_length=120)
    license_url: HttpUrl | None = None
    make_primary: bool = False


class ImageReorderRequest(BaseModel):
    image_ids: list[str] = Field(min_length=1, max_length=30)
    primary_image_id: str | None = None


class GoogleImageResult(BaseModel):
    title: str
    image_url: str
    thumbnail_url: str | None = None
    source_page_url: str
    display_link: str | None = None
    width: int | None = None
    height: int | None = None


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=180)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr | None = None
    tax_id: str | None = Field(default=None, max_length=80)


class CustomerRead(ORMModel):
    id: str
    full_name: str
    phone: str
    email: str | None
    tax_id: str | None


class VehicleCreate(BaseModel):
    customer_id: str
    vin: str | None = Field(default=None, max_length=40)
    plate: str | None = Field(default=None, max_length=30)
    make: str = Field(min_length=2, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    model_year: int | None = Field(default=None, ge=1900, le=2100)
    engine: str | None = Field(default=None, max_length=120)
    transmission: str | None = Field(default=None, max_length=120)
    mileage_km: int | None = Field(default=None, ge=0)


class VehicleRead(ORMModel):
    id: str
    customer_id: str
    vin: str | None
    plate: str | None
    make: str
    model: str
    model_year: int | None
    mileage_km: int | None


class WorkOrderCreate(BaseModel):
    number: str | None = Field(default=None, max_length=40)
    customer_id: str
    vehicle_id: str
    title: str = Field(min_length=3, max_length=220)
    concern: str = Field(min_length=5, max_length=5000)
    assigned_technicians: list[str] = Field(default_factory=list, max_length=10)
    bay_code: str | None = Field(default=None, max_length=40)
    promised_at: datetime | None = None
    actor: str = Field(min_length=2, max_length=180)


class WorkOrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=220)
    concern: str | None = Field(default=None, min_length=5, max_length=5000)
    diagnosis: str | None = Field(default=None, max_length=10000)
    technician_quote: dict[str, object] | None = None
    parts_required: list[dict[str, object]] | None = None
    assigned_technicians: list[str] | None = Field(default=None, max_length=10)
    bay_code: str | None = Field(default=None, max_length=40)
    promised_at: datetime | None = None


class WorkOrderTransition(BaseModel):
    to_status: str
    actor: str = Field(min_length=2, max_length=180)
    reason: str = Field(min_length=3, max_length=500)
    invoice_reference: str | None = Field(default=None, max_length=180)
    idempotency_key: str = Field(min_length=6, max_length=128)


class WorkOrderPartRequestCreate(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=20)
    note: str | None = Field(default=None, max_length=1000)
    actor: str = Field(min_length=2, max_length=120)


class WorkOrderPartDelivery(BaseModel):
    actor: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=120)


class WorkOrderPartStatusUpdate(BaseModel):
    status: Literal["REQUESTED", "PICKING", "READY", "DELIVERED", "RETURN_REQUESTED", "RETURNED", "RECEIVED"]
    actor: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


class WorkOrderLaborCreate(BaseModel):
    technician_id: UUID
    service_code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    rate_kind: Literal["STANDARD", "SPECIALIZED"] = "STANDARD"
    actor: str = Field(min_length=2, max_length=120)


class WorkOrderCheckInCreate(BaseModel):
    mileage_km: int = Field(ge=0, le=5_000_000)
    fuel_percent: int = Field(ge=0, le=100)
    accessories: list[str] = Field(default_factory=list, max_length=40)
    exterior_notes: str = Field(default="", max_length=3000)
    customer_name: str = Field(min_length=3, max_length=180)
    customer_accepted: bool
    actor: str = Field(min_length=2, max_length=120)


class WorkOrderTimerAction(BaseModel):
    action: Literal["START", "PAUSE", "RESUME", "STOP"]
    note: str = Field(default="", max_length=500)
    actor: str = Field(min_length=2, max_length=120)


class WorkOrderQualityCreate(BaseModel):
    checklist: dict[str, bool] = Field(min_length=1, max_length=50)
    road_test_required: bool = False
    road_test_result: Literal["NOT_REQUIRED", "PASS", "FAIL"] = "NOT_REQUIRED"
    notes: str = Field(default="", max_length=3000)
    result: Literal["PASS", "FAIL"]
    actor: str = Field(min_length=2, max_length=120)


class WorkOrderLaborRead(ORMModel):
    id: str
    work_order_id: str
    technician_user_id: UUID
    technician_name: str
    service_code: str
    description: str
    rate_kind: str
    hours: Decimal
    hourly_sale_rate: Decimal
    sale_total: Decimal
    actor: str
    created_at: datetime


class WorkOrderEventRead(ORMModel):
    id: str
    event_type: str
    from_status: str | None
    to_status: str | None
    actor: str
    reason: str
    idempotency_key: str
    payload: dict[str, object]
    created_at: datetime


class WorkOrderRead(ORMModel):
    id: str
    number: str
    external_reference: str
    customer_name: str
    vehicle_label: str
    technician_name: str | None
    quote_total: str | None
    version: int
    customer_id: str
    vehicle_id: str
    status: str
    title: str
    concern: str
    diagnosis: str | None
    technician_quote: dict[str, object] | None
    parts_required: list[dict[str, object]] | None
    assigned_technicians: list[str]
    bay_code: str | None
    promised_at: datetime | None
    invoice_reference: str | None
    erpnext_service_order_id: str | None
    erpnext_invoice_id: str | None
    erp_sync_status: str
    erp_sync_error: str | None
    erp_last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
    events: list[WorkOrderEventRead] = []


class WorkOrderBoardColumn(BaseModel):
    status: str
    label: str
    work_orders: list[WorkOrderRead]


class WorkshopSettingsUpdate(BaseModel):
    default_view: str = Field(pattern="^(KANBAN|BAYS)$")
    bays_enabled: bool
    bay_codes: list[str] = Field(default_factory=list, max_length=50)


class WorkshopSettingsRead(WorkshopSettingsUpdate):
    pass


class BrandingProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    legal_name: str = Field(min_length=2, max_length=180)
    tax_id: str = Field(default="", max_length=80)
    address: str = Field(default="", max_length=300)
    phone: str = Field(default="", max_length=40)
    email: EmailStr | None = None
    website: str = Field(default="", max_length=300)
    primary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    surface_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    document_footer: str = Field(default="", max_length=500)
    seasonal_theme_enabled: bool = False
    seasonal_theme_code: Literal["NONE", "JANUARY_NEW_YEAR", "FEBRUARY_FRIENDSHIP", "MARCH_MAINTENANCE", "APRIL_ROAD_SAFETY", "MAY_FAMILY", "JUNE_ENVIRONMENT", "JULY_TRAVEL", "AUGUST_WORKSHOP", "PATRIA_SEPTEMBER", "OCTOBER_PREVENTION", "NOVEMBER_SAVINGS", "DECEMBER_HOLIDAYS"] = "NONE"
    seasonal_theme_title: str = Field(default="", max_length=100)
    seasonal_theme_message: str = Field(default="", max_length=240)


class BrandingProfileRead(BrandingProfileUpdate):
    organization_id: str
    logo_url: str
    logo_dark_url: str
    favicon_url: str
    asset_history: list[dict[str, object]] = Field(default_factory=list)
    updated_at: str | None = None


class QuoteLineCreate(BaseModel):
    line_type: Literal["LABOR", "PART", "OTHER"]
    code: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=2, max_length=300)
    quantity: Decimal = Field(gt=0, le=1000)
    unit_price: Decimal = Field(ge=0, le=10000000)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0, le=10000000)
    approval_status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    source_reference: str | None = Field(default=None, max_length=180)


class QuoteCreate(BaseModel):
    work_order_id: str | None = None
    customer_id: str | None = None
    vehicle_id: str | None = None
    notes: str | None = Field(default=None, max_length=3000)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax: Decimal = Field(default=Decimal("0.00"), ge=0)
    created_by: str = Field(min_length=2, max_length=120)
    lines: list[QuoteLineCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_context(self) -> "QuoteCreate":
        if not self.work_order_id and not (self.customer_id and self.vehicle_id):
            raise ValueError("Indique una OT o el cliente y vehiculo de la precotizacion")
        return self


class QuoteLineRead(ORMModel):
    id: str
    line_type: str
    code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    approval_status: str
    source_reference: str | None
    line_total: Decimal


class QuoteRead(ORMModel):
    id: str
    number: str
    work_order_id: str | None
    customer_id: str | None
    vehicle_id: str | None
    converted_work_order_id: str | None
    status: str
    notes: str | None
    discount: Decimal
    tax: Decimal
    subtotal: Decimal
    total: Decimal
    created_by: str
    approved_by: str | None
    approved_at: datetime | None
    erpnext_quotation_id: str | None
    erp_sync_status: str
    erp_sync_error: str | None
    erp_last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lines: list[QuoteLineRead]


class QuoteStatusUpdate(BaseModel):
    status: Literal["SENT", "APPROVED", "REJECTED"]
    actor: str = Field(min_length=2, max_length=120)


class QuoteLineStatusUpdate(BaseModel):
    approval_status: Literal["PENDING", "APPROVED", "REJECTED"]
    actor: str = Field(min_length=2, max_length=120)


class QuoteFromWorkOrderCreate(BaseModel):
    actor: str = Field(min_length=2, max_length=120)


class QuoteConvertCreate(BaseModel):
    actor: str = Field(min_length=2, max_length=120)
    title: str = Field(default="Servicio aprobado desde cotizacion", min_length=3, max_length=220)
    concern: str = Field(default="Cotizacion aceptada por el cliente.", min_length=5, max_length=5000)


class CashSessionOpen(BaseModel):
    opening_balance: Decimal = Field(ge=0, le=10000000)
    actor: str = Field(min_length=2, max_length=120)
    access_code: str | None = Field(default=None, min_length=4, max_length=64)


class CashSessionClose(BaseModel):
    counted_cash: Decimal = Field(ge=0, le=10000000)
    actor: str = Field(min_length=2, max_length=120)
    access_code: str | None = Field(default=None, min_length=4, max_length=64)


class CashSessionRead(ORMModel):
    id: str
    opened_by: str
    closed_by: str | None
    status: str
    opening_balance: Decimal
    counted_cash: Decimal | None
    expected_cash: Decimal | None
    difference: Decimal | None
    opened_at: datetime
    closed_at: datetime | None


class PaymentCreate(BaseModel):
    work_order_id: str
    quote_id: str | None = None
    method: Literal["CASH", "CARD", "TRANSFER"]
    amount: Decimal = Field(gt=0, le=10000000)
    reference: str | None = Field(default=None, max_length=180)
    actor: str = Field(min_length=2, max_length=120)
    access_code: str | None = Field(default=None, min_length=4, max_length=64)


class PaymentRead(ORMModel):
    id: str
    receipt_number: str
    cash_session_id: str
    work_order_id: str | None
    quote_id: str | None
    retail_sale_id: str | None
    method: str
    amount: Decimal
    reference: str | None
    status: str
    received_by: str
    created_at: datetime


class CashSummary(BaseModel):
    session: CashSessionRead | None
    payments: list[PaymentRead]
    totals_by_method: dict[str, Decimal]
    total_collected: Decimal


class CounterSaleItemCreate(BaseModel):
    product_id: str
    quantity: Decimal = Field(gt=0, le=10000)
    unit_price: Decimal = Field(gt=0, le=10000000)


class CounterItemRequestCreate(BaseModel):
    search_query: str = Field(min_length=2, max_length=240)
    customer_name: str = Field(min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=40)
    vehicle_vin: str | None = Field(default=None, max_length=40)
    quantity: Decimal = Field(default=Decimal("1"), gt=0, le=10000)
    branch_id: str
    warehouse_id: str | None = None
    product_id: str | None = None
    notes: str | None = Field(default=None, max_length=1000)


class CounterItemRequestRead(ORMModel):
    id: str
    organization_id: str
    number: str
    branch_id: str
    warehouse_id: str | None
    product_id: str | None
    search_query: str
    customer_name: str
    phone: str | None
    vehicle_vin: str | None
    quantity: Decimal
    notes: str | None
    status: str
    requested_by: str
    created_at: datetime
    updated_at: datetime


class CounterSaleCreate(BaseModel):
    cash_session_id: str
    branch_id: str
    warehouse_id: str
    customer_id: str | None = None
    customer_name: str = Field(min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=40)
    tax_id: str | None = Field(default=None, max_length=80)
    vehicle_vin: str | None = Field(default=None, max_length=40)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0, le=10000000)
    tax: Decimal = Field(default=Decimal("0.00"), ge=0, le=10000000)
    method: Literal["CASH", "CARD", "TRANSFER"]
    reference: str | None = Field(default=None, max_length=180)
    actor: str = Field(min_length=2, max_length=120)
    access_code: str | None = Field(default=None, min_length=4, max_length=64)
    items: list[CounterSaleItemCreate] = Field(min_length=1, max_length=100)


class CounterSaleItemRead(ORMModel):
    id: str
    product_id: str
    sku: str
    name: str
    quantity: Decimal
    returned_quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    line_total: Decimal


class CounterSaleRead(ORMModel):
    id: str
    organization_id: str
    branch_id: str
    warehouse_id: str
    cash_session_id: str
    sale_number: str
    invoice_number: str
    customer_id: str | None
    customer_name: str
    phone: str | None
    tax_id: str | None
    vehicle_vin: str | None
    status: str
    currency: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    payment_method: str
    payment_reference: str | None
    erpnext_invoice_id: str | None
    erpnext_payment_id: str | None
    sync_status: str
    sync_error: str | None
    sync_attempts: int
    last_sync_at: datetime | None
    created_by: str
    completed_at: datetime
    created_at: datetime
    updated_at: datetime
    items: list[CounterSaleItemRead]
    payment: PaymentRead | None = None


class CounterReturnItemCreate(BaseModel):
    sale_item_id: str
    quantity: Decimal = Field(gt=0, le=10000)


class CounterReturnCreate(BaseModel):
    approval_id: str
    reason: str = Field(min_length=5, max_length=500)
    method: Literal["CASH", "CARD", "TRANSFER"]
    reference: str | None = Field(default=None, max_length=180)
    actor: str = Field(min_length=2, max_length=120)
    access_code: str | None = Field(default=None, min_length=4, max_length=64)
    items: list[CounterReturnItemCreate] = Field(min_length=1, max_length=100)


class ApprovalItemCreate(BaseModel):
    sale_item_id: str
    quantity: Decimal = Field(gt=0, le=10000)


class ApprovalRequestCreate(BaseModel):
    request_type: Literal["RETURN", "WARRANTY"]
    reason: str = Field(min_length=5, max_length=500)
    method: Literal["CASH", "CARD", "TRANSFER"]
    reference: str | None = Field(default=None, max_length=180)
    requested_by: str = Field(min_length=2, max_length=120)
    owner_email: EmailStr
    items: list[ApprovalItemCreate] = Field(min_length=1, max_length=100)


class ApprovalRequestRead(ORMModel):
    id: str
    sale_id: str
    request_type: str
    status: str
    requested_by: str
    owner_email: str
    reason: str
    payload_json: dict[str, object]
    expires_at: datetime
    delivery_status: str
    delivery_error: str | None
    decided_by: str | None
    decision_comment: str | None
    decided_at: datetime | None
    consumed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    token: str | None = None
    approval_url: str | None = None


class ApprovalDecision(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    comment: str | None = Field(default=None, max_length=500)


class CounterReturnItemRead(ORMModel):
    id: str
    sale_item_id: str
    quantity: Decimal
    unit_refund: Decimal
    line_total: Decimal


class CounterReturnRead(ORMModel):
    id: str
    sale_id: str
    return_number: str
    status: str
    reason: str
    method: str
    reference: str | None
    subtotal: Decimal
    total: Decimal
    actor: str
    erpnext_credit_note_id: str | None
    erpnext_payment_id: str | None
    sync_status: str
    sync_error: str | None
    sync_attempts: int
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[CounterReturnItemRead]
    sale_status: str


class HeartbeatRequest(BaseModel):
    node_id: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=80)
    status: str = Field(default="HEALTHY", max_length=30)
    version: str = Field(min_length=1, max_length=50)
    metadata: dict[str, object] = Field(default_factory=dict)


class HeartbeatRead(ORMModel):
    node_id: str
    role: str
    status: str
    version: str
    metadata_json: dict[str, object]
    last_seen_at: datetime


class LeaseAcquireRequest(BaseModel):
    node_id: str = Field(min_length=2, max_length=120)
    ttl_seconds: int = Field(default=30, ge=5, le=300)


class LeaseRead(ORMModel):
    lease_name: str
    holder_node_id: str
    expires_at: datetime
    fencing_token: int


class FlowEventCreate(BaseModel):
    module: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z_]+$")
    action: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z_]+$")
    item_reference: str = Field(min_length=1, max_length=120)
    actor: str = Field(min_length=2, max_length=120)
    result: str = Field(default="SUCCESS", pattern=r"^(SUCCESS|FAILED|CANCELLED)$")
    metadata: dict[str, object] = Field(default_factory=dict)


class FlowEventRead(ORMModel):
    id: str
    module: str
    action: str
    item_reference: str
    actor: str
    result: str
    metadata_json: dict[str, object]
    created_at: datetime


class FlowHeatmapCell(BaseModel):
    module: str
    action: str
    count: int
    last_seen_at: datetime


class ChatSessionCreate(BaseModel):
    website: str | None = Field(default=None, max_length=0, exclude=True)
    locale: str = Field(default="es-HN", min_length=2, max_length=20)
    page_url: str | None = Field(default=None, max_length=1000)
    referrer: str | None = Field(default=None, max_length=1000)
    accepted_privacy: Literal[True]


class ChatSessionCreated(BaseModel):
    session_id: str
    session_token: str
    expires_at: datetime
    welcome_message: str
    quick_prompts: list[str] = Field(default_factory=list)
    privacy_notice: str


class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    client_message_id: str = Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 2:
            raise ValueError("Message is too short")
        return stripped


class ChatMessageRead(ORMModel):
    id: str
    role: Literal["assistant", "user", "system"]
    content: str
    created_at: datetime
    audit_id: str | None = None
    mode: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)


class ChatReplyRead(BaseModel):
    session_id: str
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    audit_id: str | None
    mode: str
    suggested_actions: list[str] = Field(default_factory=list)


class ChatHistoryRead(BaseModel):
    session_id: str
    messages: list[ChatMessageRead]


class ChatSessionClosed(BaseModel):
    session_id: str
    status: Literal["CLOSED"]
    closed_at: datetime


class BranchCreate(BaseModel):
    code: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=160)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=40)
    email_domain: str | None = Field(default=None, max_length=180)
    timezone: str = Field(default="America/Tegucigalpa", max_length=80)


class BranchRead(ORMModel):
    id: str
    code: str
    name: str
    address: str | None
    phone: str | None
    email_domain: str | None
    timezone: str
    active: bool


class WarehouseCreate(BaseModel):
    branch_id: str
    code: str = Field(min_length=2, max_length=40, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=160)
    warehouse_type: Literal["STOCK", "PROCESS", "TRANSIT", "RETURNS"]


class WarehouseRead(ORMModel):
    id: str
    branch_id: str
    code: str
    name: str
    warehouse_type: str
    active: bool


class ReservationCreate(BaseModel):
    product_id: str
    warehouse_id: str
    store_order_id: str | None = None
    work_order_id: str | None = None
    quantity: Decimal = Field(gt=0, le=100000)
    expires_at: datetime | None = None
    actor: str = Field(min_length=2, max_length=120)

    @model_validator(mode="after")
    def validate_owner(self) -> ReservationCreate:
        if bool(self.store_order_id) == bool(self.work_order_id):
            raise ValueError("Exactly one store_order_id or work_order_id is required")
        return self


class ReservationRead(ORMModel):
    id: str
    reference: str
    product_id: str
    warehouse_id: str
    store_order_id: str | None
    work_order_id: str | None
    quantity: Decimal
    status: str
    expires_at: datetime | None
    actor: str
    created_at: datetime


class TransferCreate(BaseModel):
    from_warehouse_id: str
    to_warehouse_id: str
    items_json: list[dict[str, object]] = Field(min_length=1, max_length=100)
    carrier: str | None = Field(default=None, max_length=160)
    tracking_number: str | None = Field(default=None, max_length=180)
    guide_image_url: str | None = Field(default=None, max_length=1000)
    actor: str = Field(min_length=2, max_length=120)


class TransferRead(ORMModel):
    id: str
    number: str
    from_warehouse_id: str
    to_warehouse_id: str
    status: str
    items_json: list[dict[str, object]]
    carrier: str | None
    tracking_number: str | None
    guide_image_url: str | None
    actor: str
    erpnext_stock_entry_id: str | None
    erp_sync_status: str
    erp_sync_error: str | None
    erp_last_synced_at: datetime | None
    created_at: datetime


class ShipmentCreate(BaseModel):
    store_order_id: str
    from_warehouse_id: str
    carrier: str = Field(min_length=2, max_length=160)
    tracking_number: str | None = Field(default=None, max_length=180)
    guide_image_url: str | None = Field(default=None, max_length=1000)
    recipient_name: str = Field(min_length=2, max_length=180)
    recipient_phone: str = Field(min_length=7, max_length=40)
    delivery_notes: str | None = Field(default=None, max_length=2000)
    actor: str = Field(min_length=2, max_length=120)


class ShipmentRead(ORMModel):
    id: str
    number: str
    store_order_id: str
    from_warehouse_id: str
    status: str
    carrier: str
    tracking_number: str | None
    guide_image_url: str | None
    recipient_name: str
    recipient_phone: str
    delivery_notes: str | None
    actor: str
    created_at: datetime


class StatusActorUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=40)
    actor: str = Field(min_length=2, max_length=120)
    resolution: str | None = Field(default=None, max_length=3000)
    tracking_number: str | None = Field(default=None, max_length=180)
    guide_image_url: str | None = Field(default=None, max_length=1000)


class QualityCaseCreate(BaseModel):
    case_type: Literal["RETURN", "WARRANTY", "COMPLAINT", "REWORK"]
    customer_id: str | None = None
    vehicle_id: str | None = None
    work_order_id: str | None = None
    store_order_id: str | None = None
    description: str = Field(min_length=5, max_length=5000)
    evidence_url: str | None = Field(default=None, max_length=1000)
    actor: str = Field(min_length=2, max_length=120)


class QualityCaseRead(ORMModel):
    id: str
    number: str
    case_type: str
    customer_id: str | None
    vehicle_id: str | None
    work_order_id: str | None
    store_order_id: str | None
    status: str
    description: str
    resolution: str | None
    evidence_url: str | None
    actor: str
    created_at: datetime
    updated_at: datetime


class VehicleHistoryCreate(BaseModel):
    vin: str = Field(min_length=5, max_length=40)
    event_type: Literal["DIAGNOSIS", "SERVICE", "PART_SALE", "QUALITY", "RETURN", "INSPECTION"]
    reference: str = Field(min_length=2, max_length=120)
    summary: str = Field(min_length=5, max_length=500)
    mileage_km: int | None = Field(default=None, ge=0, le=5000000)
    quality_result: str | None = Field(default=None, max_length=60)
    actor: str = Field(min_length=2, max_length=120)
    metadata_json: dict[str, object] = Field(default_factory=dict)


class VehicleHistoryRead(ORMModel):
    id: str
    vehicle_id: str | None
    vin: str
    event_type: str
    reference: str
    summary: str
    mileage_km: int | None
    quality_result: str | None
    actor: str
    metadata_json: dict[str, object]
    created_at: datetime


class LeadCreate(BaseModel):
    website: str | None = Field(default=None, max_length=0, exclude=True)
    full_name: str = Field(min_length=2, max_length=180)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr | None = None
    interest: str = Field(min_length=3, max_length=500)
    vehicle_summary: str | None = Field(default=None, max_length=240)
    source: Literal["AI_CHAT", "LANDING", "WHATSAPP", "PHONE", "WALK_IN"] = "AI_CHAT"
    chat_session_id: str | None = None


class LeadRead(ORMModel):
    id: str
    number: str
    source: str
    full_name: str
    phone: str
    email: str | None
    interest: str
    vehicle_summary: str | None
    status: str
    assigned_to: str | None
    chat_session_id: str | None
    next_action_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    status: Literal["NEW", "QUALIFYING", "ADVISOR", "QUOTED", "WON", "LOST"]
    assigned_to: str | None = Field(default=None, max_length=120)
    next_action_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=3000)
    actor: str = Field(min_length=2, max_length=120)


class LeadActivityCreate(BaseModel):
    activity_type: Literal["CALL", "WHATSAPP", "EMAIL", "NOTE", "FOLLOW_UP"]
    content: str = Field(min_length=3, max_length=3000)
    outcome: str | None = Field(default=None, max_length=500)
    actor: str = Field(min_length=2, max_length=120)


class LeadSurveyCreate(BaseModel):
    survey_name: str = Field(min_length=3, max_length=180)
    answers: dict[str, object] = Field(default_factory=dict)
    actor: str = Field(min_length=2, max_length=120)


class ManagementDocumentCreate(BaseModel):
    branch_id: str
    document_type: Literal[
        "CAI", "FISCAL_CONFIGURATION", "INVOICE_TEMPLATE", "QUOTE_TEMPLATE", "PROFORMA", "LETTER", "EMAIL_TEMPLATE"
    ]
    number: str = Field(min_length=2, max_length=180)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    file_url: str | None = Field(default=None, max_length=1000)
    status: Literal["DRAFT", "ACTIVE", "EXPIRED"] = "DRAFT"
    metadata_json: dict[str, object] = Field(default_factory=dict)


class ManagementDocumentStatusUpdate(BaseModel):
    status: Literal["DRAFT", "ACTIVE", "EXPIRED"]
    accountant_confirmed: bool = False
    note: str | None = Field(default=None, max_length=500)


class ManagementDocumentRead(ORMModel):
    id: str
    branch_id: str
    document_type: str
    number: str
    valid_from: datetime | None
    valid_until: datetime | None
    file_url: str | None
    status: str
    metadata_json: dict[str, object]
    created_at: datetime


DocumentType = Literal[
    "QUOTE", "INVOICE", "DIAGNOSIS", "WORK_ORDER", "WARRANTY", "EXIT_PASS",
    "PICKING_TICKET", "WAREHOUSE_DELIVERY", "WAREHOUSE_RETURN", "WAREHOUSE_RECEIPT",
    "PAYSLIP",
]


class PrintProfile(BaseModel):
    printer_type: Literal["LASER_INKJET", "THERMAL", "PREPRINTED", "BROWSER_PDF"] = "BROWSER_PDF"
    orientation: Literal["PORTRAIT", "LANDSCAPE"] = "PORTRAIT"
    margins_mm: dict[Literal["top", "right", "bottom", "left"], float] = Field(default_factory=lambda: {"top": 10, "right": 10, "bottom": 10, "left": 10})
    copies: int = Field(default=1, ge=1, le=5)
    show_logo: bool = True
    preprinted_background: bool = False


class DocumentTemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=3, max_length=180)
    document_type: DocumentType
    branch_id: str | None = None
    paper_size: Literal["LETTER", "A4", "THERMAL_80", "THERMAL_58"] = "LETTER"
    print_profile: PrintProfile = Field(default_factory=PrintProfile)
    html_template: str = Field(min_length=20, max_length=100000)
    css_text: str = Field(default="", max_length=30000)
    change_note: str | None = Field(default=None, max_length=500)
    created_by: str = Field(min_length=2, max_length=120)


class DocumentTemplateVersionCreate(BaseModel):
    paper_size: Literal["LETTER", "A4", "THERMAL_80", "THERMAL_58"]
    print_profile: PrintProfile = Field(default_factory=PrintProfile)
    html_template: str = Field(min_length=20, max_length=100000)
    css_text: str = Field(default="", max_length=30000)
    change_note: str = Field(min_length=3, max_length=500)
    created_by: str = Field(min_length=2, max_length=120)


class DocumentTemplateVersionRead(ORMModel):
    id: str
    template_id: str
    version: int
    status: str
    paper_size: str
    print_profile_json: dict[str, object]
    html_template: str
    css_text: str
    variables_json: list[str]
    change_note: str | None
    created_by: str
    created_at: datetime
    published_at: datetime | None


class DocumentTemplateRead(ORMModel):
    id: str
    organization_id: str
    branch_id: str | None
    code: str
    name: str
    document_type: str
    status: str
    current_version: int
    published_version: int | None
    active: bool
    created_at: datetime
    updated_at: datetime
    versions: list[DocumentTemplateVersionRead] = Field(default_factory=list)


class DocumentTemplatePublish(BaseModel):
    version: int = Field(ge=1)
    actor: str = Field(min_length=2, max_length=120)


class DocumentTemplatePreview(BaseModel):
    html_template: str = Field(min_length=20, max_length=100000)
    css_text: str = Field(default="", max_length=30000)
    paper_size: Literal["LETTER", "A4", "THERMAL_80", "THERMAL_58"] = "LETTER"
    print_profile: PrintProfile = Field(default_factory=PrintProfile)


class DocumentRenderRead(ORMModel):
    id: str
    template_id: str | None
    template_version_id: str | None
    document_type: str
    business_reference: str
    content_sha256: str
    created_by: str
    created_at: datetime


class OperationsOverview(BaseModel):
    branches: list[BranchRead]
    warehouses: list[WarehouseRead]
    reservations: list[ReservationRead]
    transfers: list[TransferRead]
    shipments: list[ShipmentRead]
    quality_cases: list[QualityCaseRead]
    leads: list[LeadRead]
    management_documents: list[ManagementDocumentRead]


class SupplierCreate(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9._-]+$")
    name: str = Field(min_length=3, max_length=180)
    tax_id: str | None = Field(default=None, max_length=80)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    payment_terms_days: int = Field(default=0, ge=0, le=365)
    currency: str = Field(default="HNL", min_length=3, max_length=3)


class SupplierRead(ORMModel):
    id: str
    code: str
    name: str
    tax_id: str | None
    email: str | None
    phone: str | None
    payment_terms_days: int
    currency: str
    active: bool
    erpnext_supplier_id: str | None
    erp_sync_status: str
    erp_sync_error: str | None
    created_at: datetime


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=180)
    tax_id: str | None = Field(default=None, max_length=80)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    payment_terms_days: int | None = Field(default=None, ge=0, le=365)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    active: bool | None = None


class PurchaseItem(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=2, max_length=300)
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    branch_id: str | None = None
    currency: str = Field(default="HNL", min_length=3, max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    expected_at: datetime | None = None
    tax: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = Field(default=None, max_length=3000)
    items: list[PurchaseItem] = Field(min_length=1, max_length=500)


class PurchaseOrderRead(ORMModel):
    id: str
    number: str
    branch_id: str | None
    supplier_id: str
    status: str
    currency: str
    exchange_rate: Decimal
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    expected_at: datetime | None
    notes: str | None
    items_json: list[dict[str, object]]
    created_by: str
    erpnext_purchase_order_id: str | None
    erp_sync_status: str
    erp_sync_error: str | None
    created_at: datetime


class PurchaseReceiptItem(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    quantity: Decimal = Field(gt=0)


class PurchaseReceiptCreate(BaseModel):
    items: list[PurchaseReceiptItem] = Field(min_length=1, max_length=500)
    reference: str = Field(min_length=2, max_length=180)
    note: str | None = Field(default=None, max_length=1000)


class EnterpriseStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z_]+$")


class ImportCost(BaseModel):
    kind: Literal["FREIGHT", "INSURANCE", "CUSTOMS", "TAX", "HANDLING", "OTHER"]
    description: str = Field(min_length=2, max_length=300)
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class ImportCaseCreate(BaseModel):
    purchase_order_id: str
    incoterm: str = Field(min_length=2, max_length=10)
    origin_country: str = Field(min_length=2, max_length=80)
    destination_port: str = Field(min_length=2, max_length=120)
    eta: datetime | None = None
    allocation_method: Literal["BY_VALUE", "BY_QUANTITY", "BY_WEIGHT"] = "BY_VALUE"
    costs: list[ImportCost] = Field(default_factory=list, max_length=100)
    documents: list[dict[str, object]] = Field(default_factory=list, max_length=100)


class ImportCaseRead(ORMModel):
    id: str
    number: str
    purchase_order_id: str
    status: str
    incoterm: str
    origin_country: str
    destination_port: str
    eta: datetime | None
    costs_json: list[dict[str, object]]
    documents_json: list[dict[str, object]]
    additional_cost_total: Decimal
    allocation_method: str
    landed_cost_status: str
    erpnext_landed_cost_id: str | None
    created_at: datetime


class ImportCaseUpdate(BaseModel):
    eta: datetime | None = None
    allocation_method: Literal["BY_VALUE", "BY_QUANTITY", "BY_WEIGHT"] | None = None
    costs: list[ImportCost] | None = Field(default=None, max_length=100)
    documents: list[dict[str, object]] | None = Field(default=None, max_length=100)


class EmployeeContractCreate(BaseModel):
    staff_user_id: UUID | None = None
    branch_id: str | None = None
    employee_code: str | None = Field(default=None, min_length=2, max_length=60)
    employee_name: str = Field(min_length=3, max_length=180)
    date_of_birth: date
    national_id: str | None = Field(default=None, min_length=5, max_length=80)
    address: str | None = Field(default=None, min_length=5, max_length=500)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    social_security_number: str | None = Field(default=None, max_length=80)
    insurance_provider: str | None = Field(default=None, max_length=120)
    insurance_member_number: str | None = Field(default=None, max_length=120)
    job_title: str = Field(min_length=2, max_length=120)
    contract_type: Literal["PERMANENT", "TEMPORARY", "HOURLY", "CONTRACTOR"]
    start_date: date
    end_date: date | None = None
    monthly_salary: Decimal = Field(gt=0)
    payment_type: Literal["MONTHLY", "BIWEEKLY", "WEEKLY", "DAILY", "HOURLY"] = "MONTHLY"
    base_pay_amount: Decimal | None = Field(default=None, gt=0)
    standard_hours_weekly: Decimal = Field(gt=0, le=80)
    currency: str = Field(default="HNL", min_length=3, max_length=3)
    benefits: list[dict[str, object]] = Field(default_factory=list)
    schedule: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_of_birth >= self.start_date:
            raise ValueError("La fecha de nacimiento debe ser anterior al inicio laboral")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("La fecha final no puede ser anterior al inicio")
        return self


class EmployeeContractRead(ORMModel):
    id: str
    branch_id: str | None
    staff_user_id: UUID | None
    employee_code: str
    employee_name: str
    date_of_birth: date | None
    national_id: str | None
    address: str | None
    phone: str | None
    email: str | None
    social_security_number: str | None
    insurance_provider: str | None
    insurance_member_number: str | None
    job_title: str
    contract_type: str
    status: str
    start_date: date
    end_date: date | None
    monthly_salary: Decimal
    payment_type: str
    base_pay_amount: Decimal
    standard_hours_weekly: Decimal
    currency: str
    benefits_json: list[dict[str, object]]
    schedule_json: dict[str, object]
    erpnext_employee_id: str | None
    erp_sync_status: str
    created_at: datetime


class EmployeeContractUpdate(BaseModel):
    branch_id: str | None = None
    employee_name: str | None = Field(default=None, min_length=3, max_length=180)
    national_id: str | None = Field(default=None, min_length=5, max_length=80)
    address: str | None = Field(default=None, min_length=5, max_length=500)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    social_security_number: str | None = Field(default=None, max_length=80)
    insurance_provider: str | None = Field(default=None, max_length=120)
    insurance_member_number: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, min_length=2, max_length=120)
    end_date: date | None = None
    monthly_salary: Decimal | None = Field(default=None, gt=0)
    payment_type: Literal["MONTHLY", "BIWEEKLY", "WEEKLY", "DAILY", "HOURLY"] | None = None
    base_pay_amount: Decimal | None = Field(default=None, gt=0)
    standard_hours_weekly: Decimal | None = Field(default=None, gt=0, le=80)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    benefits: list[dict[str, object]] | None = None
    schedule: dict[str, object] | None = None


class AttendanceCreate(BaseModel):
    contract_id: str
    work_date: date
    regular_hours: Decimal = Field(ge=0, le=24)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0, le=16)
    status: Literal["PRESENT", "ABSENT", "LEAVE", "HOLIDAY"] = "PRESENT"
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)


class AttendanceRead(ORMModel):
    id: str
    contract_id: str
    work_date: date
    regular_hours: Decimal
    overtime_hours: Decimal
    overtime_status: str
    overtime_approved_by: str | None
    overtime_approval_note: str | None
    status: str
    check_in_at: datetime | None
    check_out_at: datetime | None
    note: str | None
    recorded_by: str


class OvertimeDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    note: str = Field(min_length=3, max_length=500)


class LeaveRequestCreate(BaseModel):
    contract_id: str
    leave_type: Literal["VACATION", "SICK", "PERSONAL", "MATERNITY", "PATERNITY", "UNPAID"]
    start_date: date
    end_date: date
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("La fecha final no puede ser anterior al inicio")
        return self


class LeaveRequestRead(ORMModel):
    id: str
    contract_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None
    status: str
    requested_by: str
    approved_by: str | None


class PayrollAdjustment(BaseModel):
    contract_id: str
    kind: Literal["COMMISSION", "BONUS", "ALLOWANCE", "DEDUCTION"]
    description: str = Field(min_length=2, max_length=300)
    amount: Decimal = Field(ge=0)


class PayrollRunCreate(BaseModel):
    period_start: date
    period_end: date
    contract_ids: list[str] = Field(min_length=1, max_length=1000)
    adjustments: list[PayrollAdjustment] = Field(default_factory=list, max_length=5000)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("El periodo de nomina es invalido")
        return self


class PayrollRunRead(ORMModel):
    id: str
    number: str
    period_start: date
    period_end: date
    status: str
    lines_json: list[dict[str, object]]
    gross_total: Decimal
    deduction_total: Decimal
    net_total: Decimal
    created_by: str
    reviewed_by: str | None
    approved_by: str | None
    posted_by: str | None
    erpnext_payroll_entry_id: str | None
    erp_sync_status: str
    created_at: datetime


class PayrollRule(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[A-Z0-9_-]+$")
    label: str = Field(min_length=2, max_length=180)
    side: Literal["EMPLOYEE_DEDUCTION", "EMPLOYER_CONTRIBUTION"]
    calculation: Literal["PERCENT", "FIXED"]
    rate: Decimal = Field(ge=0, le=10000000)
    ceiling: Decimal | None = Field(default=None, ge=0)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_rate(self):
        if self.calculation == "PERCENT" and self.rate > 100:
            raise ValueError("Un porcentaje no puede exceder 100")
        return self


class PayrollPolicyCreate(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=3, max_length=180)
    effective_from: date
    effective_until: date | None = None
    rules: list[PayrollRule] = Field(default_factory=list, max_length=100)
    source_reference: str = Field(min_length=5, max_length=500)
    active: bool = True

    @model_validator(mode="after")
    def validate_effective_dates(self):
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValueError("La fecha final de la política es inválida")
        return self


class PayrollPolicyRead(ORMModel):
    id: str
    code: str
    name: str
    effective_from: date
    effective_until: date | None
    rules_json: list[dict[str, object]]
    source_reference: str
    approved_by: str
    active: bool
    created_at: datetime


class PayrollVoucherRead(ORMModel):
    id: str
    number: str
    payroll_run_id: str
    contract_id: str
    period_start: date
    period_end: date
    gross: Decimal
    deductions: Decimal
    employer_contributions: Decimal
    net: Decimal
    details_json: dict[str, object]
    status: str
    issued_at: datetime | None


class PrestationsPreviewCreate(BaseModel):
    contract_id: str
    termination_date: date
    average_ordinary_monthly: Decimal = Field(gt=0)
    include_notice: bool = True
    include_severance: bool = True


class PrestationsPreviewRead(BaseModel):
    employee_code: str
    service_days: int
    daily_average: Decimal
    notice_days: Decimal
    severance_days: Decimal
    vacation_days: Decimal
    notice_amount: Decimal
    severance_amount: Decimal
    vacation_amount: Decimal
    thirteenth_accrual: Decimal
    fourteenth_accrual: Decimal
    estimated_total: Decimal
    legal_notice: str


class UsedVehicleCreate(BaseModel):
    branch_id: str | None = None
    vin: str = Field(min_length=11, max_length=32)
    make: str = Field(min_length=2, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    model_year: int = Field(ge=1900, le=2100)
    mileage_km: int | None = Field(default=None, ge=0)
    acquisition_type: Literal["PURCHASE", "CONSIGNMENT", "TRADE_IN"]
    acquisition_cost: Decimal = Field(ge=0)
    reconditioning_cost: Decimal = Field(default=Decimal("0"), ge=0)
    target_sale_price: Decimal = Field(gt=0)
    owner_name: str | None = Field(default=None, max_length=180)
    inspection: dict[str, object] = Field(default_factory=dict)
    media: list[dict[str, object]] = Field(default_factory=list)


class UsedVehicleRead(ORMModel):
    id: str
    branch_id: str | None
    vin: str
    make: str
    model: str
    model_year: int
    mileage_km: int | None
    acquisition_type: str
    acquisition_cost: Decimal
    reconditioning_cost: Decimal
    target_sale_price: Decimal
    status: str
    owner_name: str | None
    inspection_json: dict[str, object]
    media_json: list[dict[str, object]]
    published_at: datetime | None
    sold_at: datetime | None
    erpnext_item_id: str | None
    created_at: datetime


class SocialChannelCreate(BaseModel):
    channel_type: Literal["WHATSAPP", "FACEBOOK", "INSTAGRAM", "WEBCHAT", "EMAIL"]
    name: str = Field(min_length=2, max_length=120)
    external_account_id: str = Field(min_length=2, max_length=180)
    credential_reference: str = Field(min_length=6, max_length=300, pattern=r"^(secret|vault)://")


class SocialChannelRead(ORMModel):
    id: str
    channel_type: str
    name: str
    external_account_id: str
    credential_reference: str
    webhook_status: str
    active: bool
    created_at: datetime


class SocialConversationCreate(BaseModel):
    channel_id: str
    contact_name: str = Field(min_length=2, max_length=180)
    contact_handle: str = Field(min_length=3, max_length=180)
    consent_status: Literal["UNKNOWN", "OPTED_IN", "OPTED_OUT"] = "UNKNOWN"
    subject: str | None = Field(default=None, max_length=240)


class SocialConversationRead(ORMModel):
    id: str
    channel_id: str
    contact_name: str
    contact_handle: str
    subject: str | None
    status: str
    consent_status: str
    assigned_to: str | None
    lead_id: str | None
    last_message_at: datetime
    created_at: datetime


class SocialMessageCreate(BaseModel):
    direction: Literal["INBOUND", "OUTBOUND"]
    body: str = Field(min_length=1, max_length=8000)
    human_approved: bool = False


class SocialMessageRead(ORMModel):
    id: str
    conversation_id: str
    direction: str
    body: str
    status: str
    human_approved: bool
    provider_reference: str | None
    sent_by: str
    created_at: datetime


class EnterpriseOverview(BaseModel):
    counts: dict[str, int]
    suppliers: list[SupplierRead]
    purchase_orders: list[PurchaseOrderRead]
    import_cases: list[ImportCaseRead]
    contracts: list[EmployeeContractRead]
    attendance: list[AttendanceRead]
    leave_requests: list[LeaveRequestRead]
    payroll_runs: list[PayrollRunRead]
    used_vehicles: list[UsedVehicleRead]
    social_channels: list[SocialChannelRead]
    social_conversations: list[SocialConversationRead]
