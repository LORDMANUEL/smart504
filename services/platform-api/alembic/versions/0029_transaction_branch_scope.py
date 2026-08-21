"""Add branch ownership to operational transactions.

Revision ID: 0029_transaction_branch_scope
Revises: 0028_client_identity
"""

from alembic import op
import sqlalchemy as sa


revision = "0029_transaction_branch_scope"
down_revision = "0028_client_identity"
branch_labels = None
depends_on = None


TABLES = ("bookings", "work_orders", "quotes", "cash_sessions", "payments")
EXISTING_BRANCH_TABLES = (
    "store_orders",
    "purchase_orders",
    "employee_contracts",
    "used_vehicles",
    "document_renders",
)


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("branch_id", sa.String(36), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_branch_id",
            table,
            "branches",
            ["branch_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table}_branch_id", table, ["branch_id"])

    # Existing demo records belong to the first active branch of their own
    # organization. Organizations without a branch remain explicit NULL and
    # must be configured before branch-scoped staff can operate them.
    for table in (*TABLES, *EXISTING_BRANCH_TABLES):
        op.execute(
            sa.text(
                f"""
                UPDATE {table} AS target
                SET branch_id = (
                    SELECT branches.id
                    FROM branches
                    WHERE branches.organization_id = target.organization_id
                      AND branches.active IS TRUE
                    ORDER BY branches.created_at ASC, branches.id ASC
                    LIMIT 1
                )
                WHERE target.branch_id IS NULL
                """
            )
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_branch_id", table_name=table)
        op.drop_constraint(f"fk_{table}_branch_id", table, type_="foreignkey")
        op.drop_column(table, "branch_id")
