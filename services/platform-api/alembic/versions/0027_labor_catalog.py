"""persistent tenant labor catalog

Revision ID: 0027_labor_catalog
Revises: 0026_counter_item_requests
"""

from alembic import op
import sqlalchemy as sa


revision = "0027_labor_catalog"
down_revision = "0026_counter_item_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labor_catalog_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("standard_hours", sa.Numeric(8, 3), nullable=False),
        sa.Column("internal_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("sale_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("vehicle_rules", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("erp_item_code", sa.String(140)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("standard_hours > 0", name="ck_labor_catalog_hours"),
        sa.CheckConstraint("sale_price >= 0", name="ck_labor_catalog_sale_price"),
        sa.CheckConstraint("internal_cost >= 0", name="ck_labor_catalog_internal_cost"),
        sa.UniqueConstraint("organization_id", "code", name="uq_labor_catalog_org_code"),
    )
    op.create_index("ix_labor_catalog_items_organization_id", "labor_catalog_items", ["organization_id"])
    op.create_index("ix_labor_catalog_items_code", "labor_catalog_items", ["code"])
    op.create_index("ix_labor_catalog_items_erp_item_code", "labor_catalog_items", ["erp_item_code"])
    op.create_index("ix_labor_catalog_org_active", "labor_catalog_items", ["organization_id", "is_active"])
    op.execute(sa.text("""
        INSERT INTO labor_catalog_items
            (id, organization_id, code, description, standard_hours, internal_cost,
             sale_price, vehicle_rules, erp_item_code, is_active, created_at, updated_at)
        VALUES
            ('labor-diag-001', 'SMARTDIAG504', 'MO-DIAG-001', 'Diagnóstico electrónico completo', 1.5, 650, 1200, '[]', 'MO-DIAG-001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('labor-aceite-001', 'SMARTDIAG504', 'MO-ACEITE-001', 'Cambio de aceite y filtro', 0.7, 280, 650, '[]', 'MO-ACEITE-001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('labor-frenos-001', 'SMARTDIAG504', 'MO-FRENOS-001', 'Servicio de frenos delanteros', 2.0, 900, 1850, '[]', 'MO-FRENOS-001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('labor-susp-001', 'SMARTDIAG504', 'MO-SUSP-001', 'Inspección y ajuste de suspensión', 1.2, 520, 1100, '[]', 'MO-SUSP-001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('labor-ac-001', 'SMARTDIAG504', 'MO-AC-001', 'Diagnóstico de aire acondicionado', 1.0, 450, 950, '[]', 'MO-AC-001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """))


def downgrade() -> None:
    op.drop_table("labor_catalog_items")
