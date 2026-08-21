"""Record distinct payroll review, approval and posting actors.

Revision ID: 0032_payroll_sod
Revises: 0031_client_credit_amount
"""

from alembic import op
import sqlalchemy as sa


revision = "0032_payroll_sod"
down_revision = "0031_client_credit_amount"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payroll_runs", sa.Column("reviewed_by", sa.String(length=120), nullable=True))
    op.add_column("payroll_runs", sa.Column("approved_by", sa.String(length=120), nullable=True))
    op.add_column("payroll_runs", sa.Column("posted_by", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("payroll_runs", "posted_by")
    op.drop_column("payroll_runs", "approved_by")
    op.drop_column("payroll_runs", "reviewed_by")
