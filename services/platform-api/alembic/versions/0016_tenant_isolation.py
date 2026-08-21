"""Add tenant isolation keys to operational aggregates.

Revision ID: 0016_tenant_isolation
Revises: 0015_labor_costing
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_tenant_isolation"
down_revision = "0015_labor_costing"
branch_labels = None
depends_on = None


TENANT_TABLES = (
    "catalog_categories",
    "catalog_products",
    "catalog_product_images",
    "customers",
    "vehicles",
    "bookings",
    "store_orders",
    "store_order_items",
    "work_orders",
    "work_order_events",
    "quotes",
    "quote_lines",
    "cash_sessions",
    "payments",
    "warehouse_locations",
    "retail_sale_items",
    "retail_returns",
    "retail_return_items",
    "approval_requests",
    "inventory_reservations",
    "inventory_transfers",
    "shipments",
    "quality_cases",
    "vehicle_history_events",
    "sales_leads",
    "management_documents",
    "document_template_versions",
    "flow_events",
    "chat_sessions",
    "chat_messages",
)


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.add_column(
            table,
            sa.Column(
                "organization_id",
                sa.String(60),
                nullable=False,
                server_default="SMARTDIAG504",
            ),
        )
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.drop_index(f"ix_{table}_organization_id", table_name=table)
        op.drop_column(table, "organization_id")
