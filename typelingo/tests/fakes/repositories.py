from uuid import UUID

from src.domain.interfaces.repositories import (
    ICognitiveSkillRepository,
    IMotorSkillRepository,
    IPassageRepository,
    ISessionRepository,
    IUserRepository,
)
from src.domain.models.passage import DifficultyVector, Passage
from src.domain.models.session import TypingSession
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile, User


class InMemoryUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email), None)

    async def save(self, user: User) -> None:
        self._store[user.id] = user


class InMemoryMotorSkillRepository(IMotorSkillRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, MotorSkillProfile] = {}

    async def get_by_user(self, user_id: UUID) -> MotorSkillProfile | None:
        return self._store.get(user_id)

    async def save(self, profile: MotorSkillProfile) -> None:
        self._store[profile.user_id] = profile


class InMemoryCognitiveSkillRepository(ICognitiveSkillRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, CognitiveSkillProfile] = {}

    async def get_by_user(self, user_id: UUID) -> CognitiveSkillProfile | None:
        return self._store.get(user_id)

    async def save(self, profile: CognitiveSkillProfile) -> None:
        self._store[profile.user_id] = profile


class InMemoryPassageRepository(IPassageRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Passage] = {}

    async def get_by_id(self, passage_id: UUID) -> Passage | None:
        return self._store.get(passage_id)

    async def find_by_difficulty(self, vector: DifficultyVector, limit: int = 5) -> list[Passage]:
        # In tests, return all passages — difficulty matching is an infra concern
        return list(self._store.values())[:limit]

    async def save(self, passage: Passage) -> None:
        self._store[passage.id] = passage


class InMemorySessionRepository(ISessionRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, TypingSession] = {}

    async def get_by_id(self, session_id: UUID) -> TypingSession | None:
        return self._store.get(session_id)

    async def get_recent_by_user(self, user_id: UUID, limit: int = 10) -> list[TypingSession]:
        user_sessions = [s for s in self._store.values() if s.user_id == user_id]
        return sorted(user_sessions, key=lambda s: s.started_at, reverse=True)[:limit]

    async def save(self, session: TypingSession) -> None:
        self._store[session.id] = session
