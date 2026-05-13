import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_CLOSED = "closed"
_OPEN = "open"
_HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._state = _CLOSED
        self._failures = 0
        self._opened_at: float | None = None

    def call(self, fn: Callable[[], T]) -> T:
        if self._state == _OPEN:
            if self._should_attempt_reset():
                self._state = _HALF_OPEN
            else:
                raise CircuitOpenError("circuit is open — downstream service unavailable")

        try:
            result = fn()
        except Exception:
            self._on_failure()
            raise
        else:
            self._on_success()
            return result

    def _should_attempt_reset(self) -> bool:
        return self._opened_at is not None and time.monotonic() - self._opened_at >= self.recovery_timeout_seconds

    def _on_success(self) -> None:
        self._state = _CLOSED
        self._failures = 0
        self._opened_at = None

    def _on_failure(self) -> None:
        self._failures += 1
        if self._state == _HALF_OPEN or self._failures >= self.failure_threshold:
            self._state = _OPEN
            self._opened_at = time.monotonic()
