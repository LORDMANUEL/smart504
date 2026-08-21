"""employee self service and configurable Honduras payroll

Revision ID: 0025_hn_payroll
Revises: 0024_procurement_hr_operations
"""

from alembic import op
import sqlalchemy as sa


revision = "0025_hn_payroll"
down_revision = "0024_procurement_hr_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_template_versions", sa.Column("print_profile_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    for column in (
        sa.Column("national_id", sa.String(80)), sa.Column("address", sa.String(500)),
        sa.Column("phone", sa.String(40)), sa.Column("email", sa.String(254)),
        sa.Column("social_security_number", sa.String(80)),
        sa.Column("insurance_provider", sa.String(120)),
        sa.Column("insurance_member_number", sa.String(120)),
        sa.Column("payment_type", sa.String(30), nullable=False, server_default="MONTHLY"),
        sa.Column("base_pay_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
    ):
        op.add_column("employee_contracts", column)
    op.execute("UPDATE employee_contracts SET base_pay_amount = monthly_salary WHERE base_pay_amount = 0")
    op.create_index("ix_employee_contracts_national_id", "employee_contracts", ["national_id"])
    op.create_index("ix_employee_contracts_email", "employee_contracts", ["email"])

    op.create_table(
        "payroll_policies",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("code", sa.String(60), nullable=False), sa.Column("name", sa.String(180), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False), sa.Column("effective_until", sa.Date()),
        sa.Column("rules_json", sa.JSON(), nullable=False), sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("approved_by", sa.String(120), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", "effective_from", name="uq_payroll_policy_org_code_effective"),
    )
    op.create_index("ix_payroll_policies_organization_id", "payroll_policies", ["organization_id"])
    op.create_index("ix_payroll_policy_org_active_effective", "payroll_policies", ["organization_id", "active", "effective_from"])

    op.create_table(
        "payroll_vouchers",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("number", sa.String(60), nullable=False),
        sa.Column("payroll_run_id", sa.String(36), sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("employee_contracts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False), sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("gross", sa.Numeric(14, 2), nullable=False), sa.Column("deductions", sa.Numeric(14, 2), nullable=False),
        sa.Column("employer_contributions", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("net", sa.Numeric(14, 2), nullable=False), sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"), sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("payroll_run_id", "contract_id", name="uq_payroll_voucher_run_contract"),
        sa.UniqueConstraint("organization_id", "number", name="uq_payroll_voucher_org_number"),
    )
    for name, columns in (
        ("ix_payroll_vouchers_organization_id", ["organization_id"]), ("ix_payroll_vouchers_payroll_run_id", ["payroll_run_id"]),
        ("ix_payroll_vouchers_contract_id", ["contract_id"]), ("ix_payroll_vouchers_status", ["status"]),
    ):
        op.create_index(name, "payroll_vouchers", columns)


def downgrade() -> None:
    op.drop_table("payroll_vouchers")
    op.drop_table("payroll_policies")
    op.drop_index("ix_employee_contracts_email", table_name="employee_contracts")
    op.drop_index("ix_employee_contracts_national_id", table_name="employee_contracts")
    for name in ("base_pay_amount", "payment_type", "insurance_member_number", "insurance_provider", "social_security_number", "email", "phone", "address", "national_id"):
        op.drop_column("employee_contracts", name)
    op.drop_column("document_template_versions", "print_profile_json")
