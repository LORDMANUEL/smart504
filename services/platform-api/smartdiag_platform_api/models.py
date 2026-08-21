from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CompatibilityStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    REQUIRES_VALIDATION = "REQUIRES_VALIDATION"


class Product(BaseModel):
    sku: str
    slug: str
    name: str
    description: str
    brand: str
    category: str = "Repuestos"
    price: float = Field(ge=0)
    currency: str = "HNL"
    stock_qty: float = Field(ge=0)
    online_available_qty: float = Field(ge=0)
    compatibility_status: CompatibilityStatus
    fitment: list[str] = Field(default_factory=list)
    image_url: str | None = None


class ProductPage(BaseModel):
    items: list[Product]
    total: int


class VehicleSummary(BaseModel):
    make: str
    model: str
    year: int = Field(ge=1900, le=2100)
    vin: str | None = None


class BookingRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=24)
    email: str | None = None
    service_code: str = Field(min_length=2, max_length=50)
    requested_date: date
    vehicle: VehicleSummary
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("service_code")
    @classmethod
    def normalize_service_code(cls, value: str) -> str:
        return value.strip().upper()


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    created_at: datetime
    idempotent_replay: bool


class IncomingEvent(BaseModel):
    event_type: str
    aggregate_id: str
    aggregate_type: str = "Unknown"
    payload: dict[str, Any] = Field(default_factory=dict)
    actor_id: str | None = None


class AcceptedEvent(BaseModel):
    accepted: bool
    event_id: str
    event_key: str
