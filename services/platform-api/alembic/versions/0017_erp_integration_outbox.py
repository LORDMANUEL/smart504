"""Add general ERP integration outbox and OT projection status.

Revision ID: 0017_erp_integration_outbox
Revises: 0016_tenant_isolation
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_erp_integration_outbox"
down_revision = "0016_tenant_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="PENDING"),
    )
    op.add_column("work_orders", sa.Column("erp_sync_error", sa.String(500)))
    op.add_column("work_orders", sa.Column("erp_last_synced_at", sa.DateTime(timezone=True)))
    op.create_index("ix_work_orders_erp_sync_status", "work_orders", ["erp_sync_status"])
    op.create_index("ix_work_orders_erp_last_synced_at", "work_orders", ["erp_last_synced_at"])
    op.create_table(
        "erp_integration_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("aggregate_type", sa.String(40), nullable=False),
        sa.Column("aggregate_id", sa.String(120), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_reference", sa.String(180)),
        sa.Column("last_error", sa.String(500)),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "idempotency_key", name="uq_erp_job_org_idempotency"
        ),
    )
    for column in (
        "organization_id",
        "operation",
        "status",
        "target_reference",
        "next_attempt_at",
        "processed_at",
    ):
        op.create_index(f"ix_erp_integration_jobs_{column}", "erp_integration_jobs", [column])
    op.create_index(
        "ix_erp_job_org_status_created",
        "erp_integration_jobs",
        ["organization_id", "status", "created_at"],
    )
    op.create_index(
        "ix_erp_job_aggregate",
        "erp_integration_jobs",
        ["aggregate_type", "aggregate_id"],
    )


def downgrade() -> None:
    op.drop_table("erp_integration_jobs")
    op.drop_column("work_orders", "erp_last_synced_at")
    op.drop_column("work_orders", "erp_sync_error")
    op.drop_column("work_orders", "erp_sync_status")
