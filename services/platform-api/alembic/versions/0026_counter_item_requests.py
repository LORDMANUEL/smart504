"""counter item demand requests

Revision ID: 0026_counter_item_requests
Revises: 0025_hn_payroll
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_counter_item_requests"
down_revision = "0025_hn_payroll"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "counter_item_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("number", sa.String(60), nullable=False),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("warehouse_id", sa.String(36), sa.ForeignKey("warehouse_locations.id", ondelete="SET NULL")),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("catalog_products.id", ondelete="SET NULL")),
        sa.Column("search_query", sa.String(240), nullable=False),
        sa.Column("customer_name", sa.String(180), nullable=False),
        sa.Column("phone", sa.String(40)),
        sa.Column("vehicle_vin", sa.String(40)),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="NEW"),
        sa.Column("requested_by", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("number", name="uq_counter_item_request_number"),
    )
    for name, columns in (
        ("ix_counter_item_requests_organization_id", ["organization_id"]),
        ("ix_counter_item_requests_number", ["number"]),
        ("ix_counter_item_requests_branch_id", ["branch_id"]),
        ("ix_counter_item_requests_warehouse_id", ["warehouse_id"]),
        ("ix_counter_item_requests_product_id", ["product_id"]),
        ("ix_counter_item_requests_search_query", ["search_query"]),
        ("ix_counter_item_requests_phone", ["phone"]),
        ("ix_counter_item_requests_vehicle_vin", ["vehicle_vin"]),
        ("ix_counter_item_requests_status", ["status"]),
        ("ix_counter_item_request_org_status", ["organization_id", "status"]),
        ("ix_counter_item_request_branch_created", ["branch_id", "created_at"]),
    ):
        op.create_index(name, "counter_item_requests", columns)


def downgrade() -> None:
    op.drop_table("counter_item_requests")
