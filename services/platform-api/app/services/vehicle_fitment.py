from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import CatalogProduct, Vehicle
from app.request_context import current_identity


def normalize_vin(value: str) -> str:
    return "".join(character for character in value.strip().upper() if character.isalnum())


def find_vehicle_by_vin(db: Session, vin: str) -> Vehicle | None:
    normalized = normalize_vin(vin)
    if len(normalized) < 11:
        return None
    return db.scalar(select(Vehicle).where(
        Vehicle.vin == normalized,
        Vehicle.organization_id == current_identity().organization_id,
    ))


def vehicle_label(vehicle: Vehicle) -> str:
    return f"{vehicle.make} {vehicle.model} {vehicle.model_year or ''}".strip()


def compatible_products(db: Session, vehicle: Vehicle) -> list[CatalogProduct]:
    """Return only products whose persisted fitment names the matched vehicle.

    The lookup intentionally never decodes or guesses an unknown VIN. The current
    catalog stores exact make/model/year fitment in compatibility_notes; future
    normalized fitment rows can replace this query without changing the API.
    """

    label = vehicle_label(vehicle)
    return list(
        db.scalars(
            select(CatalogProduct)
            .where(
                CatalogProduct.active.is_(True),
                CatalogProduct.organization_id == vehicle.organization_id,
                CatalogProduct.compatibility_notes.ilike(f"%{label}%"),
            )
            .options(selectinload(CatalogProduct.images))
            .order_by(CatalogProduct.name)
        ).unique()
    )


def primary_image_url(product: CatalogProduct) -> str | None:
    primary = next((image for image in product.images if image.is_primary), None)
    selected = primary or (product.images[0] if product.images else None)
    if selected and "imagen generica de referencia" in (selected.alt_text or "").lower():
        return None
    return selected.public_url if selected else None
