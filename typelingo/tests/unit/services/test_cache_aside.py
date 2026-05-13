from uuid import uuid4

import pytest

from src.domain.models.passage import Passage, PassageSource
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.passage_selector import (
    NoPassageAvailableError,
    _build_vector,
    select_passage,
)
from tests.fakes.cache import InMemoryPassageCache
from tests.fakes.repositories import InMemoryPassageRepository
from tests.unit.domain.test_passage import make_vector

_USER = uuid4()
_MOTOR = MotorSkillProfile.initial(_USER)
_COGNITIVE = CognitiveSkillProfile.initial(_USER)


class TestCacheAside:
    @pytest.mark.asyncio()
    async def test_returns_from_cache_when_present(self):
        cache = InMemoryPassageCache()
        repo = InMemoryPassageRepository()
        passage = Passage.create("cached passage", make_vector(), (), PassageSource.SEED)
        vector = _build_vector(_MOTOR, _COGNITIVE).quantize()
        await cache.set(vector.cache_key(), passage)

        result = await select_passage(_MOTOR, _COGNITIVE, repo, cache)
        assert result == passage

    @pytest.mark.asyncio()
    async def test_populates_cache_on_repo_hit(self):
        cache = InMemoryPassageCache()
        repo = InMemoryPassageRepository()
        passage = Passage.create("db passage", make_vector(), (), PassageSource.SEED)
        await repo.save(passage)

        result = await select_passage(_MOTOR, _COGNITIVE, repo, cache)
        assert result == passage
        v = _build_vector(_MOTOR, _COGNITIVE).quantize()
        cached = await cache.get(v.cache_key())
        assert cached == passage

    @pytest.mark.asyncio()
    async def test_raises_when_both_cache_and_repo_miss(self):
        cache = InMemoryPassageCache()
        repo = InMemoryPassageRepository()
        with pytest.raises(NoPassageAvailableError):
            await select_passage(_MOTOR, _COGNITIVE, repo, cache)

    @pytest.mark.asyncio()
    async def test_works_without_cache(self):
        repo = InMemoryPassageRepository()
        passage = Passage.create("no cache", make_vector(), (), PassageSource.SEED)
        await repo.save(passage)
        result = await select_passage(_MOTOR, _COGNITIVE, repo)
        assert result == passage

    @pytest.mark.asyncio()
    async def test_calls_enqueue_on_full_miss(self):
        cache = InMemoryPassageCache()
        repo = InMemoryPassageRepository()
        enqueued: list[object] = []

        with pytest.raises(NoPassageAvailableError):
            await select_passage(
                _MOTOR,
                _COGNITIVE,
                repo,
                cache,
                enqueue_generation=enqueued.append,
            )
        assert len(enqueued) == 1
