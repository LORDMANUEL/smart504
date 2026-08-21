from decimal import Decimal

from smartdiag_domain.money import calculate_line_margin


def test_margin_uses_quantized_currency_values() -> None:
    result = calculate_line_margin(quantity=2, unit_price="150.00", unit_cost="90.00", discount="10.00")
    assert result.revenue == Decimal("290.00")
    assert result.cost == Decimal("180.00")
    assert result.margin == Decimal("110.00")
    assert result.margin_percent == Decimal("37.93")
