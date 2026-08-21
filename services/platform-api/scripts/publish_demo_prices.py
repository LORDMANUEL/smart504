"""Publish the explicit demo selling prices into ERPNext and refresh the projection.

This is an opt-in migration utility for the SmartDiag504 demo catalog. It does
not infer prices and it never touches products outside the known seed SKUs.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.demo_data import DEMO_PARTS
from app.models import CatalogProduct
from app.services.frappe import FrappeWriteClient


def demo_rates() -> dict[str, Decimal]:
    rates = {
        "SD-OIL-FILTER-001": Decimal("285.00"),
        "SD-AIR-FILTER-001": Decimal("420.00"),
        "SD-BRAKE-DISC-001": Decimal("1850.00"),
        "SD-SPARK-PLUG-001": Decimal("320.00"),
    }
    rates.update(
        {str(item["code"]): Decimal(str(item["price"])) for item in DEMO_PARTS}
    )
    return rates


def main() -> None:
    settings = get_settings()
    client = FrappeWriteClient(settings)
    applied: list[str] = []
    with SessionLocal() as db:
        for sku, rate in demo_rates().items():
            product = db.scalar(select(CatalogProduct).where(CatalogProduct.sku == sku))
            if product is None:
                continue
            client.upsert_item_price(
                item_code=sku,
                price_list=settings.frappe_price_list,
                rate=rate,
                currency=product.currency,
            )
            product.price = rate
            applied.append(sku)
        db.commit()
    print({"prices_published_to_erp": len(applied)})


if __name__ == "__main__":
    main()
