"""add cefr_level to cognitive_skill_profiles

Revision ID: c7f3d8a1b9e2
Revises: 50360f5b74f0
Create Date: 2026-04-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7f3d8a1b9e2"
down_revision: str | None = "50360f5b74f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cognitive_skill_profiles",
        sa.Column(
            "cefr_level",
            sa.String(2),
            nullable=False,
            server_default="A1",
        ),
    )


def downgrade() -> None:
    op.drop_column("cognitive_skill_profiles", "cefr_level")
