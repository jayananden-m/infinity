from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.session import KeystrokeEvent, SessionMetrics, TypingSession
from src.domain.services.auth import decode_access_token
from src.domain.services.scoring import score_session
from src.domain.services.skill_updater import update_cognitive_skill, update_motor_skill
from src.infrastructure.database.connection import AsyncSessionFactory
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
from src.observability.logging import get_logger
from src.observability.metrics import (
    SESSIONS_COMPLETED,
    WPM_HISTOGRAM,
)

router = APIRouter()
_log = get_logger(__name__)


async def _update_skills(
    db: AsyncSession,
    user_id: UUID,
    passage_id: UUID,
    metrics: SessionMetrics,
) -> None:
    motor_repo = PostgresMotorSkillRepository(db)
    cognitive_repo = PostgresCognitiveSkillRepository(db)
    passage_repo = PostgresPassageRepository(db)

    motor = await motor_repo.get_by_user(user_id)
    cognitive = await cognitive_repo.get_by_user(user_id)
    passage = await passage_repo.get_by_id(passage_id)

    if motor is None or cognitive is None:
        return

    new_motor = update_motor_skill(motor, metrics)
    await motor_repo.save(new_motor)

    grammar_tags = passage.grammar_tags if passage else ()
    challenged_level = passage.difficulty.cognitive.grammar_level if passage else None
    new_cognitive = update_cognitive_skill(cognitive, grammar_tags, metrics, challenged_grammar_level=challenged_level)
    await cognitive_repo.save(new_cognitive)
    _log.info(
        "skills.updated",
        user_id=str(user_id),
        new_wpm=new_motor.overall_wpm,
        new_grammar_level=new_cognitive.grammar_level,
    )


def _authenticate(token: str) -> UUID | None:
    try:
        payload = decode_access_token(token)
        return UUID(payload["sub"])
    except (ValueError, KeyError):
        return None


def _session_valid(session: TypingSession | None, user_id: UUID) -> bool:
    return session is not None and session.user_id == user_id and session.status.value == "started"


@router.websocket("/api/v1/sessions/{session_id}/stream")
async def keystroke_stream(websocket: WebSocket, session_id: UUID) -> None:
    token = websocket.query_params.get("token", "")
    user_id = _authenticate(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionFactory() as db, db.begin():
        repo = PostgresSessionRepository(db)
        session = await repo.get_by_id(session_id)

        if not _session_valid(session, user_id) or session is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        _log.info(
            "ws.connected",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        buffer: list[KeystrokeEvent] = []

        try:
            while True:
                data = await websocket.receive_json()

                if data.get("action") == "complete":
                    metrics = score_session(tuple(buffer), session.started_at, datetime.now(UTC))
                    completed = session.complete(tuple(buffer), metrics)
                    await repo.save(completed)

                    await _update_skills(db, user_id, session.passage_id, metrics)

                    SESSIONS_COMPLETED.inc()
                    WPM_HISTOGRAM.observe(metrics.wpm)
                    _log.info(
                        "ws.completed",
                        session_id=str(session_id),
                        user_id=str(user_id),
                        wpm=metrics.wpm,
                        accuracy=metrics.accuracy,
                    )
                    await websocket.send_json(
                        {
                            "status": "completed",
                            "wpm": metrics.wpm,
                            "accuracy": metrics.accuracy,
                        }
                    )
                    await websocket.close()
                    return

                buffer.append(
                    KeystrokeEvent(
                        key=str(data["key"]),
                        timestamp_ms=int(data["timestamp_ms"]),
                        correct=bool(data["correct"]),
                    )
                )
                await websocket.send_json(
                    {
                        "status": "ok",
                        "keystroke_count": len(buffer),
                    }
                )

        except WebSocketDisconnect:
            _log.info(
                "ws.disconnected",
                session_id=str(session_id),
                user_id=str(user_id),
            )
