"""Add multi-branch operations, logistics, quality, VIN history and leads.

Revision ID: 0008_operations_control_hub
Revises: 0007_client_calendar_cashier
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0008_operations_control_hub"
down_revision: str | None = "0007_client_calendar_cashier"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("photo_url", sa.String(1000)))
    op.add_column("store_orders", sa.Column("branch_id", sa.String(36)))
    op.add_column("store_orders", sa.Column("assigned_cashier", sa.String(120)))
    op.add_column(
        "store_orders",
        sa.Column(
            "fulfillment_status", sa.String(40), nullable=False, server_default="AWAITING_REVIEW"
        ),
    )
    op.add_column("store_orders", sa.Column("reservation_expires_at", sa.DateTime(timezone=True)))
    op.add_column(
        "store_orders",
        sa.Column("whatsapp_status", sa.String(30), nullable=False, server_default="PENDING"),
    )
    op.add_column("store_orders", sa.Column("customer_id", sa.String(36)))
    for column in ("branch_id", "assigned_cashier", "fulfillment_status", "customer_id"):
        op.create_index(f"ix_store_orders_{column}", "store_orders", [column])

    op.add_column(
        "quote_lines",
        sa.Column("approval_status", sa.String(30), nullable=False, server_default="PENDING"),
    )
    op.add_column("quote_lines", sa.Column("source_reference", sa.String(180)))
    op.create_index("ix_quote_lines_approval_status", "quote_lines", ["approval_status"])
    op.create_index("ix_quote_lines_source_reference", "quote_lines", ["source_reference"])

    op.create_table(
        "branches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address", sa.String(500)),
        sa.Column("phone", sa.String(40)),
        sa.Column("email_domain", sa.String(180)),
        sa.Column("timezone", sa.String(80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_branches_organization_id", "branches", ["organization_id"])
    op.create_index("ix_branches_code", "branches", ["code"])
    op.create_foreign_key(
        "fk_store_orders_branch_id",
        "store_orders",
        "branches",
        ["branch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_store_orders_customer_id",
        "store_orders",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "warehouse_locations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "branch_id",
            sa.String(36),
            sa.ForeignKey("branches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("warehouse_type", sa.String(30), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_warehouse_locations_branch_id", "warehouse_locations", ["branch_id"])
    op.create_index("ix_warehouse_locations_code", "warehouse_locations", ["code"])
    op.create_index(
        "ix_warehouse_locations_warehouse_type", "warehouse_locations", ["warehouse_type"]
    )
    op.create_index(
        "ix_warehouse_branch_type", "warehouse_locations", ["branch_id", "warehouse_type"]
    )

    op.create_table(
        "inventory_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reference", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("catalog_products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            sa.String(36),
            sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "store_order_id", sa.String(36), sa.ForeignKey("store_orders.id", ondelete="CASCADE")
        ),
        sa.Column(
            "work_order_id", sa.String(36), sa.ForeignKey("work_orders.id", ondelete="CASCADE")
        ),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "reference",
        "product_id",
        "warehouse_id",
        "store_order_id",
        "work_order_id",
        "status",
        "expires_at",
    ):
        op.create_index(f"ix_inventory_reservations_{column}", "inventory_reservations", [column])

    op.create_table(
        "inventory_transfers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "from_warehouse_id",
            sa.String(36),
            sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "to_warehouse_id",
            sa.String(36),
            sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("items_json", sa.JSON(), nullable=False),
        sa.Column("carrier", sa.String(160)),
        sa.Column("tracking_number", sa.String(180)),
        sa.Column("guide_image_url", sa.String(1000)),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("number", "from_warehouse_id", "to_warehouse_id", "status", "tracking_number"):
        op.create_index(f"ix_inventory_transfers_{column}", "inventory_transfers", [column])

    op.create_table(
        "shipments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "store_order_id",
            sa.String(36),
            sa.ForeignKey("store_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_warehouse_id",
            sa.String(36),
            sa.ForeignKey("warehouse_locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("carrier", sa.String(160), nullable=False),
        sa.Column("tracking_number", sa.String(180)),
        sa.Column("guide_image_url", sa.String(1000)),
        sa.Column("recipient_name", sa.String(180), nullable=False),
        sa.Column("recipient_phone", sa.String(40), nullable=False),
        sa.Column("delivery_notes", sa.Text()),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("number", "store_order_id", "from_warehouse_id", "status", "tracking_number"):
        op.create_index(f"ix_shipments_{column}", "shipments", [column])

    op.create_table(
        "quality_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(50), nullable=False, unique=True),
        sa.Column("case_type", sa.String(30), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column(
            "work_order_id", sa.String(36), sa.ForeignKey("work_orders.id", ondelete="SET NULL")
        ),
        sa.Column(
            "store_order_id", sa.String(36), sa.ForeignKey("store_orders.id", ondelete="SET NULL")
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text()),
        sa.Column("evidence_url", sa.String(1000)),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "number",
        "case_type",
        "customer_id",
        "vehicle_id",
        "work_order_id",
        "store_order_id",
        "status",
    ):
        op.create_index(f"ix_quality_cases_{column}", "quality_cases", [column])

    op.create_table(
        "vehicle_history_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("vin", sa.String(40), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("reference", sa.String(120), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("mileage_km", sa.Integer()),
        sa.Column("quality_result", sa.String(60)),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("vehicle_id", "vin", "event_type", "reference"):
        op.create_index(f"ix_vehicle_history_events_{column}", "vehicle_history_events", [column])
    op.create_index(
        "ix_vehicle_history_vin_created", "vehicle_history_events", ["vin", "created_at"]
    )

    op.create_table(
        "sales_leads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(50), nullable=False, unique=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("email", sa.String(254)),
        sa.Column("interest", sa.String(500), nullable=False),
        sa.Column("vehicle_summary", sa.String(240)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("assigned_to", sa.String(120)),
        sa.Column("chat_session_id", sa.String(36)),
        sa.Column("next_action_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "number",
        "source",
        "phone",
        "email",
        "status",
        "assigned_to",
        "chat_session_id",
        "next_action_at",
    ):
        op.create_index(f"ix_sales_leads_{column}", "sales_leads", [column])
    op.create_index("ix_sales_leads_status_created", "sales_leads", ["status", "created_at"])

    op.create_table(
        "management_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "branch_id",
            sa.String(36),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("number", sa.String(180), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("file_url", sa.String(1000)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("branch_id", "document_type", "valid_until", "status"):
        op.create_index(f"ix_management_documents_{column}", "management_documents", [column])


def downgrade() -> None:
    op.drop_constraint("fk_store_orders_customer_id", "store_orders", type_="foreignkey")
    op.drop_constraint("fk_store_orders_branch_id", "store_orders", type_="foreignkey")
    for table in (
        "management_documents",
        "sales_leads",
        "vehicle_history_events",
        "quality_cases",
        "shipments",
        "inventory_transfers",
        "inventory_reservations",
        "warehouse_locations",
        "branches",
    ):
        op.drop_table(table)
    op.drop_column("quote_lines", "source_reference")
    op.drop_column("quote_lines", "approval_status")
    for column in (
        "customer_id",
        "whatsapp_status",
        "reservation_expires_at",
        "fulfillment_status",
        "assigned_cashier",
        "branch_id",
    ):
        op.drop_column("store_orders", column)
    op.drop_column("vehicles", "photo_url")
