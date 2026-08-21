"""Add legal birth date required by ERPNext Employee.

Revision ID: 0023_employee_birth_date
Revises: 0022_enterprise_modules
"""

from alembic import op
import sqlalchemy as sa

revision = "0023_employee_birth_date"
down_revision = "0022_enterprise_modules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employee_contracts", sa.Column("date_of_birth", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("employee_contracts", "date_of_birth")
