"""Accounts, sessions, saved chats, feedback, app settings and the admin activity log

Revision ID: d566b5bd752c
Revises:
Create Date: 2026-11-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d566b5bd752c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Times are stored in UTC. mrag.db.UtcDateTime adds the time zone back when SQLite reads them.
# Migrations use the plain column type, so they never depend on the current app code
UTC_TIME = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_app_settings")),
    )
    op.create_table(
        "guest_daily",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("messages", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("day", name=op.f("pk_guest_daily")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("created_at", UTC_TIME, nullable=False),
        sa.Column("last_login_at", UTC_TIME, nullable=True),
        sa.CheckConstraint("role IN ('member', 'admin')", name=op.f("ck_users_role")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("admin_label", sa.String(length=254), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=254), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", UTC_TIME, nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
            name=op.f("fk_audit_log_admin_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_index(op.f("ix_audit_log_created_at"), "audit_log", ["created_at"], unique=False)
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.Column("created_at", UTC_TIME, nullable=False),
        sa.CheckConstraint("kind IN ('problem', 'idea', 'other')", name=op.f("ck_feedback_kind")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_feedback_user_id_users"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
    )
    op.create_index(op.f("ix_feedback_user_id"), "feedback", ["user_id"], unique=False)
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("csrf_token", sa.String(length=64), nullable=False),
        sa.Column("remember", sa.Boolean(), nullable=False),
        sa.Column("guest_messages", sa.Integer(), nullable=False),
        sa.Column("created_at", UTC_TIME, nullable=False),
        sa.Column("last_seen_at", UTC_TIME, nullable=False),
        sa.Column("expires_at", UTC_TIME, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")),
    )
    op.create_index(op.f("ix_sessions_expires_at"), "sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.create_table(
        "chats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("created_at", UTC_TIME, nullable=False),
        sa.Column("updated_at", UTC_TIME, nullable=False),
        sa.CheckConstraint(
            "(user_id IS NULL) <> (session_id IS NULL)", name=op.f("ck_chats_one_owner")
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_chats_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_chats_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chats")),
    )
    op.create_index(op.f("ix_chats_session_id"), "chats", ["session_id"], unique=False)
    op.create_index("ix_chats_user_id_updated_at", "chats", ["user_id", "updated_at"], unique=False)
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("created_at", UTC_TIME, nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name=op.f("ck_messages_role")),
        sa.CheckConstraint(
            "status IN ('done', 'stopped', 'failed')", name=op.f("ck_messages_status")
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"], ["chats.id"], name=op.f("fk_messages_chat_id_chats"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_chat_id"), "messages", ["chat_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_chat_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_chats_user_id_updated_at", table_name="chats")
    op.drop_index(op.f("ix_chats_session_id"), table_name="chats")
    op.drop_table("chats")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_feedback_user_id"), table_name="feedback")
    op.drop_table("feedback")
    op.drop_index(op.f("ix_audit_log_created_at"), table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("users")
    op.drop_table("guest_daily")
    op.drop_table("app_settings")
