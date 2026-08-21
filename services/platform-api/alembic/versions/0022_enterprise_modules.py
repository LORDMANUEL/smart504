"""Add operational enterprise modules without duplicating the ERP ledger.

Revision ID: 0022_enterprise_modules
Revises: 0021_quote_inventory_erp
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_enterprise_modules"
down_revision = "0021_quote_inventory_erp"
branch_labels = None
depends_on = None


def _common(table: str) -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table("suppliers", *_common("suppliers"),
        sa.Column("code", sa.String(60), nullable=False), sa.Column("name", sa.String(180), nullable=False),
        sa.Column("tax_id", sa.String(80)), sa.Column("email", sa.String(254)), sa.Column("phone", sa.String(40)),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="HNL"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("erpnext_supplier_id", sa.String(180)), sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("erp_sync_error", sa.String(500)), sa.UniqueConstraint("organization_id", "code", name="uq_supplier_org_code"))
    op.create_index("ix_supplier_org_active_name", "suppliers", ["organization_id", "active", "name"])
    op.create_index("ix_suppliers_organization_id", "suppliers", ["organization_id"])
    op.create_index("ix_suppliers_tax_id", "suppliers", ["tax_id"])
    op.create_index("ix_suppliers_erpnext_supplier_id", "suppliers", ["erpnext_supplier_id"])
    op.create_index("ix_suppliers_erp_sync_status", "suppliers", ["erp_sync_status"])

    op.create_table("purchase_orders", *_common("purchase_orders"),
        sa.Column("number", sa.String(60), nullable=False), sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="SET NULL")),
        sa.Column("supplier_id", sa.String(36), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"), sa.Column("currency", sa.String(3), nullable=False, server_default="HNL"),
        sa.Column("exchange_rate", sa.Numeric(14,6), nullable=False, server_default="1"),
        sa.Column("subtotal", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("tax", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("expected_at", sa.DateTime(timezone=True)), sa.Column("notes", sa.Text()),
        sa.Column("items_json", sa.JSON(), nullable=False), sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("erpnext_purchase_order_id", sa.String(180)), sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("erp_sync_error", sa.String(500)), sa.Column("erp_last_synced_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("organization_id", "number", name="uq_purchase_order_org_number"))
    op.create_index("ix_purchase_order_org_status_created", "purchase_orders", ["organization_id", "status", "created_at"])
    for col in ("organization_id", "branch_id", "supplier_id", "status", "expected_at", "erpnext_purchase_order_id", "erp_sync_status"):
        op.create_index(f"ix_purchase_orders_{col}", "purchase_orders", [col])

    op.create_table("import_cases", *_common("import_cases"),
        sa.Column("number", sa.String(60), nullable=False), sa.Column("purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PLANNED"), sa.Column("incoterm", sa.String(10), nullable=False),
        sa.Column("origin_country", sa.String(80), nullable=False), sa.Column("destination_port", sa.String(120), nullable=False), sa.Column("eta", sa.DateTime(timezone=True)),
        sa.Column("costs_json", sa.JSON(), nullable=False), sa.Column("documents_json", sa.JSON(), nullable=False),
        sa.Column("additional_cost_total", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("allocation_method", sa.String(30), nullable=False, server_default="BY_VALUE"),
        sa.Column("landed_cost_status", sa.String(30), nullable=False, server_default="PENDING"), sa.Column("erpnext_landed_cost_id", sa.String(180)),
        sa.Column("created_by", sa.String(120), nullable=False), sa.UniqueConstraint("organization_id", "number", name="uq_import_case_org_number"))
    op.create_index("ix_import_case_org_status_eta", "import_cases", ["organization_id", "status", "eta"])
    for col in ("organization_id", "purchase_order_id", "status", "eta", "erpnext_landed_cost_id"):
        op.create_index(f"ix_import_cases_{col}", "import_cases", [col])

    op.create_table("employee_contracts", *_common("employee_contracts"),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="SET NULL")), sa.Column("staff_user_id", sa.Uuid(), sa.ForeignKey("staff_users.id", ondelete="SET NULL")),
        sa.Column("employee_code", sa.String(60), nullable=False), sa.Column("employee_name", sa.String(180), nullable=False), sa.Column("job_title", sa.String(120), nullable=False),
        sa.Column("contract_type", sa.String(30), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("start_date", sa.Date(), nullable=False), sa.Column("end_date", sa.Date()), sa.Column("monthly_salary", sa.Numeric(14,2), nullable=False),
        sa.Column("standard_hours_weekly", sa.Numeric(6,2), nullable=False), sa.Column("currency", sa.String(3), nullable=False, server_default="HNL"),
        sa.Column("benefits_json", sa.JSON(), nullable=False), sa.Column("erpnext_employee_id", sa.String(180)), sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.UniqueConstraint("organization_id", "employee_code", name="uq_employee_contract_org_code"))
    op.create_index("ix_employee_contract_org_status", "employee_contracts", ["organization_id", "status"])
    for col in ("organization_id", "branch_id", "staff_user_id", "status", "erpnext_employee_id", "erp_sync_status"):
        op.create_index(f"ix_employee_contracts_{col}", "employee_contracts", [col])

    op.create_table("attendance_entries", *_common("attendance_entries"),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("employee_contracts.id", ondelete="CASCADE"), nullable=False), sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("regular_hours", sa.Numeric(6,2), nullable=False, server_default="0"), sa.Column("overtime_hours", sa.Numeric(6,2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PRESENT"), sa.Column("check_in_at", sa.DateTime(timezone=True)), sa.Column("check_out_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.String(500)), sa.Column("recorded_by", sa.String(120), nullable=False),
        sa.UniqueConstraint("organization_id", "contract_id", "work_date", name="uq_attendance_contract_date"))
    op.create_index("ix_attendance_org_date", "attendance_entries", ["organization_id", "work_date"])
    for col in ("organization_id", "contract_id"):
        op.create_index(f"ix_attendance_entries_{col}", "attendance_entries", [col])

    op.create_table("leave_requests", *_common("leave_requests"),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("employee_contracts.id", ondelete="CASCADE"), nullable=False), sa.Column("leave_type", sa.String(40), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False), sa.Column("end_date", sa.Date(), nullable=False), sa.Column("reason", sa.String(500)),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"), sa.Column("requested_by", sa.String(120), nullable=False), sa.Column("approved_by", sa.String(120)))
    op.create_index("ix_leave_org_status_start", "leave_requests", ["organization_id", "status", "start_date"])
    for col in ("organization_id", "contract_id", "status"):
        op.create_index(f"ix_leave_requests_{col}", "leave_requests", [col])

    op.create_table("payroll_runs", *_common("payroll_runs"),
        sa.Column("number", sa.String(60), nullable=False), sa.Column("period_start", sa.Date(), nullable=False), sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"), sa.Column("lines_json", sa.JSON(), nullable=False),
        sa.Column("gross_total", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("deduction_total", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("net_total", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("erpnext_payroll_entry_id", sa.String(180)), sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="NOT_REQUIRED"),
        sa.UniqueConstraint("organization_id", "number", name="uq_payroll_run_org_number"))
    op.create_index("ix_payroll_org_status_period", "payroll_runs", ["organization_id", "status", "period_start"])
    for col in ("organization_id", "status", "erpnext_payroll_entry_id", "erp_sync_status"):
        op.create_index(f"ix_payroll_runs_{col}", "payroll_runs", [col])

    op.create_table("used_vehicles", *_common("used_vehicles"),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="SET NULL")), sa.Column("vin", sa.String(32), nullable=False),
        sa.Column("make", sa.String(80), nullable=False), sa.Column("model", sa.String(100), nullable=False), sa.Column("model_year", sa.Integer(), nullable=False),
        sa.Column("mileage_km", sa.Integer()), sa.Column("acquisition_type", sa.String(30), nullable=False), sa.Column("acquisition_cost", sa.Numeric(14,2), nullable=False),
        sa.Column("reconditioning_cost", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("target_sale_price", sa.Numeric(14,2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="APPRAISAL"), sa.Column("owner_name", sa.String(180)),
        sa.Column("inspection_json", sa.JSON(), nullable=False), sa.Column("media_json", sa.JSON(), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("sold_at", sa.DateTime(timezone=True)), sa.Column("erpnext_item_id", sa.String(180)), sa.Column("created_by", sa.String(120), nullable=False),
        sa.UniqueConstraint("organization_id", "vin", name="uq_used_vehicle_org_vin"))
    op.create_index("ix_used_vehicle_org_status", "used_vehicles", ["organization_id", "status"])
    for col in ("organization_id", "branch_id", "status", "erpnext_item_id"):
        op.create_index(f"ix_used_vehicles_{col}", "used_vehicles", [col])

    op.create_table("social_channels", *_common("social_channels"),
        sa.Column("channel_type", sa.String(30), nullable=False), sa.Column("name", sa.String(120), nullable=False),
        sa.Column("external_account_id", sa.String(180), nullable=False), sa.Column("credential_reference", sa.String(300), nullable=False),
        sa.Column("webhook_status", sa.String(30), nullable=False, server_default="PENDING"), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("organization_id", "channel_type", "external_account_id", name="uq_social_channel_account"))
    op.create_index("ix_social_channel_org_active", "social_channels", ["organization_id", "active"])
    op.create_index("ix_social_channels_organization_id", "social_channels", ["organization_id"])

    op.create_table("social_conversations", *_common("social_conversations"),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("social_channels.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contact_name", sa.String(180), nullable=False), sa.Column("contact_handle", sa.String(180), nullable=False), sa.Column("subject", sa.String(240)),
        sa.Column("status", sa.String(30), nullable=False, server_default="NEW"), sa.Column("consent_status", sa.String(30), nullable=False, server_default="UNKNOWN"),
        sa.Column("assigned_to", sa.String(120)), sa.Column("lead_id", sa.String(36), sa.ForeignKey("sales_leads.id", ondelete="SET NULL")),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_social_conversation_org_status_updated", "social_conversations", ["organization_id", "status", "updated_at"])
    for col in ("organization_id", "channel_id", "contact_handle", "status", "assigned_to", "lead_id"):
        op.create_index(f"ix_social_conversations_{col}", "social_conversations", [col])

    op.create_table("social_messages",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("social_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("human_approved", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("provider_reference", sa.String(180)),
        sa.Column("sent_by", sa.String(120), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_social_message_conversation_created", "social_messages", ["conversation_id", "created_at"])
    for col in ("organization_id", "conversation_id", "provider_reference"):
        op.create_index(f"ix_social_messages_{col}", "social_messages", [col])


def downgrade() -> None:
    for table in ("social_messages", "social_conversations", "social_channels", "used_vehicles", "payroll_runs", "leave_requests", "attendance_entries", "employee_contracts", "import_cases", "purchase_orders", "suppliers"):
        op.drop_table(table)
