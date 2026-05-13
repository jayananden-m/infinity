from uuid import uuid4

import pytest

from src.domain.models.passage import Passage, PassageSource
from src.domain.models.session import KeystrokeEvent, SessionMetrics, TypingSession
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile, User
from tests.fakes.repositories import (
    InMemoryCognitiveSkillRepository,
    InMemoryMotorSkillRepository,
    InMemoryPassageRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
)

# Helpers reused from other test modules to avoid duplication
from tests.unit.domain.test_passage import make_vector


def make_user() -> User:
    return User.create("test@example.com", "Tester", "hashed_pw")


def make_metrics() -> SessionMetrics:
    return SessionMetrics(wpm=50.0, accuracy=0.95, duration_seconds=60.0, per_key_stats={})


def make_keystrokes() -> tuple[KeystrokeEvent, ...]:
    return (KeystrokeEvent(key="a", timestamp_ms=0, correct=True),)


class TestInMemoryUserRepository:
    @pytest.mark.asyncio()
    async def test_save_and_get_by_id(self):
        repo = InMemoryUserRepository()
        user = make_user()
        await repo.save(user)
        assert await repo.get_by_id(user.id) == user

    @pytest.mark.asyncio()
    async def test_get_by_id_returns_none_when_missing(self):
        repo = InMemoryUserRepository()
        assert await repo.get_by_id(uuid4()) is None

    @pytest.mark.asyncio()
    async def test_get_by_email(self):
        repo = InMemoryUserRepository()
        user = make_user()
        await repo.save(user)
        assert await repo.get_by_email(user.email) == user

    @pytest.mark.asyncio()
    async def test_get_by_email_returns_none_when_missing(self):
        repo = InMemoryUserRepository()
        assert await repo.get_by_email("nobody@example.com") is None

    @pytest.mark.asyncio()
    async def test_save_overwrites_existing(self):
        repo = InMemoryUserRepository()
        user = make_user()
        await repo.save(user)
        await repo.save(user)
        assert await repo.get_by_id(user.id) == user


class TestInMemoryMotorSkillRepository:
    @pytest.mark.asyncio()
    async def test_save_and_get_by_user(self):
        repo = InMemoryMotorSkillRepository()
        profile = MotorSkillProfile.initial(uuid4())
        await repo.save(profile)
        assert await repo.get_by_user(profile.user_id) == profile

    @pytest.mark.asyncio()
    async def test_get_by_user_returns_none_when_missing(self):
        repo = InMemoryMotorSkillRepository()
        assert await repo.get_by_user(uuid4()) is None


class TestInMemoryCognitiveSkillRepository:
    @pytest.mark.asyncio()
    async def test_save_and_get_by_user(self):
        repo = InMemoryCognitiveSkillRepository()
        profile = CognitiveSkillProfile.initial(uuid4())
        await repo.save(profile)
        assert await repo.get_by_user(profile.user_id) == profile

    @pytest.mark.asyncio()
    async def test_get_by_user_returns_none_when_missing(self):
        repo = InMemoryCognitiveSkillRepository()
        assert await repo.get_by_user(uuid4()) is None


class TestInMemoryPassageRepository:
    @pytest.mark.asyncio()
    async def test_save_and_get_by_id(self):
        repo = InMemoryPassageRepository()
        p = Passage.create("hello world", make_vector(), ("present_simple",), PassageSource.SEED)
        await repo.save(p)
        assert await repo.get_by_id(p.id) == p

    @pytest.mark.asyncio()
    async def test_get_by_id_returns_none_when_missing(self):
        repo = InMemoryPassageRepository()
        assert await repo.get_by_id(uuid4()) is None

    @pytest.mark.asyncio()
    async def test_find_by_difficulty_respects_limit(self):
        repo = InMemoryPassageRepository()
        for i in range(5):
            p = Passage.create(f"passage {i}", make_vector(), (), PassageSource.SEED)
            await repo.save(p)
        results = await repo.find_by_difficulty(make_vector(), limit=3)
        assert len(results) == 3


class TestInMemorySessionRepository:
    @pytest.mark.asyncio()
    async def test_save_and_get_by_id(self):
        repo = InMemorySessionRepository()
        session = TypingSession.start(uuid4(), uuid4())
        await repo.save(session)
        assert await repo.get_by_id(session.id) == session

    @pytest.mark.asyncio()
    async def test_get_by_id_returns_none_when_missing(self):
        repo = InMemorySessionRepository()
        assert await repo.get_by_id(uuid4()) is None

    @pytest.mark.asyncio()
    async def test_get_recent_by_user_filters_by_user(self):
        repo = InMemorySessionRepository()
        user_a = uuid4()
        user_b = uuid4()
        passage = uuid4()
        s1 = TypingSession.start(user_a, passage)
        s2 = TypingSession.start(user_b, passage)
        await repo.save(s1)
        await repo.save(s2)
        results = await repo.get_recent_by_user(user_a)
        assert len(results) == 1
        assert results[0].id == s1.id

    @pytest.mark.asyncio()
    async def test_get_recent_by_user_respects_limit(self):
        repo = InMemorySessionRepository()
        user_id = uuid4()
        passage = uuid4()
        for _ in range(5):
            await repo.save(TypingSession.start(user_id, passage))
        results = await repo.get_recent_by_user(user_id, limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio()
    async def test_save_updates_existing_session(self):
        repo = InMemorySessionRepository()
        session = TypingSession.start(uuid4(), uuid4())
        await repo.save(session)
        completed = session.complete(make_keystrokes(), make_metrics())
        await repo.save(completed)
        stored = await repo.get_by_id(session.id)
        assert stored is not None
        assert stored.status == completed.status
