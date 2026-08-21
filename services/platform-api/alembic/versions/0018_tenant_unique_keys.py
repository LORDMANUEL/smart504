"""Scope business identifiers by organization.

Revision ID: 0018_tenant_unique_keys
Revises: 0017_erp_integration_outbox

PostgreSQL receives the complete constraint replacement. SQLite is used only
for local migration smoke tests; it receives the composite indexes but keeps
its anonymous auto-indexes because SQLite cannot drop them in place.
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_tenant_unique_keys"
down_revision = "0017_erp_integration_outbox"
branch_labels = None
depends_on = None


KEYS = (
    ("catalog_categories", "name", "catalog_categories_name_key", "uq_catalog_category_org_name"),
    ("catalog_categories", "slug", "catalog_categories_slug_key", "uq_catalog_category_org_slug"),
    ("catalog_products", "sku", "catalog_products_sku_key", "uq_catalog_product_org_sku"),
    ("catalog_products", "slug", "catalog_products_slug_key", "uq_catalog_product_org_slug"),
    ("vehicles", "vin", "vehicles_vin_key", "uq_vehicle_org_vin"),
    ("store_orders", "order_number", "store_orders_order_number_key", "uq_store_order_org_number"),
    ("store_orders", "idempotency_key", "store_orders_idempotency_key_key", "uq_store_order_org_idempotency"),
    ("work_orders", "number", "work_orders_number_key", "uq_work_order_org_number"),
    ("quotes", "number", "quotes_number_key", "uq_quote_org_number"),
    ("payments", "receipt_number", "payments_receipt_number_key", "uq_payment_org_receipt"),
    ("branches", "code", "branches_code_key", "uq_branch_org_code"),
    ("warehouse_locations", "code", "warehouse_locations_code_key", "uq_warehouse_org_code"),
    ("retail_sales", "sale_number", "retail_sales_sale_number_key", "uq_retail_sale_org_number"),
    ("retail_sales", "invoice_number", "retail_sales_invoice_number_key", "uq_retail_sale_org_invoice"),
    ("retail_returns", "return_number", "retail_returns_return_number_key", "uq_retail_return_org_number"),
    ("inventory_reservations", "reference", "inventory_reservations_reference_key", "uq_inventory_reservation_org_ref"),
    ("inventory_transfers", "number", "inventory_transfers_number_key", "uq_inventory_transfer_org_number"),
    ("shipments", "number", "shipments_number_key", "uq_shipment_org_number"),
    ("quality_cases", "number", "quality_cases_number_key", "uq_quality_case_org_number"),
    ("sales_leads", "number", "sales_leads_number_key", "uq_sales_lead_org_number"),
)


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    inspector = sa.inspect(bind)
    for table, column, old_name, new_name in KEYS:
        if is_postgres:
            for constraint in inspector.get_unique_constraints(table):
                if constraint.get("column_names") == [column] and constraint.get("name"):
                    op.drop_constraint(str(constraint["name"]), table, type_="unique")
                    break
        op.create_index(new_name, table, ["organization_id", column], unique=True)


def downgrade() -> None:
    is_postgres = op.get_bind().dialect.name == "postgresql"
    for table, column, old_name, new_name in reversed(KEYS):
        op.drop_index(new_name, table_name=table)
        if is_postgres:
            op.create_unique_constraint(old_name, table, [column])
