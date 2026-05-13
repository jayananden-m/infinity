from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import UserVocabORM


class PostgresVocabRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record_practiced(self, user_id: UUID, word: str, cefr_level: str, pos: str) -> None:
        now = datetime.now(UTC)
        stmt = (
            insert(UserVocabORM)
            .values(
                user_id=user_id,
                word=word.lower(),
                cefr_level=cefr_level,
                pos=pos,
                practiced_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_user_vocab_user_word",
                set_={"practiced_at": now, "cefr_level": cefr_level, "pos": pos},
            )
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def list_words(self, user_id: UUID) -> list[UserVocabORM]:
        result = await self._db.execute(
            select(UserVocabORM).where(UserVocabORM.user_id == user_id).order_by(UserVocabORM.practiced_at.desc())
        )
        return list(result.scalars().all())

    async def get_recent_words(self, user_id: UUID, limit: int = 10) -> list[str]:
        result = await self._db.execute(
            select(UserVocabORM.word)
            .where(UserVocabORM.user_id == user_id)
            .order_by(UserVocabORM.practiced_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
