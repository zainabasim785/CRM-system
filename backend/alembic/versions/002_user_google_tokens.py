"""Add per-user Google Calendar OAuth token columns.

Revision ID: 002_user_google_tokens
Revises: 001_initial_schema
Create Date: 2026-07-17 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_user_google_tokens"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_access_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_refresh_token", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("google_token_expiry", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "google_token_expiry")
    op.drop_column("users", "google_refresh_token")
    op.drop_column("users", "google_access_token")
