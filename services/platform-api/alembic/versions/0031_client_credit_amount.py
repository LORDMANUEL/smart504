"""Persist the amount requested by a portal client.

Revision ID: 0031_client_credit_amount
Revises: 0030_require_transaction_branch
"""

from alembic import op
import sqlalchemy as sa


revision = "0031_client_credit_amount"
down_revision = "0030_require_transaction_branch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_users", sa.Column("requested_credit_amount", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("client_users", "requested_credit_amount")
