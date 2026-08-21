"""Add configurable document templates, immutable versions and render history.

Revision ID: 0010_document_template_center
Revises: 0009_prequotes_by_vehicle
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0010_document_template_center"
down_revision: str | None = "0009_prequotes_by_vehicle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="CASCADE")),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("published_version", sa.Integer()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_document_template_org_code"),
    )
    op.create_index("ix_document_templates_organization_id", "document_templates", ["organization_id"])
    op.create_index("ix_document_templates_branch_id", "document_templates", ["branch_id"])
    op.create_index("ix_document_templates_document_type", "document_templates", ["document_type"])
    op.create_index("ix_document_templates_status", "document_templates", ["status"])
    op.create_index("ix_document_template_scope_type", "document_templates", ["organization_id", "branch_id", "document_type"])

    op.create_table(
        "document_template_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("document_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("paper_size", sa.String(20), nullable=False, server_default="LETTER"),
        sa.Column("html_template", sa.Text(), nullable=False),
        sa.Column("css_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("variables_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("change_note", sa.String(500)),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("template_id", "version", name="uq_document_template_version"),
    )
    op.create_index("ix_document_template_versions_template_id", "document_template_versions", ["template_id"])
    op.create_index("ix_document_template_versions_status", "document_template_versions", ["status"])
    op.create_index("ix_document_template_versions_created_at", "document_template_versions", ["created_at"])
    op.create_index("ix_document_template_versions_published_at", "document_template_versions", ["published_at"])
    op.create_index("ix_document_template_version_status", "document_template_versions", ["template_id", "status"])

    op.create_table(
        "document_renders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False, server_default="SMARTDIAG504"),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("branches.id", ondelete="SET NULL")),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("document_templates.id", ondelete="SET NULL")),
        sa.Column("template_version_id", sa.String(36), sa.ForeignKey("document_template_versions.id", ondelete="SET NULL")),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("business_reference", sa.String(180), nullable=False),
        sa.Column("html_snapshot", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ["organization_id", "branch_id", "template_id", "template_version_id", "document_type", "business_reference", "content_sha256", "created_at"]:
        op.create_index(f"ix_document_renders_{column}", "document_renders", [column])
    op.create_index("ix_document_render_reference_created", "document_renders", ["business_reference", "created_at"])
    op.create_index("ix_document_render_type_created", "document_renders", ["document_type", "created_at"])


def downgrade() -> None:
    op.drop_table("document_renders")
    op.drop_table("document_template_versions")
    op.drop_table("document_templates")
