"""Add ERP pricing policy and owner approval requests.

Revision ID: 0014_pricing_and_approvals
Revises: 0013_counter_sales_erp_outbox
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_pricing_and_approvals"
down_revision = "0013_counter_sales_erp_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalog_products", sa.Column("purchase_cost", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("catalog_products", sa.Column("landed_cost_factor", sa.Numeric(8, 4), nullable=False, server_default="1"))
    op.add_column("catalog_products", sa.Column("target_markup_percent", sa.Numeric(7, 2), nullable=False, server_default="30"))
    op.add_column("catalog_products", sa.Column("minimum_markup_percent", sa.Numeric(7, 2), nullable=False, server_default="0"))
    op.add_column("catalog_products", sa.Column("abc_class", sa.String(1), nullable=False, server_default="C"))
    op.add_column("catalog_products", sa.Column("xyz_class", sa.String(1), nullable=False, server_default="Z"))
    op.create_index("ix_catalog_products_abc_class", "catalog_products", ["abc_class"])
    op.create_index("ix_catalog_products_xyz_class", "catalog_products", ["xyz_class"])
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sale_id", sa.String(36), sa.ForeignKey("retail_sales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("requested_by", sa.String(120), nullable=False),
        sa.Column("owner_email", sa.String(254), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("delivery_error", sa.String(500)),
        sa.Column("decided_by", sa.String(254)),
        sa.Column("decision_comment", sa.String(500)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("sale_id", "request_type", "status", "owner_email", "token_hash", "expires_at"):
        op.create_index(f"ix_approval_requests_{column}", "approval_requests", [column])
    op.create_index("ix_approval_request_status_created", "approval_requests", ["status", "created_at"])
    op.create_index("ix_approval_request_sale_type", "approval_requests", ["sale_id", "request_type"])


def downgrade() -> None:
    op.drop_table("approval_requests")
    op.drop_index("ix_catalog_products_xyz_class", table_name="catalog_products")
    op.drop_index("ix_catalog_products_abc_class", table_name="catalog_products")
    for column in ("xyz_class", "abc_class", "minimum_markup_percent", "target_markup_percent", "landed_cost_factor", "purchase_cost"):
        op.drop_column("catalog_products", column)
