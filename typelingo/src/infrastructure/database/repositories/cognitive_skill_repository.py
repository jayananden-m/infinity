from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import ICognitiveSkillRepository
from src.domain.models.user import CognitiveSkillProfile
from src.infrastructure.database.models import CognitiveSkillProfileORM


class PostgresCognitiveSkillRepository(ICognitiveSkillRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: UUID) -> CognitiveSkillProfile | None:
        result = await self._session.execute(
            select(CognitiveSkillProfileORM).where(CognitiveSkillProfileORM.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def save(self, profile: CognitiveSkillProfile) -> None:
        result = await self._session.execute(
            select(CognitiveSkillProfileORM).where(CognitiveSkillProfileORM.user_id == profile.user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            self._session.add(_to_orm(profile))
        else:
            row.grammar_level = profile.grammar_level
            row.vocabulary_tier = profile.vocabulary_tier
            row.weak_areas = list(profile.weak_areas)
            row.strong_areas = list(profile.strong_areas)
            row.cefr_level = profile.cefr_level
            row.updated_at = datetime.now(UTC)


def _to_domain(row: CognitiveSkillProfileORM) -> CognitiveSkillProfile:
    return CognitiveSkillProfile(
        user_id=row.user_id,
        grammar_level=row.grammar_level,
        vocabulary_tier=row.vocabulary_tier,
        weak_areas=tuple(row.weak_areas),
        strong_areas=tuple(row.strong_areas),
        cefr_level=getattr(row, "cefr_level", "A1"),
    )


def _to_orm(profile: CognitiveSkillProfile) -> CognitiveSkillProfileORM:
    return CognitiveSkillProfileORM(
        user_id=profile.user_id,
        grammar_level=profile.grammar_level,
        vocabulary_tier=profile.vocabulary_tier,
        weak_areas=list(profile.weak_areas),
        strong_areas=list(profile.strong_areas),
        cefr_level=profile.cefr_level,
        updated_at=datetime.now(UTC),
    )
