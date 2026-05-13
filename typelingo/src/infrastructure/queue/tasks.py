import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.domain.models.passage import DifficultyVector
from src.domain.services.circuit_breaker import CircuitBreaker, CircuitOpenError
from src.infrastructure.cache.redis_cache import RedisPassageCache
from src.infrastructure.cache.vocab_cache import RedisVocabCache
from src.infrastructure.database.repositories.passage_repository import (
    PostgresPassageRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresUserRepository,
)
from src.infrastructure.llm.groq_client import (
    generate_assess_questions,
    generate_passage,
    generate_vocab_batch,
)
from src.infrastructure.queue.celery_app import celery_app
from src.observability.logging import get_logger

_log = get_logger(__name__)

_circuit_breaker = CircuitBreaker()


@celery_app.task(max_retries=2, default_retry_delay=30)  # type: ignore[misc]
def generate_passage_task(
    difficulty_dict: dict[str, Any],
    grammar_tags: list[str],
) -> None:
    vector = DifficultyVector.from_dict(difficulty_dict)

    async def _run() -> None:
        try:
            passage = await _circuit_breaker.call(lambda: generate_passage(vector, tuple(grammar_tags)))
        except (CircuitOpenError, Exception):
            return

        engine = create_async_engine(settings.database_url)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session, session.begin():
            await PostgresPassageRepository(session).save(passage)
        await engine.dispose()

        cache = RedisPassageCache(settings.redis_url)
        await cache.set(vector.quantize().cache_key(), passage)
        await cache.close()

    asyncio.run(_run())


@celery_app.task(max_retries=2, default_retry_delay=60)  # type: ignore[misc]
def generate_vocab_task(level: str, batch_size: int = 5) -> None:
    if not settings.groq_api_key:
        return

    async def _run() -> None:
        try:
            words = await generate_vocab_batch(level, n=batch_size)
        except Exception:
            return
        cache = RedisVocabCache(settings.redis_url)
        await cache.push_vocab_words(level, words)
        await cache.close()

    asyncio.run(_run())


@celery_app.task(max_retries=2, default_retry_delay=60)  # type: ignore[misc]
def generate_assess_questions_task(level: str) -> None:
    if not settings.groq_api_key:
        return

    async def _run() -> None:
        try:
            questions = await generate_assess_questions(level, n=2)
        except Exception:
            return
        cache = RedisVocabCache(settings.redis_url)
        await cache.set_assess_questions(level, questions)
        await cache.close()

    asyncio.run(_run())


@celery_app.task  # type: ignore[misc]
def cleanup_expired_guests_task() -> None:
    """Delete guest accounts whose TTL has elapsed (runs daily via beat)."""

    async def _run() -> None:
        engine = create_async_engine(settings.database_url)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session, session.begin():
            deleted = await PostgresUserRepository(session).delete_expired_guests()
        await engine.dispose()
        _log.info("guests.cleaned_up", deleted=deleted)

    asyncio.run(_run())
