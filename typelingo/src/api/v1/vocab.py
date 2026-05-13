from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user_id, get_db
from src.config import settings
from src.domain.services.user_setup import initialise_user_profiles
from src.infrastructure.cache.vocab_cache import RedisVocabCache
from src.infrastructure.database.repositories.cognitive_skill_repository import (
    PostgresCognitiveSkillRepository,
)
from src.infrastructure.database.repositories.motor_skill_repository import (
    PostgresMotorSkillRepository,
)
from src.infrastructure.database.repositories.vocab_repository import (
    PostgresVocabRepository,
)
from src.infrastructure.llm.groq_client import generate_vocab_batch
from src.infrastructure.queue.tasks import generate_vocab_task

router = APIRouter(prefix="/vocab", tags=["vocab"])

_POOL_REFILL_THRESHOLD = 5


async def _is_real_word(word: str) -> bool:
    """Check Datamuse for an exact dictionary match. Fast (~50ms), no API key needed."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                "https://api.datamuse.com/words",
                params={"sp": word, "max": 1},
            )
            data: list[dict[str, Any]] = resp.json()
            return bool(data) and data[0].get("word", "").lower() == word.lower()
    except Exception:
        return True  # network error → don't block the user, let LLM decide


class VocabWordResponse(BaseModel):
    word: str
    cefr_level: str
    pos: str
    definition: str
    etymology: str
    register: str
    contrast_note: str
    memory_hook: str
    examples: list[str]
    sentence_stem: str
    sentence_answer: str


@router.get("/next", response_model=VocabWordResponse)
async def get_next_vocab_word(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    word: str | None = Query(None),
) -> VocabWordResponse:
    motor_repo = PostgresMotorSkillRepository(db)
    cognitive_repo = PostgresCognitiveSkillRepository(db)
    _, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)

    level = cognitive.cefr_level

    # On-demand lookup for a specific word
    if word:
        if not await _is_real_word(word):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"'{word}' is not a recognised English word — check the spelling",
            )
        if not settings.groq_api_key:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM not configured",
            )
        results = await generate_vocab_batch(level, n=1, target_word=word)
        if not results:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"'{word}' is not a recognised English word — check the spelling",
            )
        vocab_word = results[0]
        return VocabWordResponse(
            word=vocab_word.word,
            cefr_level=vocab_word.cefr_level,
            pos=vocab_word.pos,
            definition=vocab_word.definition,
            etymology=vocab_word.etymology,
            register=vocab_word.register,
            contrast_note=vocab_word.contrast_note,
            memory_hook=vocab_word.memory_hook,
            examples=list(vocab_word.examples),
            sentence_stem=vocab_word.sentence_stem,
            sentence_answer=vocab_word.sentence_answer,
        )

    # Pool-based next word
    cache = RedisVocabCache(settings.redis_url)
    try:
        pool_word = await cache.pop_vocab_word(level)
        remaining = await cache.pool_size(level)
    finally:
        await cache.close()

    if remaining < _POOL_REFILL_THRESHOLD and settings.groq_api_key:
        generate_vocab_task.delay(level)

    if pool_word is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="vocab pool empty — generation queued, try again shortly",
        )

    return VocabWordResponse(
        word=pool_word.word,
        cefr_level=pool_word.cefr_level,
        pos=pool_word.pos,
        definition=pool_word.definition,
        etymology=pool_word.etymology,
        register=pool_word.register,
        contrast_note=pool_word.contrast_note,
        memory_hook=pool_word.memory_hook,
        examples=list(pool_word.examples),
        sentence_stem=pool_word.sentence_stem,
        sentence_answer=pool_word.sentence_answer,
    )


class PracticedRequest(BaseModel):
    word: str
    cefr_level: str
    pos: str


@router.post("/practiced", status_code=204)
async def record_practiced(
    body: PracticedRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = PostgresVocabRepository(db)
    await repo.record_practiced(user_id, body.word, body.cefr_level, body.pos)


class VocabListItem(BaseModel):
    word: str
    cefr_level: str
    pos: str
    practiced_at: datetime


@router.get("/list", response_model=list[VocabListItem])
async def list_vocab(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[VocabListItem]:
    repo = PostgresVocabRepository(db)
    rows = await repo.list_words(user_id)
    return [
        VocabListItem(
            word=r.word,
            cefr_level=r.cefr_level,
            pos=r.pos,
            practiced_at=r.practiced_at,
        )
        for r in rows
    ]
