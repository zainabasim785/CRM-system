"""Initial schema: users, appointments, conversations, interaction_logs, reminders.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-07-14 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: enums are created explicitly in upgrade(); without this,
# SQLAlchemy also emits CREATE TYPE during create_table and the migration fails.
user_role = postgresql.ENUM(
    "admin",
    "receptionist",
    "customer",
    name="user_role",
    create_type=False,
)
appointment_status = postgresql.ENUM(
    "scheduled",
    "cancelled",
    "completed",
    "rescheduled",
    name="appointment_status",
    create_type=False,
)
conversation_status = postgresql.ENUM(
    "active",
    "closed",
    "escalated",
    name="conversation_status",
    create_type=False,
)
interaction_role = postgresql.ENUM(
    "user",
    "assistant",
    "system",
    "agent",
    name="interaction_role",
    create_type=False,
)
reminder_channel = postgresql.ENUM(
    "internal",
    "email",
    "sms",
    name="reminder_channel",
    create_type=False,
)
reminder_status = postgresql.ENUM(
    "scheduled",
    "sent",
    "cancelled",
    "failed",
    name="reminder_status",
    create_type=False,
)


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    appointment_status.create(op.get_bind(), checkfirst=True)
    conversation_status.create(op.get_bind(), checkfirst=True)
    interaction_role.create(op.get_bind(), checkfirst=True)
    reminder_channel.create(op.get_bind(), checkfirst=True)
    reminder_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column(
            "role",
            user_role,
            server_default="customer",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_created_at", "users", ["created_at"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_phone", "users", ["phone"], unique=False)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("google_event_id", sa.String(length=255), nullable=True),
        sa.Column("calendar_id", sa.String(length=255), server_default="primary", nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attendee_email", sa.String(length=320), nullable=True),
        sa.Column("attendee_name", sa.String(length=255), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            appointment_status,
            server_default="scheduled",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_event_id"),
    )
    op.create_index(
        "ix_appointments_attendee_email",
        "appointments",
        ["attendee_email"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_created_at",
        "appointments",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_google_event_id",
        "appointments",
        ["google_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_starts_at",
        "appointments",
        ["starts_at"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_starts_at_status",
        "appointments",
        ["starts_at", "status"],
        unique=False,
    )
    op.create_index("ix_appointments_status", "appointments", ["status"], unique=False)
    op.create_index("ix_appointments_user_id", "appointments", ["user_id"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "status",
            conversation_status,
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "extra_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index(
        "ix_conversations_created_at",
        "conversations",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_session_id",
        "conversations",
        ["session_id"],
        unique=False,
    )
    op.create_index("ix_conversations_status", "conversations", ["status"], unique=False)
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"], unique=False)

    op.create_table(
        "interaction_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", interaction_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("agent_name", sa.String(length=64), nullable=True),
        sa.Column(
            "extra_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interaction_logs_conversation_created",
        "interaction_logs",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interaction_logs_conversation_id",
        "interaction_logs",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_interaction_logs_created_at",
        "interaction_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interaction_logs_intent",
        "interaction_logs",
        ["intent"],
        unique=False,
    )
    op.create_index(
        "ix_interaction_logs_role",
        "interaction_logs",
        ["role"],
        unique=False,
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("appointment_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column(
            "channel",
            reminder_channel,
            server_default="internal",
            nullable=False,
        ),
        sa.Column(
            "status",
            reminder_status,
            server_default="scheduled",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reminders_appointment_id",
        "reminders",
        ["appointment_id"],
        unique=False,
    )
    op.create_index(
        "ix_reminders_conversation_id",
        "reminders",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_reminders_created_at",
        "reminders",
        ["created_at"],
        unique=False,
    )
    op.create_index("ix_reminders_remind_at", "reminders", ["remind_at"], unique=False)
    op.create_index(
        "ix_reminders_remind_at_status",
        "reminders",
        ["remind_at", "status"],
        unique=False,
    )
    op.create_index("ix_reminders_status", "reminders", ["status"], unique=False)
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reminders_user_id", table_name="reminders")
    op.drop_index("ix_reminders_status", table_name="reminders")
    op.drop_index("ix_reminders_remind_at_status", table_name="reminders")
    op.drop_index("ix_reminders_remind_at", table_name="reminders")
    op.drop_index("ix_reminders_created_at", table_name="reminders")
    op.drop_index("ix_reminders_conversation_id", table_name="reminders")
    op.drop_index("ix_reminders_appointment_id", table_name="reminders")
    op.drop_table("reminders")

    op.drop_index("ix_interaction_logs_role", table_name="interaction_logs")
    op.drop_index("ix_interaction_logs_intent", table_name="interaction_logs")
    op.drop_index("ix_interaction_logs_created_at", table_name="interaction_logs")
    op.drop_index("ix_interaction_logs_conversation_id", table_name="interaction_logs")
    op.drop_index("ix_interaction_logs_conversation_created", table_name="interaction_logs")
    op.drop_table("interaction_logs")

    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_index("ix_conversations_status", table_name="conversations")
    op.drop_index("ix_conversations_session_id", table_name="conversations")
    op.drop_index("ix_conversations_created_at", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_appointments_user_id", table_name="appointments")
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_starts_at_status", table_name="appointments")
    op.drop_index("ix_appointments_starts_at", table_name="appointments")
    op.drop_index("ix_appointments_google_event_id", table_name="appointments")
    op.drop_index("ix_appointments_created_at", table_name="appointments")
    op.drop_index("ix_appointments_attendee_email", table_name="appointments")
    op.drop_table("appointments")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_table("users")

    reminder_status.drop(op.get_bind(), checkfirst=True)
    reminder_channel.drop(op.get_bind(), checkfirst=True)
    interaction_role.drop(op.get_bind(), checkfirst=True)
    conversation_status.drop(op.get_bind(), checkfirst=True)
    appointment_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
