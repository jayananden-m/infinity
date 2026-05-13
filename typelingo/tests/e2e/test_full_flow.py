"""E2E: full user flows through the HTTP API."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e()
class TestAuthFlow:
    def test_register_returns_token(self, client: TestClient) -> None:
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": "e2e_a@test.com",
                "display_name": "E2E A",
                "password": "pw123",
            },
        )
        assert res.status_code == 201
        assert "access_token" in res.json()

    def test_duplicate_register_conflicts(self, client: TestClient) -> None:
        payload = {"email": "e2e_dup@test.com", "display_name": "Dup", "password": "pw"}
        client.post("/api/v1/auth/register", json=payload)
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 409

    def test_login_with_valid_credentials(self, client: TestClient) -> None:
        email = "e2e_login@test.com"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "display_name": "Login", "password": "secret"},
        )
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "secret"})
        assert res.status_code == 200
        assert res.json()["token_type"] == "bearer"  # noqa: S105

    def test_login_wrong_password_is_401(self, client: TestClient) -> None:
        email = "e2e_bad@test.com"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "display_name": "Bad", "password": "right"},
        )
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
        assert res.status_code == 401

    def test_refresh_issues_new_token(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "e2e_refresh@test.com",
                "display_name": "R",
                "password": "pw",
            },
        )
        token = reg.json()["access_token"]
        res = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["access_token"] != token


@pytest.mark.e2e()
class TestSessionFlow:
    def _register(self, client: TestClient, suffix: str) -> str:
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"e2e_sess_{suffix}@test.com",
                "display_name": "S",
                "password": "pw",
            },
        )
        return res.json()["access_token"]

    def test_start_session_returns_passage_content(self, client: TestClient) -> None:
        token = self._register(client, "start")
        res = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 201
        body = res.json()
        assert body["status"] == "started"
        assert isinstance(body["passage_content"], str)
        assert len(body["passage_content"]) > 0

    def test_get_session_returns_passage_content(self, client: TestClient) -> None:
        token = self._register(client, "get")
        start = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"})
        session_id = start.json()["id"]
        res = client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["passage_content"] is not None

    def test_another_user_cannot_access_session(self, client: TestClient) -> None:
        token_a = self._register(client, "owner")
        token_b = self._register(client, "intruder")
        start = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token_a}"})
        session_id = start.json()["id"]
        res = client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404

    def test_abandon_session(self, client: TestClient) -> None:
        token = self._register(client, "abandon")
        start = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"})
        session_id = start.json()["id"]
        res = client.post(
            f"/api/v1/sessions/{session_id}/abandon",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "abandoned"

    def test_cannot_abandon_twice(self, client: TestClient) -> None:
        token = self._register(client, "aband2")
        start = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"})
        session_id = start.json()["id"]
        hdrs = {"Authorization": f"Bearer {token}"}
        client.post(f"/api/v1/sessions/{session_id}/abandon", headers=hdrs)
        res = client.post(f"/api/v1/sessions/{session_id}/abandon", headers=hdrs)
        assert res.status_code == 409


@pytest.mark.e2e()
class TestSkillsFlow:
    def test_skills_returned_for_new_user(self, client: TestClient) -> None:
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": "e2e_skills@test.com",
                "display_name": "Sk",
                "password": "pw",
            },
        )
        token = res.json()["access_token"]
        skills = client.get(
            "/api/v1/users/me/skills",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert skills.status_code == 200
        body = skills.json()
        assert body["motor"]["overall_wpm"] == 30.0
        assert body["cognitive"]["grammar_level"] == 1

    def test_skills_require_auth(self, client: TestClient) -> None:
        res = client.get("/api/v1/users/me/skills")
        assert res.status_code == 403
