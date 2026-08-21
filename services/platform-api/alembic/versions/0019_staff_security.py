"""Add staff lockout, TOTP MFA and session revocation state.

Revision ID: 0019_staff_security
Revises: 0018_tenant_unique_keys
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_staff_security"
down_revision = "0018_tenant_unique_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("staff_users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("staff_users", sa.Column("locked_until", sa.DateTime(timezone=True)))
    op.add_column("staff_users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("staff_users", sa.Column("mfa_secret_encrypted", sa.String(500)))
    op.add_column("staff_users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_staff_users_locked_until", "staff_users", ["locked_until"])


def downgrade() -> None:
    op.drop_index("ix_staff_users_locked_until", table_name="staff_users")
    op.drop_column("staff_users", "session_version")
    op.drop_column("staff_users", "mfa_secret_encrypted")
    op.drop_column("staff_users", "mfa_enabled")
    op.drop_column("staff_users", "locked_until")
    op.drop_column("staff_users", "failed_login_attempts")
