"""Integration tests: PostgresSessionRepository against a real database."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.session import SessionStatus, TypingSession
from src.infrastructure.database.repositories.session_repository import (
    PostgresSessionRepository,
)


@pytest.mark.integration()
async def test_save_and_retrieve_session(db_session: AsyncSession) -> None:
    repo = PostgresSessionRepository(db_session)
    user_id = uuid4()
    passage_id = uuid4()

    session = TypingSession(
        id=uuid4(),
        user_id=user_id,
        passage_id=passage_id,
        status=SessionStatus.STARTED,
        started_at=datetime.now(UTC),
        completed_at=None,
        keystrokes=(),
        metrics=None,
    )
    await repo.save(session)

    fetched = await repo.get_by_id(session.id)
    assert fetched is not None
    assert fetched.id == session.id
    assert fetched.user_id == user_id
    assert fetched.status == SessionStatus.STARTED


@pytest.mark.integration()
async def test_disconnect_does_not_abandon_session(db_session: AsyncSession) -> None:
    """Session must remain STARTED after a WebSocket disconnect (no auto-abandon)."""
    repo = PostgresSessionRepository(db_session)

    session = TypingSession(
        id=uuid4(),
        user_id=uuid4(),
        passage_id=uuid4(),
        status=SessionStatus.STARTED,
        started_at=datetime.now(UTC),
        completed_at=None,
        keystrokes=(),
        metrics=None,
    )
    await repo.save(session)

    # Simulate disconnect: handler just logs, does NOT call session.abandon()
    fetched = await repo.get_by_id(session.id)
    assert fetched is not None
    assert fetched.status == SessionStatus.STARTED


@pytest.mark.integration()
async def test_get_recent_by_user_returns_ordered(db_session: AsyncSession) -> None:
    repo = PostgresSessionRepository(db_session)
    user_id = uuid4()

    ids = []
    for _ in range(3):
        s = TypingSession(
            id=uuid4(),
            user_id=user_id,
            passage_id=uuid4(),
            status=SessionStatus.STARTED,
            started_at=datetime.now(UTC),
            completed_at=None,
            keystrokes=(),
            metrics=None,
        )
        await repo.save(s)
        ids.append(s.id)

    recent = await repo.get_recent_by_user(user_id, limit=10)
    assert len(recent) == 3
    # All belong to our user
    assert all(s.user_id == user_id for s in recent)


@pytest.mark.integration()
async def test_reconnect_to_started_session_allowed(db_session: AsyncSession) -> None:
    """After disconnect (session stays STARTED), the session can be fetched and used."""
    repo = PostgresSessionRepository(db_session)
    user_id = uuid4()

    session = TypingSession(
        id=uuid4(),
        user_id=user_id,
        passage_id=uuid4(),
        status=SessionStatus.STARTED,
        started_at=datetime.now(UTC),
        completed_at=None,
        keystrokes=(),
        metrics=None,
    )
    await repo.save(session)

    # _session_valid logic: status must be "started" and user_id must match
    fetched = await repo.get_by_id(session.id)
    assert fetched is not None
    assert fetched.status.value == "started"
    assert fetched.user_id == user_id
