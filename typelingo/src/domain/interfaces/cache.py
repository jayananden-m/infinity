from abc import ABC, abstractmethod

from src.domain.models.passage import Passage


class IPassageCache(ABC):
    @abstractmethod
    async def get(self, cache_key: str) -> Passage | None: ...

    @abstractmethod
    async def set(self, cache_key: str, passage: Passage, ttl_seconds: int = 86400) -> None: ...
