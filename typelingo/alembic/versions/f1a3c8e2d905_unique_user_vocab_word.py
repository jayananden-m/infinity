"""unique constraint on user_vocab(user_id, word)

Revision ID: f1a3c8e2d905
Revises: d4e91f2a7c03
Create Date: 2026-04-25 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f1a3c8e2d905"
down_revision: str | Sequence[str] | None = "d4e91f2a7c03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove duplicate rows, keeping the most recent practiced_at per (user_id, word)
    op.execute("""
        DELETE FROM user_vocab
        WHERE id NOT IN (
            SELECT DISTINCT ON (user_id, word) id
            FROM user_vocab
            ORDER BY user_id, word, practiced_at DESC
        )
    """)
    op.create_unique_constraint("uq_user_vocab_user_word", "user_vocab", ["user_id", "word"])


def downgrade() -> None:
    op.drop_constraint("uq_user_vocab_user_word", "user_vocab", type_="unique")
