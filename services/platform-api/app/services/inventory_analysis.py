from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CatalogProduct, RetailSale, RetailSaleItem
from app.services.pricing import product_pricing_policy


def _xyz(months: list[Decimal]) -> str:
    if not months or sum(months) == 0:
        return "Z"
    mean = sum(months) / Decimal(len(months))
    variance = sum((value - mean) ** 2 for value in months) / Decimal(len(months))
    coefficient = variance.sqrt() / mean if mean else Decimal("99")
    if coefficient <= Decimal("0.50"):
        return "X"
    if coefficient <= Decimal("1.00"):
        return "Y"
    return "Z"


def _recommendation(abc: str, xyz: str, stock: Decimal, sold: Decimal) -> str:
    if sold == 0:
        return "Sin demanda registrada: no reordenar automaticamente; revisar promocion, devolucion a proveedor o liquidacion"
    if abc == "A" and xyz == "X":
        return "Alta prioridad: mantener disponibilidad y revisar punto de reorden con proveedor"
    if xyz == "Z":
        return "Demanda irregular: comprar contra pedido confirmado o reserva"
    if abc == "C" and stock > sold:
        return "Baja rotacion: reducir compra y consumir existencia actual"
    return "Revision periodica: ajustar compra con ventas, plazo del proveedor y existencia"


def inventory_policy_report(db: Session) -> list[dict[str, object]]:
    products = list(db.scalars(select(CatalogProduct).where(CatalogProduct.active.is_(True))))
    cutoff = datetime.now(UTC) - timedelta(days=180)
    sold_rows = list(
        db.execute(
            select(RetailSaleItem.product_id, RetailSaleItem.quantity, RetailSale.completed_at)
            .join(RetailSale, RetailSale.id == RetailSaleItem.sale_id)
            .where(RetailSale.completed_at >= cutoff)
        )
    )
    monthly: dict[str, dict[tuple[int, int], Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for product_id, quantity, completed_at in sold_rows:
        monthly[product_id][(completed_at.year, completed_at.month)] += Decimal(str(quantity))
    values = []
    for product in products:
        policy = product_pricing_policy(product)
        values.append((product, policy.landed_cost * product.stock_qty, policy))
    values.sort(key=lambda row: row[1], reverse=True)
    total_value = sum((row[1] for row in values), Decimal("0"))
    cumulative = Decimal("0")
    report = []
    for product, stock_value, policy in values:
        cumulative += stock_value
        share = cumulative / total_value if total_value else Decimal("1")
        abc = "A" if share <= Decimal("0.80") else "B" if share <= Decimal("0.95") else "C"
        demand = list(monthly[product.id].values())
        xyz = _xyz(demand)
        sold = sum(demand, Decimal("0"))
        report.append({
            "product_id": product.id, "sku": product.sku, "name": product.name,
            "abc_class": abc, "xyz_class": xyz, "stock_qty": str(product.stock_qty),
            "sold_180_days": str(sold), "stock_value": str(stock_value.quantize(Decimal('0.01'))),
            "minimum_sale_price": str(policy.minimum_sale_price),
            "suggested_sale_price": str(policy.suggested_sale_price),
            "recommendation": _recommendation(abc, xyz, product.stock_qty, sold),
        })
    return report
