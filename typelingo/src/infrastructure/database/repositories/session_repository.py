from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import ISessionRepository
from src.domain.models.session import (
    KeystrokeEvent,
    SessionMetrics,
    SessionStatus,
    TypingSession,
)
from src.infrastructure.database.models import TypingSessionORM


class PostgresSessionRepository(ISessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, session_id: UUID) -> TypingSession | None:
        row = await self._session.get(TypingSessionORM, session_id)
        return _to_domain(row) if row else None

    async def get_recent_by_user(self, user_id: UUID, limit: int = 10) -> list[TypingSession]:
        result = await self._session.execute(
            select(TypingSessionORM)
            .where(TypingSessionORM.user_id == user_id)
            .order_by(TypingSessionORM.started_at.desc())
            .limit(limit)
        )
        return [_to_domain(row) for row in result.scalars()]

    async def save(self, session: TypingSession) -> None:
        row = await self._session.get(TypingSessionORM, session.id)
        if row is None:
            self._session.add(_to_orm(session))
        else:
            row.status = session.status.value
            row.completed_at = session.completed_at
            row.keystrokes = [_keystroke_to_dict(k) for k in session.keystrokes]
            row.metrics = _metrics_to_dict(session.metrics) if session.metrics else None


def _to_domain(row: TypingSessionORM) -> TypingSession:
    return TypingSession(
        id=row.id,
        user_id=row.user_id,
        passage_id=row.passage_id,
        status=SessionStatus(row.status),
        started_at=row.started_at,
        completed_at=row.completed_at,
        keystrokes=tuple(_keystroke_from_dict(k) for k in row.keystrokes),
        metrics=_metrics_from_dict(row.metrics) if row.metrics else None,
    )


def _to_orm(session: TypingSession) -> TypingSessionORM:
    return TypingSessionORM(
        id=session.id,
        user_id=session.user_id,
        passage_id=session.passage_id,
        status=session.status.value,
        started_at=session.started_at,
        completed_at=session.completed_at,
        keystrokes=[_keystroke_to_dict(k) for k in session.keystrokes],
        metrics=_metrics_to_dict(session.metrics) if session.metrics else None,
    )


def _keystroke_to_dict(k: KeystrokeEvent) -> dict[str, str | int | bool]:
    return {"key": k.key, "timestamp_ms": k.timestamp_ms, "correct": k.correct}


def _keystroke_from_dict(d: dict[str, str | int | bool]) -> KeystrokeEvent:
    return KeystrokeEvent(
        key=str(d["key"]),
        timestamp_ms=int(d["timestamp_ms"]),
        correct=bool(d["correct"]),
    )


def _metrics_to_dict(m: SessionMetrics) -> dict[str, object]:
    return {
        "wpm": m.wpm,
        "accuracy": m.accuracy,
        "duration_seconds": m.duration_seconds,
        "per_key_stats": m.per_key_stats,
    }


def _metrics_from_dict(d: dict[str, object]) -> SessionMetrics:
    return SessionMetrics(
        wpm=float(d["wpm"]),  # type: ignore[arg-type]
        accuracy=float(d["accuracy"]),  # type: ignore[arg-type]
        duration_seconds=float(d["duration_seconds"]),  # type: ignore[arg-type]
        per_key_stats=d["per_key_stats"],  # type: ignore[arg-type]
    )
