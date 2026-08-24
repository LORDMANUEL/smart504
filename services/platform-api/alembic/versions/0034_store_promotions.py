"""Persist verified store discounts.

Revision ID: 0034_store_promotions
Revises: 0033_client_self_registration
"""

from alembic import op
import sqlalchemy as sa

revision = "0034_store_promotions"
down_revision = "0033_client_self_registration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("store_orders", sa.Column("discount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("store_orders", sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("store_orders", sa.Column("promo_code", sa.String(40), nullable=True))
    op.execute("UPDATE store_orders SET total = subtotal")
    op.create_index("ix_store_orders_promo_code", "store_orders", ["promo_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_store_orders_promo_code", table_name="store_orders")
    op.drop_column("store_orders", "promo_code")
    op.drop_column("store_orders", "total")
    op.drop_column("store_orders", "discount")
