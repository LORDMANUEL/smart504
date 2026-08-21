"""Persistent tenant-scoped client identity.

Revision ID: 0028_client_identity
Revises: 0027_labor_catalog
"""

from alembic import op
import sqlalchemy as sa

revision = "0028_client_identity"
down_revision = "0027_labor_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("customer_id", sa.String(36), nullable=False),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mfa_secret_encrypted", sa.String(500)),
        sa.Column("session_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("loyalty_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("loyalty_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credit_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("credit_status", sa.String(30), nullable=False, server_default="NO_SOLICITADO"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("organization_id", "customer_id", name="uq_client_user_org_customer"),
        sa.UniqueConstraint("organization_id", "username", name="uq_client_user_org_username"),
    )
    op.create_index("ix_client_users_email", "client_users", ["email"], unique=True)
    op.create_index("ix_client_users_organization_id", "client_users", ["organization_id"])
    op.create_index("ix_client_users_customer_id", "client_users", ["customer_id"])
    op.create_index("ix_client_users_locked_until", "client_users", ["locked_until"])
    op.create_index("ix_client_users_last_login_at", "client_users", ["last_login_at"])
    op.create_index("ix_client_user_org_active", "client_users", ["organization_id", "is_active"])


def downgrade() -> None:
    op.drop_table("client_users")
