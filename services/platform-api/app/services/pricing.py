from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException


MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PricingPolicy:
    purchase_cost: Decimal
    landed_cost_factor: Decimal = Decimal("1.00")
    target_markup_percent: Decimal = Decimal("30.00")
    minimum_markup_percent: Decimal = Decimal("0.00")

    @property
    def landed_cost(self) -> Decimal:
        return _money(self.purchase_cost * max(self.landed_cost_factor, Decimal("1.00")))

    @property
    def minimum_sale_price(self) -> Decimal:
        multiplier = Decimal("1") + max(self.minimum_markup_percent, Decimal("0")) / Decimal("100")
        return _money(self.landed_cost * multiplier)

    @property
    def suggested_sale_price(self) -> Decimal:
        multiplier = Decimal("1") + max(self.target_markup_percent, Decimal("0")) / Decimal("100")
        return _money(self.landed_cost * multiplier)


def product_pricing_policy(product) -> PricingPolicy:
    return PricingPolicy(
        purchase_cost=Decimal(str(product.purchase_cost or 0)),
        landed_cost_factor=Decimal(str(product.landed_cost_factor or 1)),
        target_markup_percent=Decimal(str(product.target_markup_percent or 0)),
        minimum_markup_percent=Decimal(str(product.minimum_markup_percent or 0)),
    )


def validate_transaction_floor(
    *, lines: list[tuple[Decimal, Decimal, Decimal]], discount: Decimal
) -> None:
    """Prevent both direct price overrides and global discounts from crossing the cost floor."""
    sale_subtotal = Decimal("0")
    minimum_subtotal = Decimal("0")
    for quantity, unit_price, minimum_unit_price in lines:
        if minimum_unit_price > 0 and unit_price < minimum_unit_price:
            raise HTTPException(
                status_code=422,
                detail=f"El precio minimo permitido es {minimum_unit_price:.2f}; revise costo, importacion y margen",
            )
        sale_subtotal += quantity * unit_price
        minimum_subtotal += quantity * minimum_unit_price
    if sale_subtotal - discount < minimum_subtotal:
        allowed = max(sale_subtotal - minimum_subtotal, Decimal("0"))
        raise HTTPException(
            status_code=422,
            detail=f"El descuento excede el margen disponible. Descuento maximo: {allowed:.2f}",
        )
