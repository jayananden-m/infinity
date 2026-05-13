"""add is_guest and guest_expires_at to users

Revision ID: a3b5c7d9e1f0
Revises: f1a3c8e2d905
Create Date: 2026-05-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a3b5c7d9e1f0"
down_revision: str | Sequence[str] | None = "f1a3c8e2d905"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_guest", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("guest_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Index to make the cleanup query fast
    op.create_index(
        "ix_users_guest_expires_at",
        "users",
        ["guest_expires_at"],
        postgresql_where=sa.text("is_guest = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_guest_expires_at", "users")
    op.drop_column("users", "guest_expires_at")
    op.drop_column("users", "is_guest")
