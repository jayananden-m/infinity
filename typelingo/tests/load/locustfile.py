"""Locust load test for TypeLingo API.

Run with:
    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

import random
import string

from locust import HttpUser, between, task


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase, k=8))  # noqa: S311
    return f"loadtest_{suffix}@example.com"


class TypingUser(HttpUser):
    """Simulates a user registering, logging in, and typing sessions."""

    wait_time = between(1, 3)
    token: str = ""

    def on_start(self) -> None:
        """Register then immediately log in to obtain a JWT."""
        email = _random_email()
        password = "Loadtest1!"  # noqa: S105

        self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "display_name": "Load Tester",
                "password": password,
            },
        )

        with self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json()["access_token"]
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def start_and_complete_session(self) -> None:
        """Start a session and immediately complete it with dummy metrics."""
        if not self.token:
            return

        with self.client.post(
            "/api/v1/sessions",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(f"start_session failed: {resp.status_code}")
                return
            session_id: str = resp.json()["id"]

        self.client.post(
            f"/api/v1/sessions/{session_id}/complete",
            headers=self._auth_headers(),
            json={
                "keystrokes": [{"key": "a", "timestamp_ms": 0, "correct": True}],
                "metrics": {
                    "wpm": 45.0,
                    "accuracy": 0.95,
                    "duration_seconds": 30.0,
                    "per_key_stats": {},
                },
            },
        )

    @task(1)
    def check_health(self) -> None:
        self.client.get("/api/v1/health")
