from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import IPassageRepository
from src.domain.models.passage import DifficultyVector, Passage, PassageSource
from src.infrastructure.database.models import PassageORM


class PostgresPassageRepository(IPassageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, passage_id: UUID) -> Passage | None:
        row = await self._session.get(PassageORM, passage_id)
        return _to_domain(row) if row else None

    async def find_by_difficulty(self, _vector: DifficultyVector, limit: int = 5) -> list[Passage]:
        # Full GIN-based JSONB matching is added in Phase 11 (Redis + query tuning).
        # For now, return recent passages and let the selector pick.
        result = await self._session.execute(select(PassageORM).order_by(PassageORM.created_at.desc()).limit(limit))
        return [_to_domain(row) for row in result.scalars()]

    async def save(self, passage: Passage) -> None:
        row = await self._session.get(PassageORM, passage.id)
        if row is None:
            self._session.add(_to_orm(passage))


def _to_domain(row: PassageORM) -> Passage:
    return Passage(
        id=row.id,
        content=row.content,
        difficulty=DifficultyVector.from_dict(row.difficulty),
        grammar_tags=tuple(row.grammar_tags),
        word_count=row.word_count,
        source=PassageSource(row.source),
        created_at=row.created_at,
    )


def _to_orm(passage: Passage) -> PassageORM:
    return PassageORM(
        id=passage.id,
        content=passage.content,
        difficulty=passage.difficulty.to_dict(),
        grammar_tags=list(passage.grammar_tags),
        word_count=passage.word_count,
        source=passage.source.value,
        created_at=passage.created_at,
    )
