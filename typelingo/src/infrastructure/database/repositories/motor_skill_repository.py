from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import IMotorSkillRepository
from src.domain.models.skill import BigramProfile, KeyProfile
from src.domain.models.user import MotorSkillProfile
from src.infrastructure.database.models import MotorSkillProfileORM


class PostgresMotorSkillRepository(IMotorSkillRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: UUID) -> MotorSkillProfile | None:
        result = await self._session.execute(
            select(MotorSkillProfileORM).where(MotorSkillProfileORM.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def save(self, profile: MotorSkillProfile) -> None:
        result = await self._session.execute(
            select(MotorSkillProfileORM).where(MotorSkillProfileORM.user_id == profile.user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            self._session.add(_to_orm(profile))
        else:
            row.overall_wpm = profile.overall_wpm
            row.overall_accuracy = profile.overall_accuracy
            row.key_profiles = {k: _key_to_dict(v) for k, v in profile.key_profiles.items()}
            row.bigram_stats = {k: _bigram_to_dict(v) for k, v in profile.bigram_stats.items()}


def _to_domain(row: MotorSkillProfileORM) -> MotorSkillProfile:
    return MotorSkillProfile(
        user_id=row.user_id,
        overall_wpm=row.overall_wpm,
        overall_accuracy=row.overall_accuracy,
        key_profiles={k: _key_from_dict(v) for k, v in row.key_profiles.items()},
        bigram_stats={k: _bigram_from_dict(v) for k, v in row.bigram_stats.items()},
    )


def _to_orm(profile: MotorSkillProfile) -> MotorSkillProfileORM:
    return MotorSkillProfileORM(
        user_id=profile.user_id,
        overall_wpm=profile.overall_wpm,
        overall_accuracy=profile.overall_accuracy,
        key_profiles={k: _key_to_dict(v) for k, v in profile.key_profiles.items()},
        bigram_stats={k: _bigram_to_dict(v) for k, v in profile.bigram_stats.items()},
        updated_at=datetime.now(UTC),
    )


def _key_to_dict(k: KeyProfile) -> dict[str, float | int]:
    return {"avg_ms": k.avg_ms, "error_rate": k.error_rate, "samples": k.samples}


def _key_from_dict(d: dict[str, float | int]) -> KeyProfile:
    return KeyProfile(
        avg_ms=float(d["avg_ms"]),
        error_rate=float(d["error_rate"]),
        samples=int(d["samples"]),
    )


def _bigram_to_dict(b: BigramProfile) -> dict[str, float | int]:
    return {"avg_ms": b.avg_ms, "samples": b.samples}


def _bigram_from_dict(d: dict[str, float | int]) -> BigramProfile:
    return BigramProfile(avg_ms=float(d["avg_ms"]), samples=int(d["samples"]))
