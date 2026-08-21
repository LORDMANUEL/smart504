from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.services.frappe import projected_catalog_price
from app.services.pricing import PricingPolicy, validate_transaction_floor


def test_landed_cost_and_suggested_price_use_configured_factor_and_markup() -> None:
    policy = PricingPolicy(
        purchase_cost=Decimal("100.00"),
        landed_cost_factor=Decimal("1.25"),
        target_markup_percent=Decimal("40.00"),
        minimum_markup_percent=Decimal("0.00"),
    )

    assert policy.landed_cost == Decimal("125.00")
    assert policy.minimum_sale_price == Decimal("125.00")
    assert policy.suggested_sale_price == Decimal("175.00")


def test_transaction_rejects_line_price_or_discount_below_real_cost() -> None:
    with pytest.raises(HTTPException, match="precio minimo"):
        validate_transaction_floor(
            lines=[(Decimal("1"), Decimal("124.99"), Decimal("125.00"))],
            discount=Decimal("0"),
        )

    with pytest.raises(HTTPException, match="descuento"):
        validate_transaction_floor(
            lines=[(Decimal("2"), Decimal("150.00"), Decimal("125.00"))],
            discount=Decimal("60.01"),
        )

    validate_transaction_floor(
        lines=[(Decimal("2"), Decimal("150.00"), Decimal("125.00"))],
        discount=Decimal("50.00"),
    )


def test_erp_sync_does_not_replace_valid_store_price_with_zero() -> None:
    assert projected_catalog_price(Decimal("0"), Decimal("285")) == Decimal("285")
    assert projected_catalog_price(Decimal("320"), Decimal("285")) == Decimal("320")
