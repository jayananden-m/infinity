"""Fixtures for E2E tests.

Requires live Postgres (DATABASE_URL) — same as integration tests.
Run: pytest tests/e2e/ -v -m e2e
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config
from src.config import settings
from src.domain.models.passage import (
    CognitiveTarget,
    DifficultyVector,
    MotorTarget,
    Passage,
    PassageSource,
)
from src.infrastructure.database.repositories.passage_repository import (
    PostgresPassageRepository,
)
from src.main import create_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session", autouse=True)
async def _seed_passage() -> None:
    """Ensure at least one passage exists so start_session doesn't 503."""
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session, session.begin():
        repo = PostgresPassageRepository(session)
        passage = Passage(
            id=uuid4(),
            content="The quick brown fox jumps over the lazy dog every single day.",
            difficulty=DifficultyVector(
                motor=MotorTarget(
                    target_wpm=35.0,
                    key_focus=("t", "h"),
                    bigram_focus=("th",),
                    word_length_avg=4.0,
                ),
                cognitive=CognitiveTarget(
                    grammar_level=1,
                    vocabulary_tier=1,
                    grammar_targets=("present_simple",),
                    sentence_complexity=0.3,
                ),
            ),
            grammar_tags=("present_simple",),
            word_count=12,
            source=PassageSource.SEED,
            created_at=datetime.now(UTC),
        )
        await repo.save(passage)
    await engine.dispose()
