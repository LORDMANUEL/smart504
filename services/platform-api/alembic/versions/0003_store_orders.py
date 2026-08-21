"""Create public parts order request schema.

Revision ID: 0003_store_orders
Revises: 0002_chatbot
Create Date: 2026-08-12
"""
from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_store_orders"
down_revision: str | None = "0002_chatbot"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "store_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_number", sa.String(40), nullable=False, unique=True),
        sa.Column("customer_name", sa.String(180), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("email", sa.String(254)),
        sa.Column("vehicle_vin", sa.String(40)),
        sa.Column("notes", sa.Text()),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("erpnext_sales_order_id", sa.String(180)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_store_orders_order_number", "store_orders", ["order_number"])
    op.create_index("ix_store_orders_phone", "store_orders", ["phone"])
    op.create_index("ix_store_orders_vehicle_vin", "store_orders", ["vehicle_vin"])
    op.create_index("ix_store_orders_status", "store_orders", ["status"])
    op.create_index("ix_store_orders_status_created", "store_orders", ["status", "created_at"])
    op.create_index(
        "ix_store_orders_erpnext_sales_order_id", "store_orders", ["erpnext_sales_order_id"]
    )

    op.create_table(
        "store_order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("store_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("catalog_products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_store_order_items_order_id", "store_order_items", ["order_id"])
    op.create_index("ix_store_order_items_product_id", "store_order_items", ["product_id"])


def downgrade() -> None:
    op.drop_table("store_order_items")
    op.drop_table("store_orders")
