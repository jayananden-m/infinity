from dataclasses import replace
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user_id, get_db
from src.config import settings
from src.domain.models.vocab import CEFR_LEVELS, AssessmentQuestion
from src.domain.services.user_setup import initialise_user_profiles
from src.infrastructure.cache.vocab_cache import RedisVocabCache
from src.infrastructure.database.repositories.cognitive_skill_repository import (
    PostgresCognitiveSkillRepository,
)
from src.infrastructure.database.repositories.motor_skill_repository import (
    PostgresMotorSkillRepository,
)
from src.infrastructure.queue.tasks import generate_assess_questions_task

router = APIRouter(prefix="/assess", tags=["assess"])

# Hardcoded fallback questions — used when cache is cold and LLM is unavailable.
# Two per CEFR level, ordered A1 → C2.
_FALLBACK_QUESTIONS: list[AssessmentQuestion] = [
    # A1
    AssessmentQuestion(
        "I ___ a student.",
        ("am", "is", "are", "be"),
        0,
        "A1",
        "'I' always takes 'am' with the verb to be.",
    ),
    AssessmentQuestion(
        "She ___ to school every day.",
        ("go", "goes", "going", "gone"),
        1,
        "A1",
        "Third-person singular present simple adds -s/-es.",
    ),
    # A2
    AssessmentQuestion(
        "We ___ to Paris last summer.",
        ("go", "went", "have gone", "will go"),
        1,
        "A2",
        "Past simple uses the simple past form for completed past events.",
    ),
    AssessmentQuestion(
        "There ___ some apples on the table.",
        ("is", "are", "was", "were"),
        1,
        "A2",
        "'There are' is used because the subject 'apples' is plural.",
    ),
    # B1
    AssessmentQuestion(
        "She had ___ finished her work when the guests arrived.",
        ("just", "already", "yet", "still"),
        1,
        "B1",
        "'Already' in affirmative past perfect shows completion before another past event.",
    ),
    AssessmentQuestion(
        "If I ___ more time, I would travel the world.",
        ("have", "had", "will have", "would have"),
        1,
        "B1",
        "Second conditional uses past simple in the if-clause.",
    ),
    # B2
    AssessmentQuestion(
        "The project will ___ completed by next Friday.",
        ("be", "been", "being", "have"),
        0,
        "B2",
        "Future passive uses 'will + be + past participle'.",
    ),
    AssessmentQuestion(
        "No sooner had he arrived ___ the meeting began.",
        ("than", "when", "as", "then"),
        0,
        "B2",
        "'No sooner…than' is a fixed correlative conjunction.",
    ),
    # C1
    AssessmentQuestion(
        "The committee is said ___ reached a consensus.",
        ("to have", "to be", "having", "to"),
        0,
        "C1",
        "'Is said to have done' reports a completed past action via passive + perfect infinitive.",
    ),
    AssessmentQuestion(
        "She spoke with such ___ that her audience was convinced.",
        ("eloquence", "eloquent", "eloquently", "eloquency"),
        0,
        "C1",
        "After 'with such', a noun is required; 'eloquence' is the correct noun form.",
    ),
    # C2
    AssessmentQuestion(
        "Scarcely ___ the announcement been made when protests erupted.",
        ("had", "has", "have", "did"),
        0,
        "C2",
        "'Scarcely had' triggers subject-auxiliary inversion in the same pattern as 'no sooner had'.",
    ),
    AssessmentQuestion(
        "The ___ of the argument rested on a single unverified assumption.",
        ("crux", "crust", "crunch", "crush"),
        0,
        "C2",
        "'Crux' means the decisive or most important point of a matter.",
    ),
]


class AssessmentQuestionResponse(BaseModel):
    sentence: str
    options: list[str]
    correct_index: int
    cefr_level: str
    explanation: str


class AssessCompleteRequest(BaseModel):
    cefr_level: str


class AssessCompleteResponse(BaseModel):
    cefr_level: str


@router.get("/questions", response_model=list[AssessmentQuestionResponse])
async def get_assessment_questions(
    _user_id: UUID = Depends(get_current_user_id),
    _db: AsyncSession = Depends(get_db),
) -> list[AssessmentQuestionResponse]:
    cache = RedisVocabCache(settings.redis_url)
    questions: list[AssessmentQuestion] = []

    try:
        for level in CEFR_LEVELS:
            cached = await cache.get_assess_questions(level)
            if cached:
                questions.extend(cached)
            else:
                # Use fallback and enqueue generation for next time
                fallback = [q for q in _FALLBACK_QUESTIONS if q.cefr_level == level]
                questions.extend(fallback)
                if settings.groq_api_key:
                    generate_assess_questions_task.delay(level)
    finally:
        await cache.close()

    return [
        AssessmentQuestionResponse(
            sentence=q.sentence,
            options=list(q.options),
            correct_index=q.correct_index,
            cefr_level=q.cefr_level,
            explanation=q.explanation,
        )
        for q in questions
    ]


@router.post("/complete", response_model=AssessCompleteResponse)
async def complete_assessment(
    body: AssessCompleteRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> AssessCompleteResponse:
    if body.cefr_level not in CEFR_LEVELS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid cefr_level")

    motor_repo = PostgresMotorSkillRepository(db)
    cognitive_repo = PostgresCognitiveSkillRepository(db)
    _, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)

    updated = replace(cognitive, cefr_level=body.cefr_level)
    await cognitive_repo.save(updated)

    return AssessCompleteResponse(cefr_level=body.cefr_level)
