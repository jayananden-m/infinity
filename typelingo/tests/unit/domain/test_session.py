from datetime import UTC
from uuid import uuid4

import pytest

from src.domain.models.session import (
    KeystrokeEvent,
    SessionMetrics,
    SessionStatus,
    TypingSession,
)


def make_metrics() -> SessionMetrics:
    return SessionMetrics(wpm=45.0, accuracy=0.95, duration_seconds=60.0, per_key_stats={})


def make_keystrokes() -> tuple[KeystrokeEvent, ...]:
    return (
        KeystrokeEvent(key="h", timestamp_ms=0, correct=True),
        KeystrokeEvent(key="i", timestamp_ms=80, correct=True),
    )


class TestTypingSession:
    def test_start_creates_session_with_started_status(self):
        session = TypingSession.start(uuid4(), uuid4())
        assert session.status == SessionStatus.STARTED

    def test_start_creates_empty_keystrokes(self):
        session = TypingSession.start(uuid4(), uuid4())
        assert session.keystrokes == ()

    def test_start_sets_utc_timestamp(self):
        session = TypingSession.start(uuid4(), uuid4())
        assert session.started_at.tzinfo is UTC

    def test_complete_transitions_status_to_completed(self):
        session = TypingSession.start(uuid4(), uuid4())
        completed = session.complete(make_keystrokes(), make_metrics())
        assert completed.status == SessionStatus.COMPLETED

    def test_complete_preserves_session_id(self):
        session = TypingSession.start(uuid4(), uuid4())
        completed = session.complete(make_keystrokes(), make_metrics())
        assert completed.id == session.id

    def test_complete_sets_completed_at(self):
        session = TypingSession.start(uuid4(), uuid4())
        completed = session.complete(make_keystrokes(), make_metrics())
        assert completed.completed_at is not None

    def test_complete_stores_metrics(self):
        session = TypingSession.start(uuid4(), uuid4())
        metrics = make_metrics()
        completed = session.complete(make_keystrokes(), metrics)
        assert completed.metrics == metrics

    def test_cannot_complete_already_completed_session(self):
        session = TypingSession.start(uuid4(), uuid4())
        completed = session.complete(make_keystrokes(), make_metrics())
        with pytest.raises(ValueError, match="completed"):
            completed.complete(make_keystrokes(), make_metrics())

    def test_cannot_complete_abandoned_session(self):
        session = TypingSession.start(uuid4(), uuid4())
        abandoned = session.abandon()
        with pytest.raises(ValueError, match="abandoned"):
            abandoned.complete(make_keystrokes(), make_metrics())

    def test_abandon_transitions_status(self):
        session = TypingSession.start(uuid4(), uuid4())
        abandoned = session.abandon()
        assert abandoned.status == SessionStatus.ABANDONED

    def test_cannot_abandon_completed_session(self):
        session = TypingSession.start(uuid4(), uuid4())
        completed = session.complete(make_keystrokes(), make_metrics())
        with pytest.raises(ValueError, match="completed"):
            completed.abandon()

    def test_complete_returns_new_instance(self):
        session = TypingSession.start(uuid4(), uuid4())
        completed = session.complete(make_keystrokes(), make_metrics())
        assert completed is not session
        assert session.status == SessionStatus.STARTED  # original unchanged


class TestKeystrokeEvent:
    def test_is_immutable(self):
        event = KeystrokeEvent(key="a", timestamp_ms=100, correct=True)
        with pytest.raises(AttributeError):
            event.key = "b"  # type: ignore[misc]
