"""Venta por mostrador, pagos y devoluciones.

Revision ID: 0012_counter_sales
Revises: 0011_staff_identity_rbac
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_counter_sales"
down_revision = "0011_staff_identity_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_balances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("warehouse_id", sa.String(36), sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("source_system", sa.String(30), nullable=False, server_default="LOCAL_PROJECTION"),
        sa.Column("source_reference", sa.String(180)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("warehouse_id", "product_id", name="uq_inventory_balance_warehouse_product"),
    )
    for column in ("organization_id", "warehouse_id", "product_id", "source_reference"):
        op.create_index(f"ix_inventory_balances_{column}", "inventory_balances", [column])
    op.create_index("ix_inventory_balance_org_product", "inventory_balances", ["organization_id", "product_id"])

    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("warehouse_id", sa.String(36), sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("reference", sa.String(80), nullable=False),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("erpnext_stock_entry_id", sa.String(180)),
        sa.Column("sync_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("organization_id", "warehouse_id", "product_id", "movement_type", "reference", "erpnext_stock_entry_id", "sync_status"):
        op.create_index(f"ix_inventory_movements_{column}", "inventory_movements", [column])
    op.create_index("ix_inventory_movement_reference_created", "inventory_movements", ["reference", "created_at"])

    op.create_table(
        "retail_sales",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("warehouse_id", sa.String(36), sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cash_session_id", sa.String(36), sa.ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sale_number", sa.String(50), nullable=False, unique=True),
        sa.Column("invoice_number", sa.String(50), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("customer_name", sa.String(180), nullable=False),
        sa.Column("phone", sa.String(40)),
        sa.Column("tax_id", sa.String(80)),
        sa.Column("vehicle_vin", sa.String(40)),
        sa.Column("status", sa.String(30), nullable=False, server_default="COMPLETED"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="HNL"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tax", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("payment_reference", sa.String(180)),
        sa.Column("erpnext_invoice_id", sa.String(180)),
        sa.Column("sync_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("organization_id", "branch_id", "warehouse_id", "cash_session_id", "sale_number", "invoice_number", "customer_id", "phone", "tax_id", "vehicle_vin", "status", "payment_method", "erpnext_invoice_id", "sync_status"):
        op.create_index(f"ix_retail_sales_{column}", "retail_sales", [column])
    op.create_index("ix_retail_sale_org_created", "retail_sales", ["organization_id", "created_at"])
    op.create_index("ix_retail_sale_branch_status", "retail_sales", ["branch_id", "status"])

    op.create_table(
        "retail_sale_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sale_id", sa.String(36), sa.ForeignKey("retail_sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("returned_quantity", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_retail_sale_items_sale_id", "retail_sale_items", ["sale_id"])
    op.create_index("ix_retail_sale_items_product_id", "retail_sale_items", ["product_id"])

    op.create_table(
        "retail_returns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sale_id", sa.String(36), sa.ForeignKey("retail_sales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("return_number", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="COMPLETED"),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("reference", sa.String(180)),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_retail_returns_sale_id", "retail_returns", ["sale_id"])
    op.create_index("ix_retail_returns_return_number", "retail_returns", ["return_number"])
    op.create_index("ix_retail_returns_status", "retail_returns", ["status"])
    op.create_index("ix_retail_return_sale_created", "retail_returns", ["sale_id", "created_at"])

    op.create_table(
        "retail_return_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("return_id", sa.String(36), sa.ForeignKey("retail_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_item_id", sa.String(36), sa.ForeignKey("retail_sale_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_refund", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_retail_return_items_return_id", "retail_return_items", ["return_id"])
    op.create_index("ix_retail_return_items_sale_item_id", "retail_return_items", ["sale_item_id"])

    op.alter_column("payments", "work_order_id", existing_type=sa.String(36), nullable=True)
    op.add_column("payments", sa.Column("retail_sale_id", sa.String(36)))
    op.create_foreign_key(
        "fk_payments_retail_sale_id", "payments", "retail_sales", ["retail_sale_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_index("ix_payments_retail_sale_id", "payments", ["retail_sale_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_retail_sale_id", table_name="payments")
    op.drop_constraint("fk_payments_retail_sale_id", "payments", type_="foreignkey")
    op.drop_column("payments", "retail_sale_id")
    op.alter_column("payments", "work_order_id", existing_type=sa.String(36), nullable=False)
    op.drop_table("retail_return_items")
    op.drop_table("retail_returns")
    op.drop_table("retail_sale_items")
    op.drop_table("retail_sales")
    op.drop_table("inventory_movements")
    op.drop_table("inventory_balances")
