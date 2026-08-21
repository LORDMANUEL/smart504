"""Track ERP authority for quotations and warehouse transfers.

Revision ID: 0021_quote_inventory_erp
Revises: 0020_notification_outbox
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_quote_inventory_erp"
down_revision = "0020_notification_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quotes", sa.Column("erpnext_quotation_id", sa.String(180)))
    op.add_column(
        "quotes",
        sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="PENDING"),
    )
    op.add_column("quotes", sa.Column("erp_sync_error", sa.String(500)))
    op.add_column("quotes", sa.Column("erp_last_synced_at", sa.DateTime(timezone=True)))
    op.create_index("ix_quotes_erpnext_quotation_id", "quotes", ["erpnext_quotation_id"])
    op.create_index("ix_quotes_erp_sync_status", "quotes", ["erp_sync_status"])

    op.add_column("inventory_transfers", sa.Column("erpnext_stock_entry_id", sa.String(180)))
    op.add_column(
        "inventory_transfers",
        sa.Column("erp_sync_status", sa.String(30), nullable=False, server_default="NOT_REQUIRED"),
    )
    op.add_column("inventory_transfers", sa.Column("erp_sync_error", sa.String(500)))
    op.add_column(
        "inventory_transfers", sa.Column("erp_last_synced_at", sa.DateTime(timezone=True))
    )
    op.create_index(
        "ix_inventory_transfers_erpnext_stock_entry_id",
        "inventory_transfers",
        ["erpnext_stock_entry_id"],
    )
    op.create_index(
        "ix_inventory_transfers_erp_sync_status",
        "inventory_transfers",
        ["erp_sync_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_transfers_erp_sync_status", "inventory_transfers")
    op.drop_index("ix_inventory_transfers_erpnext_stock_entry_id", "inventory_transfers")
    op.drop_column("inventory_transfers", "erp_last_synced_at")
    op.drop_column("inventory_transfers", "erp_sync_error")
    op.drop_column("inventory_transfers", "erp_sync_status")
    op.drop_column("inventory_transfers", "erpnext_stock_entry_id")
    op.drop_index("ix_quotes_erp_sync_status", "quotes")
    op.drop_index("ix_quotes_erpnext_quotation_id", "quotes")
    op.drop_column("quotes", "erp_last_synced_at")
    op.drop_column("quotes", "erp_sync_error")
    op.drop_column("quotes", "erp_sync_status")
    op.drop_column("quotes", "erpnext_quotation_id")
