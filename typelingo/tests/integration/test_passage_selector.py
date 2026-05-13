"""Integration tests: passage selector cache-aside against real Postgres + Redis."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.domain.models.passage import (
    CognitiveTarget,
    DifficultyVector,
    MotorTarget,
    Passage,
    PassageSource,
)
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.passage_selector import NoPassageAvailableError, select_passage
from src.infrastructure.cache.redis_cache import RedisPassageCache
from src.infrastructure.database.repositories.passage_repository import (
    PostgresPassageRepository,
)
from tests.fakes.repositories import (  # type: ignore[import-untyped]
    InMemoryPassageRepository,
)

_MOTOR = MotorSkillProfile(
    user_id=__import__("uuid").uuid4(),
    overall_wpm=30.0,
    overall_accuracy=0.90,
    key_profiles={},
    bigram_stats={},
)
_COGNITIVE = CognitiveSkillProfile(
    user_id=_MOTOR.user_id,
    grammar_level=1,
    vocabulary_tier=1,
    weak_areas=(),
    strong_areas=(),
)


@pytest.mark.integration()
async def test_select_passage_from_db(db_session: AsyncSession) -> None:
    """Passage is returned from Postgres when cache is empty."""
    repo = PostgresPassageRepository(db_session)

    # Seed one passage directly
    passage = Passage(
        id=uuid4(),
        content="Integration test passage content.",
        difficulty=DifficultyVector(
            motor=MotorTarget(target_wpm=30.0, key_focus=(), bigram_focus=(), word_length_avg=4.0),
            cognitive=CognitiveTarget(
                grammar_level=1,
                vocabulary_tier=1,
                grammar_targets=(),
                sentence_complexity=0.3,
            ),
        ),
        grammar_tags=("present_simple",),
        word_count=5,
        source=PassageSource.SEED,
        created_at=datetime.now(UTC),
    )
    await repo.save(passage)

    result = await select_passage(_MOTOR, _COGNITIVE, repo)
    assert result is not None
    assert isinstance(result.content, str)


@pytest.mark.integration()
async def test_select_passage_cache_hit() -> None:
    """Second call returns from Redis cache, not Postgres."""
    cache = RedisPassageCache(settings.redis_url)
    repo = InMemoryPassageRepository()

    passage = Passage(
        id=uuid4(),
        content="Cached passage.",
        difficulty=DifficultyVector(
            motor=MotorTarget(target_wpm=30.0, key_focus=(), bigram_focus=(), word_length_avg=4.0),
            cognitive=CognitiveTarget(
                grammar_level=1,
                vocabulary_tier=1,
                grammar_targets=(),
                sentence_complexity=0.3,
            ),
        ),
        grammar_tags=("present_simple",),
        word_count=2,
        source=PassageSource.SEED,
        created_at=datetime.now(UTC),
    )
    await repo.save(passage)

    # First call: DB hit, populates cache
    result1 = await select_passage(_MOTOR, _COGNITIVE, repo, cache=cache)
    assert result1.id == passage.id

    # Clear repo so second call must use cache
    repo._store.clear()  # type: ignore[attr-defined]

    # Second call: cache hit
    result2 = await select_passage(_MOTOR, _COGNITIVE, repo, cache=cache)
    assert result2.id == passage.id

    await cache.close()


@pytest.mark.integration()
async def test_select_passage_enqueues_when_empty() -> None:
    """NoPassageAvailableError is raised and enqueue callback is called when DB is empty."""
    repo = InMemoryPassageRepository()
    enqueued: list[object] = []

    with pytest.raises(NoPassageAvailableError):
        await select_passage(
            _MOTOR,
            _COGNITIVE,
            repo,
            enqueue_generation=enqueued.append,
        )

    assert len(enqueued) == 1
