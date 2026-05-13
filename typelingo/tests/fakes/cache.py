from src.domain.interfaces.cache import IPassageCache
from src.domain.models.passage import Passage


class InMemoryPassageCache(IPassageCache):
    def __init__(self) -> None:
        self._store: dict[str, Passage] = {}

    async def get(self, cache_key: str) -> Passage | None:
        return self._store.get(cache_key)

    async def set(self, cache_key: str, passage: Passage, ttl_seconds: int = 86400) -> None:
        self._store[cache_key] = passage
