"""Add token-protected public chatbot sessions and messages.

Revision ID: 0002_chatbot
Revises: 0001_initial
Create Date: 2026-08-12
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_chatbot"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("page_url", sa.String(1000)),
        sa.Column("referrer", sa.String(1000)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("accepted_privacy_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_hash", sa.String(64)),
        sa.Column("user_agent_hash", sa.String(64)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rate_window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rate_window_count", sa.Integer(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_sessions_token_hash", "chat_sessions", ["token_hash"], unique=True)
    op.create_index("ix_chat_sessions_status", "chat_sessions", ["status"])
    op.create_index("ix_chat_sessions_expires_at", "chat_sessions", ["expires_at"])
    op.create_index("ix_chat_sessions_last_message_at", "chat_sessions", ["last_message_at"])
    op.create_index("ix_chat_sessions_ip_hash", "chat_sessions", ["ip_hash"])
    op.create_index("ix_chat_sessions_status_expires", "chat_sessions", ["status", "expires_at"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("client_message_id", sa.String(128)),
        sa.Column(
            "reply_to_message_id",
            sa.String(36),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
        ),
        sa.Column("provider", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("mode", sa.String(40)),
        sa.Column("audit_id", sa.String(80)),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("suggested_actions", sa.JSON(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", "client_message_id", name="uq_chat_message_client_id"),
        sa.UniqueConstraint("reply_to_message_id", name="uq_chat_message_reply"),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_reply_to_message_id", "chat_messages", ["reply_to_message_id"])
    op.create_index("ix_chat_messages_audit_id", "chat_messages", ["audit_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("ix_chat_messages_session_created", "chat_messages", ["session_id", "created_at"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
