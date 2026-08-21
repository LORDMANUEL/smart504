"""Estado reintentable de sincronizacion ERP para mostrador.

Revision ID: 0013_counter_sales_erp_outbox
Revises: 0012_counter_sales
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_counter_sales_erp_outbox"
down_revision = "0012_counter_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("retail_sales", sa.Column("erpnext_payment_id", sa.String(180)))
    op.add_column("retail_sales", sa.Column("sync_error", sa.String(500)))
    op.add_column(
        "retail_sales", sa.Column("sync_attempts", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("retail_sales", sa.Column("last_sync_at", sa.DateTime(timezone=True)))
    op.create_index("ix_retail_sales_erpnext_payment_id", "retail_sales", ["erpnext_payment_id"])
    op.create_index("ix_retail_sales_last_sync_at", "retail_sales", ["last_sync_at"])

    op.add_column("retail_returns", sa.Column("erpnext_credit_note_id", sa.String(180)))
    op.add_column("retail_returns", sa.Column("erpnext_payment_id", sa.String(180)))
    op.add_column(
        "retail_returns",
        sa.Column("sync_status", sa.String(30), nullable=False, server_default="PENDING"),
    )
    op.add_column("retail_returns", sa.Column("sync_error", sa.String(500)))
    op.add_column(
        "retail_returns", sa.Column("sync_attempts", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("retail_returns", sa.Column("last_sync_at", sa.DateTime(timezone=True)))
    op.create_index(
        "ix_retail_returns_erpnext_credit_note_id", "retail_returns", ["erpnext_credit_note_id"]
    )
    op.create_index(
        "ix_retail_returns_erpnext_payment_id", "retail_returns", ["erpnext_payment_id"]
    )
    op.create_index("ix_retail_returns_sync_status", "retail_returns", ["sync_status"])
    op.create_index("ix_retail_returns_last_sync_at", "retail_returns", ["last_sync_at"])


def downgrade() -> None:
    raise RuntimeError("Forward-only migration: restore a verified backup to roll back")
