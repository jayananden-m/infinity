import json
from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio import Redis

from src.domain.interfaces.cache import IPassageCache
from src.domain.models.passage import DifficultyVector, Passage, PassageSource


class RedisPassageCache(IPassageCache):
    def __init__(self, redis_url: str) -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)

    async def get(self, cache_key: str) -> Passage | None:
        raw = await self._redis.get(cache_key)
        if raw is None:
            return None
        return _deserialize(raw)

    async def set(self, cache_key: str, passage: Passage, ttl_seconds: int = 86400) -> None:
        await self._redis.set(cache_key, _serialize(passage), ex=ttl_seconds)

    async def close(self) -> None:
        await self._redis.aclose()


def _serialize(passage: Passage) -> str:
    return json.dumps(
        {
            "id": str(passage.id),
            "content": passage.content,
            "difficulty": passage.difficulty.to_dict(),
            "grammar_tags": list(passage.grammar_tags),
            "word_count": passage.word_count,
            "source": passage.source.value,
            "created_at": passage.created_at.isoformat(),
        }
    )


def _deserialize(raw: str) -> Passage:
    data = json.loads(raw)
    return Passage(
        id=UUID(data["id"]),
        content=data["content"],
        difficulty=DifficultyVector.from_dict(data["difficulty"]),
        grammar_tags=tuple(data["grammar_tags"]),
        word_count=data["word_count"],
        source=PassageSource(data["source"]),
        created_at=datetime.fromisoformat(data["created_at"]).replace(tzinfo=UTC),
    )
