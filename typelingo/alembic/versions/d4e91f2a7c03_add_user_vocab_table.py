"""add user_vocab table

Revision ID: d4e91f2a7c03
Revises: c7f3d8a1b9e2
Create Date: 2026-04-25 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4e91f2a7c03"
down_revision: str | Sequence[str] | None = "c7f3d8a1b9e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_vocab",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("word", sa.String(length=100), nullable=False),
        sa.Column("cefr_level", sa.String(length=2), nullable=False),
        sa.Column("pos", sa.String(length=50), server_default="", nullable=False),
        sa.Column("practiced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_vocab_user_id", "user_vocab", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_vocab_user_id", table_name="user_vocab")
    op.drop_table("user_vocab")
