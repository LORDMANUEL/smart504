"""Create SmartDiag504 operational and catalog schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-12
"""
from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("slug", sa.String(140), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_catalog_categories_slug", "catalog_categories", ["slug"])

    op.create_table(
        "catalog_products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sku", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("short_description", sa.String(320)),
        sa.Column("description", sa.Text()),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("catalog_categories.id", ondelete="SET NULL")),
        sa.Column("brand", sa.String(100)),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("stock_qty", sa.Numeric(14, 3), nullable=False),
        sa.Column("stock_status", sa.String(30), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("compatibility_notes", sa.Text()),
        sa.Column("source_system", sa.String(30), nullable=False),
        sa.Column("source_reference", sa.String(180)),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_catalog_products_sku", "catalog_products", ["sku"])
    op.create_index("ix_catalog_products_slug", "catalog_products", ["slug"])
    op.create_index("ix_catalog_products_name", "catalog_products", ["name"])
    op.create_index("ix_catalog_products_category_id", "catalog_products", ["category_id"])
    op.create_index("ix_catalog_product_active_category", "catalog_products", ["active", "category_id"])

    op.create_table(
        "catalog_product_images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("public_url", sa.String(700), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("source_page_url", sa.String(1000)),
        sa.Column("attribution_text", sa.String(500)),
        sa.Column("license_name", sa.String(120)),
        sa.Column("license_url", sa.String(1000)),
        sa.Column("mime_type", sa.String(60), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("product_id", "sha256", name="uq_product_image_sha256"),
    )
    op.create_index("ix_catalog_product_images_product_id", "catalog_product_images", ["product_id"])

    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("email", sa.String(254)),
        sa.Column("tax_id", sa.String(80)),
        sa.Column("erpnext_customer_id", sa.String(180)),
        *_timestamps(),
    )
    op.create_index("ix_customers_phone", "customers", ["phone"])

    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vin", sa.String(40), unique=True),
        sa.Column("plate", sa.String(30)),
        sa.Column("make", sa.String(80), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("model_year", sa.Integer()),
        sa.Column("engine", sa.String(120)),
        sa.Column("transmission", sa.String(120)),
        sa.Column("mileage_km", sa.Integer()),
        *_timestamps(),
    )
    op.create_index("ix_vehicles_customer_id", "vehicles", ["customer_id"])
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"])
    op.create_index("ix_vehicles_plate", "vehicles", ["plate"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("email", sa.String(254)),
        sa.Column("vehicle_summary", sa.String(240), nullable=False),
        sa.Column("service_requested", sa.String(180), nullable=False),
        sa.Column("preferred_date", sa.String(30)),
        sa.Column("concern", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_bookings_phone", "bookings", ["phone"])

    op.create_table(
        "workshop_settings",
        sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(40), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("concern", sa.Text(), nullable=False),
        sa.Column("diagnosis", sa.Text()),
        sa.Column("technician_quote", sa.JSON()),
        sa.Column("parts_required", sa.JSON()),
        sa.Column("assigned_technicians", sa.JSON(), nullable=False),
        sa.Column("bay_code", sa.String(40)),
        sa.Column("promised_at", sa.DateTime(timezone=True)),
        sa.Column("invoice_reference", sa.String(180)),
        sa.Column("erpnext_service_order_id", sa.String(180)),
        sa.Column("erpnext_invoice_id", sa.String(180)),
        *_timestamps(),
    )
    op.create_index("ix_work_orders_number", "work_orders", ["number"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_customer_id", "work_orders", ["customer_id"])
    op.create_index("ix_work_orders_vehicle_id", "work_orders", ["vehicle_id"])

    op.create_table(
        "work_order_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("work_order_id", sa.String(36), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("from_status", sa.String(50)),
        sa.Column("to_status", sa.String(50)),
        sa.Column("actor", sa.String(180), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("work_order_id", "idempotency_key", name="uq_work_order_event_key"),
    )
    op.create_index("ix_work_order_events_work_order_id", "work_order_events", ["work_order_id"])

    op.create_table(
        "node_heartbeats",
        sa.Column("node_id", sa.String(120), primary_key=True),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_heartbeats_last_seen_at", "node_heartbeats", ["last_seen_at"])

    op.create_table(
        "leader_leases",
        sa.Column("lease_name", sa.String(120), primary_key=True),
        sa.Column("holder_node_id", sa.String(120), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
    )
    op.create_index("ix_leader_leases_holder_node_id", "leader_leases", ["holder_node_id"])


def downgrade() -> None:
    for table in [
        "leader_leases",
        "node_heartbeats",
        "work_order_events",
        "work_orders",
        "workshop_settings",
        "bookings",
        "vehicles",
        "customers",
        "catalog_product_images",
        "catalog_products",
        "catalog_categories",
    ]:
        op.drop_table(table)
