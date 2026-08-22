"""Client self-registration and managed mailbox identity.

Revision ID: 0033_client_self_registration
Revises: 0032_payroll_separation_of_duties
"""

from alembic import op
import sqlalchemy as sa

revision = "0033_client_self_registration"
down_revision = "0032_payroll_separation_of_duties"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_users", sa.Column("notification_email", sa.String(320), nullable=True))
    op.add_column("client_users", sa.Column("managed_email", sa.String(320), nullable=True))
    op.add_column(
        "client_users",
        sa.Column("mailbox_status", sa.String(30), nullable=False, server_default="PENDING_CONFIGURATION"),
    )
    op.execute("UPDATE client_users SET notification_email = email WHERE notification_email IS NULL")
    op.alter_column("client_users", "notification_email", nullable=False)
    op.create_index("ix_client_users_managed_email", "client_users", ["managed_email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_client_users_managed_email", table_name="client_users")
    op.drop_column("client_users", "mailbox_status")
    op.drop_column("client_users", "managed_email")
    op.drop_column("client_users", "notification_email")
