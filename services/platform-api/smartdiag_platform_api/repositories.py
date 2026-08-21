from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime

from smartdiag_domain.events import DomainEvent

from .models import BookingRequest, BookingResponse, CompatibilityStatus, Product


class InMemoryRepository:
    """Deterministic demo repository.

    Production adapters replace this class with Frappe/PostgreSQL implementations
    while preserving these method signatures.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._bookings: dict[str, BookingResponse] = {}
        self._events: dict[str, DomainEvent] = {}
        self._products = [
            Product(
                sku="FL-910S",
                slug="filtro-aceite-motorcraft-fl-910s",
                name="Filtro de aceite Motorcraft FL-910S",
                description="Filtro original para mantenimiento preventivo de motores Ford seleccionados.",
                brand="Motorcraft",
                category="Filtros",
                price=315.00,
                stock_qty=14,
                online_available_qty=8,
                compatibility_status=CompatibilityStatus.REQUIRES_VALIDATION,
                fitment=["Ford Escape", "Ford Focus", "Ford Transit Connect"],
                image_url="/assets/products/filter-oil.svg",
            ),
            Product(
                sku="FP-70",
                slug="filtro-cabina-motorcraft-fp-70",
                name="Filtro de cabina Motorcraft FP-70",
                description="Filtro de partículas para sistema de aire acondicionado y ventilación.",
                brand="Motorcraft",
                category="Filtros",
                price=485.00,
                stock_qty=9,
                online_available_qty=5,
                compatibility_status=CompatibilityStatus.PROBABLE,
                fitment=["Ford Explorer", "Ford Edge"],
                image_url="/assets/products/filter-cabin.svg",
            ),
            Product(
                sku="MERCON-LV-1Q",
                slug="fluido-transmision-mercon-lv",
                name="Fluido de transmisión MERCON LV",
                description="Fluido de transmisión automática por cuarto; instalación según especificación técnica.",
                brand="Motorcraft",
                category="Transmisión",
                price=395.00,
                stock_qty=28,
                online_available_qty=18,
                compatibility_status=CompatibilityStatus.REQUIRES_VALIDATION,
                fitment=["Aplicaciones Ford con especificación MERCON LV"],
                image_url="/assets/products/transmission-fluid.svg",
            ),
            Product(
                sku="BRF-1548",
                slug="pastillas-freno-delanteras-brf-1548",
                name="Pastillas de freno delanteras BRF-1548",
                description="Juego de pastillas delanteras; confirmar por VIN antes de facturar.",
                brand="Motorcraft",
                category="Frenos",
                price=2190.00,
                stock_qty=4,
                online_available_qty=3,
                compatibility_status=CompatibilityStatus.REQUIRES_VALIDATION,
                fitment=["Ford Explorer 2016-2019"],
                image_url="/assets/products/brake-pads.svg",
            ),
        ]

    def list_products(
        self,
        *,
        query: str | None = None,
        make: str | None = None,
        model: str | None = None,
        year: int | None = None,
    ) -> list[Product]:
        del year  # The demo uses fitment text; the Frappe adapter performs structured filtering.
        products = self._products
        if query:
            needle = query.casefold().strip()
            products = [
                product
                for product in products
                if needle in f"{product.name} {product.description} {product.sku} {product.brand}".casefold()
            ]
        if make:
            make_needle = make.casefold().strip()
            products = [product for product in products if any(make_needle in item.casefold() for item in product.fitment)]
        if model:
            model_needle = model.casefold().strip()
            products = [product for product in products if any(model_needle in item.casefold() for item in product.fitment)]
        return products

    def create_booking(self, idempotency_key: str, request: BookingRequest) -> tuple[BookingResponse, bool]:
        del request  # Persisted by the production Frappe adapter.
        with self._lock:
            if existing := self._bookings.get(idempotency_key):
                return existing.model_copy(update={"idempotent_replay": True}), False
            response = BookingResponse(
                booking_id=f"SD-BKG-{uuid.uuid4().hex[:10].upper()}",
                status="REQUESTED",
                created_at=datetime.now(UTC),
                idempotent_replay=False,
            )
            self._bookings[idempotency_key] = response
            return response, True

    def accept_event(self, event: DomainEvent) -> DomainEvent:
        with self._lock:
            self._events.setdefault(event.event_key, event)
            return self._events[event.event_key]
