from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.models.passage import DifficultyVector, Passage
from src.domain.models.session import TypingSession
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile, User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def delete_expired_guests(self) -> int: ...


class IMotorSkillRepository(ABC):
    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> MotorSkillProfile | None: ...

    @abstractmethod
    async def save(self, profile: MotorSkillProfile) -> None: ...


class ICognitiveSkillRepository(ABC):
    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> CognitiveSkillProfile | None: ...

    @abstractmethod
    async def save(self, profile: CognitiveSkillProfile) -> None: ...


class IPassageRepository(ABC):
    @abstractmethod
    async def get_by_id(self, passage_id: UUID) -> Passage | None: ...

    @abstractmethod
    async def find_by_difficulty(self, vector: DifficultyVector, limit: int = 5) -> list[Passage]: ...

    @abstractmethod
    async def save(self, passage: Passage) -> None: ...


class ISessionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> TypingSession | None: ...

    @abstractmethod
    async def get_recent_by_user(self, user_id: UUID, limit: int = 10) -> list[TypingSession]: ...

    @abstractmethod
    async def save(self, session: TypingSession) -> None: ...
