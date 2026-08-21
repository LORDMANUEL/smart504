from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CURRENCY = Decimal("0.01")
PERCENT = Decimal("0.01")


def _decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class MarginResult:
    revenue: Decimal
    cost: Decimal
    margin: Decimal
    margin_percent: Decimal


def calculate_line_margin(
    *,
    quantity: Decimal | int | float | str,
    unit_price: Decimal | int | float | str,
    unit_cost: Decimal | int | float | str,
    discount: Decimal | int | float | str = "0",
) -> MarginResult:
    qty = _decimal(quantity)
    revenue = (qty * _decimal(unit_price) - _decimal(discount)).quantize(CURRENCY, ROUND_HALF_UP)
    cost = (qty * _decimal(unit_cost)).quantize(CURRENCY, ROUND_HALF_UP)
    margin = (revenue - cost).quantize(CURRENCY, ROUND_HALF_UP)
    margin_percent = (
        (margin / revenue * Decimal("100")).quantize(PERCENT, ROUND_HALF_UP)
        if revenue
        else Decimal("0.00")
    )
    return MarginResult(revenue=revenue, cost=cost, margin=margin, margin_percent=margin_percent)
