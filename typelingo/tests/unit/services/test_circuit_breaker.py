import pytest

from src.domain.services.circuit_breaker import CircuitBreaker, CircuitOpenError


def ok() -> str:
    return "ok"


def fail() -> str:
    raise ValueError("downstream error")


class TestCircuitBreaker:
    def test_calls_fn_when_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.call(ok) == "ok"

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(ValueError, match="downstream error"):
                cb.call(fail)
        with pytest.raises(CircuitOpenError):
            cb.call(ok)

    def test_does_not_open_before_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(2):
            with pytest.raises(ValueError, match="downstream error"):
                cb.call(fail)
        assert cb.call(ok) == "ok"

    def test_resets_to_closed_after_success_in_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0.0)
        with pytest.raises(ValueError, match="downstream error"):
            cb.call(fail)
        # recovery_timeout=0 → immediately enters HALF_OPEN on next call
        assert cb.call(ok) == "ok"
        assert cb.call(ok) == "ok"  # fully closed again

    def test_reopens_on_failure_in_half_open(self):
        # timeout=0 → HALF_OPEN; long timeout keeps it OPEN after re-failure
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0.0)
        with pytest.raises(ValueError, match="downstream error"):
            cb.call(fail)  # threshold hit → OPEN
        with pytest.raises(ValueError, match="downstream error"):
            cb.call(fail)  # recovery=0 → enters HALF_OPEN → fails → OPEN again
        # Force the recovery window to be long so the next call cannot reset
        cb.recovery_timeout_seconds = 9999.0
        with pytest.raises(CircuitOpenError):
            cb.call(ok)

    def test_propagates_original_exception(self):
        cb = CircuitBreaker(failure_threshold=5)
        with pytest.raises(ValueError, match="downstream error"):
            cb.call(fail)
