"""Add protected staff compensation and work-order labor costing.

Revision ID: 0015_labor_costing
Revises: 0014_pricing_and_approvals
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_labor_costing"
down_revision = "0014_pricing_and_approvals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_compensation_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("staff_user_id", sa.Uuid(), sa.ForeignKey("staff_users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("fixed_monthly_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("productive_hours_monthly", sa.Numeric(8, 2), nullable=False),
        sa.Column("base_hourly_wage", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("specialized_hourly_wage", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("employer_burden_percent", sa.Numeric(7, 2), nullable=False, server_default="0"),
        sa.Column("standard_sale_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("specialized_sale_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="HNL"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("source_system", sa.String(30), nullable=False, server_default="LOCAL_PROJECTION"),
        sa.Column("source_reference", sa.String(180)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("productive_hours_monthly > 0", name="ck_staff_comp_productive_hours"),
        sa.CheckConstraint("employer_burden_percent >= 0", name="ck_staff_comp_burden"),
    )
    op.create_index("ix_staff_compensation_profiles_organization_id", "staff_compensation_profiles", ["organization_id"])
    op.create_index("ix_staff_compensation_profiles_staff_user_id", "staff_compensation_profiles", ["staff_user_id"])
    op.create_index("ix_staff_compensation_profiles_source_reference", "staff_compensation_profiles", ["source_reference"])
    op.create_index("ix_staff_comp_org_effective", "staff_compensation_profiles", ["organization_id", "effective_from"])

    op.create_table(
        "work_order_labor_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("work_order_id", sa.String(36), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("technician_user_id", sa.Uuid(), sa.ForeignKey("staff_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("technician_name", sa.String(180), nullable=False),
        sa.Column("service_code", sa.String(80), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("rate_kind", sa.String(20), nullable=False),
        sa.Column("hours", sa.Numeric(8, 3), nullable=False),
        sa.Column("hourly_cost_snapshot", sa.Numeric(12, 2), nullable=False),
        sa.Column("hourly_sale_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("hours > 0", name="ck_work_order_labor_hours"),
    )
    for column in ("organization_id", "work_order_id", "technician_user_id", "service_code"):
        op.create_index(f"ix_work_order_labor_entries_{column}", "work_order_labor_entries", [column])
    op.create_index("ix_work_order_labor_technician_created", "work_order_labor_entries", ["technician_user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("work_order_labor_entries")
    op.drop_table("staff_compensation_profiles")
