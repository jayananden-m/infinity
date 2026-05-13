from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user_id, get_db
from src.domain.services.user_setup import initialise_user_profiles
from src.infrastructure.database.repositories.cognitive_skill_repository import (
    PostgresCognitiveSkillRepository,
)
from src.infrastructure.database.repositories.motor_skill_repository import (
    PostgresMotorSkillRepository,
)

router = APIRouter(prefix="/users", tags=["users"])


class MotorSkillOut(BaseModel):
    overall_wpm: float
    overall_accuracy: float
    weak_keys: list[str]


class CognitiveSkillOut(BaseModel):
    grammar_level: int
    vocabulary_tier: int
    weak_areas: list[str]
    strong_areas: list[str]


class SkillsResponse(BaseModel):
    motor: MotorSkillOut
    cognitive: CognitiveSkillOut


@router.get("/me/skills", response_model=SkillsResponse)
async def get_my_skills(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SkillsResponse:
    motor_repo = PostgresMotorSkillRepository(db)
    cognitive_repo = PostgresCognitiveSkillRepository(db)
    motor, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)
    return SkillsResponse(
        motor=MotorSkillOut(
            overall_wpm=motor.overall_wpm,
            overall_accuracy=motor.overall_accuracy,
            weak_keys=motor.weakest_keys(3),
        ),
        cognitive=CognitiveSkillOut(
            grammar_level=cognitive.grammar_level,
            vocabulary_tier=cognitive.vocabulary_tier,
            weak_areas=list(cognitive.weak_areas),
            strong_areas=list(cognitive.strong_areas),
        ),
    )
