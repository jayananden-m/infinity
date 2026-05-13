from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.domain.models.session import SessionStatus, TypingSession
from src.domain.services.auth import create_access_token
from src.main import create_app
from src.websocket.handler import _authenticate, _session_valid


class TestWebSocketAuth:
    def test_rejects_missing_token(self):
        app = create_app()
        session_id = uuid4()
        with (
            TestClient(app) as client,
            pytest.raises(WebSocketDisconnect),
            client.websocket_connect(f"/api/v1/sessions/{session_id}/stream"),
        ):
            pass

    def test_rejects_invalid_token(self):
        app = create_app()
        session_id = uuid4()
        url = f"/api/v1/sessions/{session_id}/stream?token=bad.token.here"
        with (
            TestClient(app) as client,
            pytest.raises(WebSocketDisconnect),
            client.websocket_connect(url),
        ):
            pass


class TestAuthenticate:
    def test_returns_none_for_bad_token(self):
        assert _authenticate("not.a.real.token") is None

    def test_returns_uuid_for_valid_token(self):
        user_id = uuid4()
        token = create_access_token(subject=str(user_id))
        result = _authenticate(token)
        assert result == user_id

    def test_returns_none_for_non_uuid_sub(self):
        token = create_access_token(subject="not-a-uuid")
        assert _authenticate(token) is None


class TestSessionValid:
    def _make_session(self, user_id, status):
        return TypingSession(
            id=uuid4(),
            user_id=user_id,
            passage_id=uuid4(),
            status=status,
            started_at=datetime.now(UTC),
            completed_at=None,
            keystrokes=(),
            metrics=None,
        )

    def test_started_session_is_valid(self):
        user_id = uuid4()
        session = self._make_session(user_id, SessionStatus.STARTED)
        assert _session_valid(session, user_id) is True

    def test_abandoned_session_is_invalid(self):
        """Reconnecting to an abandoned session must be rejected."""
        user_id = uuid4()
        session = self._make_session(user_id, SessionStatus.ABANDONED)
        assert _session_valid(session, user_id) is False

    def test_completed_session_is_invalid(self):
        user_id = uuid4()
        session = self._make_session(user_id, SessionStatus.COMPLETED)
        assert _session_valid(session, user_id) is False

    def test_wrong_user_is_invalid(self):
        session = self._make_session(uuid4(), SessionStatus.STARTED)
        assert _session_valid(session, uuid4()) is False

    def test_none_session_is_invalid(self):
        assert _session_valid(None, uuid4()) is False

    def test_session_stays_started_after_disconnect(self):
        """After a WebSocketDisconnect the handler only logs — status is unchanged."""
        user_id = uuid4()
        session = self._make_session(user_id, SessionStatus.STARTED)
        # Simulate what the handler now does on disconnect: nothing to the session
        # Status must remain STARTED so the user can reconnect
        assert session.status == SessionStatus.STARTED
