"""Require branch ownership for operational transactions.

Revision ID: 0030_require_transaction_branch
Revises: 0029_transaction_branch_scope
"""

from alembic import op
import sqlalchemy as sa


revision = "0030_require_transaction_branch"
down_revision = "0029_transaction_branch_scope"
branch_labels = None
depends_on = None


TABLES = (
    "bookings",
    "store_orders",
    "work_orders",
    "quotes",
    "cash_sessions",
    "payments",
    "purchase_orders",
    "employee_contracts",
    "used_vehicles",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            sa.text(
                f"""
                UPDATE {table} AS target
                SET branch_id = (
                    SELECT branches.id
                    FROM branches
                    WHERE branches.organization_id = target.organization_id
                    ORDER BY branches.active DESC, (branches.code = 'MAIN') DESC,
                             branches.created_at ASC, branches.id ASC
                    LIMIT 1
                )
                WHERE target.branch_id IS NULL
                """
            )
        )
        op.alter_column(
            table,
            "branch_id",
            existing_type=sa.String(36),
            nullable=False,
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.alter_column(
            table,
            "branch_id",
            existing_type=sa.String(36),
            nullable=True,
        )
