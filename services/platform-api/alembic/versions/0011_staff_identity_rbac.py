"""Add staff identities, RBAC attributes and access audit trail.

Revision ID: 0011_staff_identity_rbac
Revises: 0010_document_template_center
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_staff_identity_rbac"
down_revision: str | None = "0010_document_template_center"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("organization_id", sa.String(length=60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("employee_code", sa.String(length=40), nullable=False),
        sa.Column("full_name", sa.String(length=180), nullable=False),
        sa.Column("job_title", sa.String(length=120), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="TECHNICIAN"),
        sa.Column("permissions_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("organization_id", "employee_code", name="uq_staff_org_employee_code"),
    )
    op.create_index("ix_staff_users_email", "staff_users", ["email"], unique=True)
    op.create_index("ix_staff_users_organization_id", "staff_users", ["organization_id"])
    op.create_index("ix_staff_users_branch_id", "staff_users", ["branch_id"])
    op.create_index("ix_staff_users_role", "staff_users", ["role"])
    op.create_index("ix_staff_users_last_login_at", "staff_users", ["last_login_at"])
    op.create_index("ix_staff_org_role_active", "staff_users", ["organization_id", "role", "is_active"])
    op.create_index("ix_staff_branch_active", "staff_users", ["branch_id", "is_active"])

    op.create_table(
        "staff_access_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.String(length=60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("detail", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["staff_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_access_events_user_id", "staff_access_events", ["user_id"])
    op.create_index("ix_staff_access_events_organization_id", "staff_access_events", ["organization_id"])
    op.create_index("ix_staff_access_events_created_at", "staff_access_events", ["created_at"])
    op.create_index("ix_staff_access_user_created", "staff_access_events", ["user_id", "created_at"])
    op.create_index("ix_staff_access_action_created", "staff_access_events", ["action", "created_at"])


def downgrade() -> None:
    op.drop_table("staff_access_events")
    op.drop_table("staff_users")
