import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user_id, get_db
from src.config import settings
from src.domain.models.passage import DifficultyVector, Passage, PassageSource
from src.domain.models.session import KeystrokeEvent, SessionMetrics, TypingSession
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.passage_selector import NoPassageAvailableError, select_passage
from src.domain.services.user_setup import initialise_user_profiles
from src.infrastructure.cache.redis_cache import RedisPassageCache
from src.infrastructure.database.repositories.cognitive_skill_repository import (
    PostgresCognitiveSkillRepository,
)
from src.infrastructure.database.repositories.motor_skill_repository import (
    PostgresMotorSkillRepository,
)
from src.infrastructure.database.repositories.passage_repository import (
    PostgresPassageRepository,
)
from src.infrastructure.database.repositories.session_repository import (
    PostgresSessionRepository,
)
from src.infrastructure.database.repositories.vocab_repository import (
    PostgresVocabRepository,
)
from src.infrastructure.llm.groq_client import (
    generate_cloze_items,
    generate_drill_session,
    generate_mine_passage,
)
from src.infrastructure.queue.tasks import generate_passage_task
from src.observability.logging import get_logger
from src.observability.metrics import (
    SESSIONS_ABANDONED,
    SESSIONS_COMPLETED,
    SESSIONS_STARTED,
    WPM_HISTOGRAM,
)

# Grammar targets per CEFR level — used when user has no weak_areas yet
_CEFR_GRAMMAR_DEFAULTS: dict[str, list[str]] = {
    "A1": ["present simple", "basic questions", "there is / there are"],
    "A2": ["past simple", "present continuous", "comparative adjectives"],
    "B1": ["present perfect", "modal verbs", "passive voice"],
    "B2": ["conditional clauses", "relative clauses", "reported speech"],
    "C1": ["subjunctive mood", "cleft sentences", "noun clauses"],
    "C2": ["nominalization", "pragmatic hedging", "discourse markers"],
}

router = APIRouter(prefix="/sessions", tags=["sessions"])
_log = get_logger(__name__)

_MIN_VOCAB_WORDS = 2


class KeystrokeIn(BaseModel):
    key: str
    timestamp_ms: int
    correct: bool


class MetricsIn(BaseModel):
    wpm: float
    accuracy: float
    duration_seconds: float
    per_key_stats: dict[str, dict[str, float]]


class CompleteRequest(BaseModel):
    keystrokes: list[KeystrokeIn]
    metrics: MetricsIn


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    passage_id: UUID
    status: str
    passage_content: str | None = None


class MineSessionResponse(BaseModel):
    id: UUID
    mode: str = "mine"
    passage: str
    target_words: list[str]


class ClozeItemSchema(BaseModel):
    full: str
    stem: str
    answer: str


class ClozeSessionResponse(BaseModel):
    id: UUID
    mode: str = "cloze"
    items: list[ClozeItemSchema]


class DrillRoundSchema(BaseModel):
    round_type: str
    text: str
    stem: str | None = None
    target_word: str | None = None


class DrillSessionResponse(BaseModel):
    id: UUID
    mode: str = "drill"
    rounds: list[DrillRoundSchema]
    grammar_target: str


def _make_difficulty(
    motor: MotorSkillProfile,
    cognitive: CognitiveSkillProfile,
    grammar_targets: list[str] | None = None,
) -> DifficultyVector:
    return DifficultyVector.from_dict(
        {
            "motor": {
                "target_wpm": motor.overall_wpm,
                "key_focus": [],
                "bigram_focus": [],
                "word_length_avg": 5.0,
            },
            "cognitive": {
                "grammar_level": cognitive.grammar_level,
                "vocabulary_tier": cognitive.vocabulary_tier,
                "grammar_targets": grammar_targets or [],
                "sentence_complexity": 0.5,
            },
        }
    )


async def _persist_session(  # noqa: PLR0913
    content: str,
    difficulty: DifficultyVector,
    grammar_tags: tuple[str, ...],
    user_id: UUID,
    passage_repo: PostgresPassageRepository,
    session_repo: PostgresSessionRepository,
    mode: str,
) -> TypingSession:
    passage = Passage.create(
        content=content, difficulty=difficulty, grammar_tags=grammar_tags, source=PassageSource.LLM
    )
    await passage_repo.save(passage)
    typing_session = TypingSession.start(user_id, passage.id)
    await session_repo.save(typing_session)
    SESSIONS_STARTED.inc()
    _log.info("session.started", session_id=str(typing_session.id), user_id=str(user_id), mode=mode)
    return typing_session


async def _start_mine(  # noqa: PLR0913
    user_id: UUID,
    motor: MotorSkillProfile,
    cognitive: CognitiveSkillProfile,
    vocab_repo: PostgresVocabRepository,
    passage_repo: PostgresPassageRepository,
    session_repo: PostgresSessionRepository,
) -> MineSessionResponse:
    if not settings.groq_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM not configured")
    vocab_words = await vocab_repo.get_recent_words(user_id, limit=10)
    if len(vocab_words) < _MIN_VOCAB_WORDS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"practice at least {_MIN_VOCAB_WORDS} vocab words first — use /vocab to learn words",
        )
    data = await generate_mine_passage(cognitive.cefr_level, vocab_words)
    passage_text: str = data.get("passage", "").strip()
    target_words: list[str] = data.get("target_words", [])
    if not passage_text:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="generation failed")
    typing_session = await _persist_session(
        passage_text, _make_difficulty(motor, cognitive), (), user_id, passage_repo, session_repo, "mine"
    )
    return MineSessionResponse(id=typing_session.id, passage=passage_text, target_words=target_words)


async def _start_cloze(  # noqa: PLR0913
    user_id: UUID,
    motor: MotorSkillProfile,
    cognitive: CognitiveSkillProfile,
    vocab_repo: PostgresVocabRepository,
    passage_repo: PostgresPassageRepository,
    session_repo: PostgresSessionRepository,
) -> ClozeSessionResponse:
    if not settings.groq_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM not configured")
    vocab_words = await vocab_repo.get_recent_words(user_id, limit=8)
    if len(vocab_words) < _MIN_VOCAB_WORDS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"practice at least {_MIN_VOCAB_WORDS} vocab words first — use /vocab to learn words",
        )
    raw_items = await generate_cloze_items(cognitive.cefr_level, vocab_words)
    items = [ClozeItemSchema(full=d["full"], stem=d["stem"], answer=d["answer"]) for d in raw_items]
    if not items:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="generation failed")
    synthetic = " ".join(item.full for item in items)
    typing_session = await _persist_session(
        synthetic, _make_difficulty(motor, cognitive), (), user_id, passage_repo, session_repo, "cloze"
    )
    return ClozeSessionResponse(id=typing_session.id, items=items)


async def _start_drill(
    user_id: UUID,
    motor: MotorSkillProfile,
    cognitive: CognitiveSkillProfile,
    passage_repo: PostgresPassageRepository,
    session_repo: PostgresSessionRepository,
) -> DrillSessionResponse:
    if not settings.groq_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM not configured")
    candidates = list(cognitive.weak_areas) or _CEFR_GRAMMAR_DEFAULTS.get(cognitive.cefr_level, ["present simple"])
    grammar_target = random.choice(candidates)  # noqa: S311
    data = await generate_drill_session(grammar_target, cognitive.cefr_level)
    rounds = [
        DrillRoundSchema(
            round_type=r["round_type"], text=r["text"], stem=r.get("stem"), target_word=r.get("target_word")
        )
        for r in data.get("rounds", [])
    ]
    if not rounds:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="generation failed")
    synthetic = " ".join(r.text for r in rounds)
    typing_session = await _persist_session(
        synthetic,
        _make_difficulty(motor, cognitive, [grammar_target]),
        (grammar_target,),
        user_id,
        passage_repo,
        session_repo,
        "drill",
    )
    return DrillSessionResponse(id=typing_session.id, rounds=rounds, grammar_target=grammar_target)


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_session(
    mode: str | None = Query(None, pattern="^(mine|cloze|drill)$"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse | MineSessionResponse | ClozeSessionResponse | DrillSessionResponse:
    motor_repo = PostgresMotorSkillRepository(db)
    cognitive_repo = PostgresCognitiveSkillRepository(db)
    passage_repo = PostgresPassageRepository(db)
    session_repo = PostgresSessionRepository(db)
    vocab_repo = PostgresVocabRepository(db)
    motor, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)

    if mode == "mine":
        return await _start_mine(user_id, motor, cognitive, vocab_repo, passage_repo, session_repo)
    if mode == "cloze":
        return await _start_cloze(user_id, motor, cognitive, vocab_repo, passage_repo, session_repo)
    if mode == "drill":
        return await _start_drill(user_id, motor, cognitive, passage_repo, session_repo)

    # ── Regular adaptive session ─────────────────────────────────────────────
    cache = RedisPassageCache(settings.redis_url)

    def _enqueue(vector: DifficultyVector) -> None:
        if settings.groq_api_key:
            generate_passage_task.delay(vector.to_dict(), list(vector.cognitive.grammar_targets))

    try:
        passage = await select_passage(motor, cognitive, passage_repo, cache=cache, enqueue_generation=_enqueue)
    except NoPassageAvailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="no passages available") from exc

    typing_session = TypingSession.start(user_id, passage.id)
    await session_repo.save(typing_session)
    SESSIONS_STARTED.inc()
    _log.info("session.started", session_id=str(typing_session.id), user_id=str(user_id))
    return SessionResponse(
        id=typing_session.id,
        user_id=typing_session.user_id,
        passage_id=typing_session.passage_id,
        status=typing_session.status.value,
        passage_content=passage.content,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session_repo = PostgresSessionRepository(db)
    passage_repo = PostgresPassageRepository(db)
    session = await session_repo.get_by_id(session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    passage = await passage_repo.get_by_id(session.passage_id)
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        passage_id=session.passage_id,
        status=session.status.value,
        passage_content=passage.content if passage else None,
    )


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    body: CompleteRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    repo = PostgresSessionRepository(db)
    session = await repo.get_by_id(session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")

    keystrokes = tuple(
        KeystrokeEvent(key=k.key, timestamp_ms=k.timestamp_ms, correct=k.correct) for k in body.keystrokes
    )
    metrics = SessionMetrics(
        wpm=body.metrics.wpm,
        accuracy=body.metrics.accuracy,
        duration_seconds=body.metrics.duration_seconds,
        per_key_stats=body.metrics.per_key_stats,
    )
    try:
        completed = session.complete(keystrokes, metrics)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await repo.save(completed)
    SESSIONS_COMPLETED.inc()
    WPM_HISTOGRAM.observe(body.metrics.wpm)
    _log.info(
        "session.completed",
        session_id=str(session_id),
        user_id=str(user_id),
        wpm=body.metrics.wpm,
        accuracy=body.metrics.accuracy,
    )
    return SessionResponse(
        id=completed.id,
        user_id=completed.user_id,
        passage_id=completed.passage_id,
        status=completed.status.value,
    )


@router.post("/{session_id}/abandon", response_model=SessionResponse)
async def abandon_session(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    repo = PostgresSessionRepository(db)
    session = await repo.get_by_id(session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")

    try:
        abandoned = session.abandon()
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await repo.save(abandoned)
    SESSIONS_ABANDONED.inc()
    _log.info(
        "session.abandoned",
        session_id=str(session_id),
        user_id=str(user_id),
    )
    return SessionResponse(
        id=abandoned.id,
        user_id=abandoned.user_id,
        passage_id=abandoned.passage_id,
        status=abandoned.status.value,
    )
