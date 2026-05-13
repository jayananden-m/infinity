from datetime import UTC, datetime, timedelta

import pytest

from src.domain.models.session import KeystrokeEvent
from src.domain.services.scoring import score_session


def ts(ms: int) -> KeystrokeEvent:
    """Shorthand: correct keystroke at given timestamp."""
    return KeystrokeEvent(key="a", timestamp_ms=ms, correct=True)


def err(key: str, ms: int) -> KeystrokeEvent:
    return KeystrokeEvent(key=key, timestamp_ms=ms, correct=False)


def ok(key: str, ms: int) -> KeystrokeEvent:
    return KeystrokeEvent(key=key, timestamp_ms=ms, correct=True)


def make_window(seconds: float) -> tuple[datetime, datetime]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return start, start + timedelta(seconds=seconds)


class TestWPM:
    def test_basic_wpm_calculation(self):
        # 10 correct chars over 24s → (10/5) / (24/60) = 5.0 WPM
        keystrokes = tuple(ok("a", i * 2400) for i in range(10))
        start, end = make_window(24.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.wpm == pytest.approx(5.0)

    def test_wpm_counts_only_correct_keystrokes(self):
        # 8 correct + 2 errors over 24s → (8/5) / (24/60) = 4.0 WPM
        keystrokes = (
            *[ok("a", i * 3000) for i in range(8)],
            err("x", 8000),
            err("x", 9000),
        )
        start, end = make_window(24.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.wpm == pytest.approx(4.0)

    def test_wpm_is_zero_for_empty_keystrokes(self):
        start, end = make_window(10.0)
        metrics = score_session((), start, end)
        assert metrics.wpm == 0.0

    def test_wpm_is_zero_when_duration_is_zero(self):
        keystrokes = (ok("a", 0),)
        start = datetime(2026, 1, 1, tzinfo=UTC)
        metrics = score_session(keystrokes, start, start)
        assert metrics.wpm == 0.0


class TestAccuracy:
    def test_perfect_accuracy(self):
        keystrokes = tuple(ok("a", i * 100) for i in range(10))
        start, end = make_window(10.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.accuracy == pytest.approx(1.0)

    def test_partial_accuracy(self):
        keystrokes = (
            *[ok("a", i * 100) for i in range(8)],
            err("x", 800),
            err("x", 900),
        )
        start, end = make_window(10.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.accuracy == pytest.approx(0.8)

    def test_zero_accuracy_all_errors(self):
        keystrokes = tuple(err("x", i * 100) for i in range(5))
        start, end = make_window(5.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.accuracy == pytest.approx(0.0)

    def test_accuracy_is_zero_for_empty_keystrokes(self):
        start, end = make_window(5.0)
        metrics = score_session((), start, end)
        assert metrics.accuracy == 0.0


class TestDuration:
    def test_duration_from_timestamps(self):
        start, end = make_window(60.0)
        metrics = score_session((ok("a", 0),), start, end)
        assert metrics.duration_seconds == pytest.approx(60.0)


class TestPerKeyStats:
    def test_per_key_stats_contains_typed_keys(self):
        keystrokes = (ok("a", 0), ok("b", 100), ok("a", 200))
        start, end = make_window(1.0)
        metrics = score_session(keystrokes, start, end)
        assert "a" in metrics.per_key_stats
        assert "b" in metrics.per_key_stats

    def test_per_key_avg_iki_ms(self):
        # "a" at t=0 (no predecessor), t=200 (IKI=100, prev was "b" at t=100)
        # avg IKI for "a" = 100ms
        keystrokes = (ok("a", 0), ok("b", 100), ok("a", 200))
        start, end = make_window(1.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.per_key_stats["a"]["avg_iki_ms"] == pytest.approx(100.0)

    def test_per_key_error_rate(self):
        # key "q": 3 total, 1 error → error_rate = 1/3
        keystrokes = (
            ok("q", 0),
            ok("q", 100),
            err("q", 200),
        )
        start, end = make_window(1.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.per_key_stats["q"]["error_rate"] == pytest.approx(1 / 3)

    def test_per_key_samples_count(self):
        keystrokes = (ok("z", 0), ok("z", 100), ok("z", 200))
        start, end = make_window(1.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.per_key_stats["z"]["samples"] == 3

    def test_first_keystroke_excluded_from_iki(self):
        # Only one keystroke — no IKI to compute, avg_iki_ms should be 0
        keystrokes = (ok("a", 0),)
        start, end = make_window(1.0)
        metrics = score_session(keystrokes, start, end)
        assert metrics.per_key_stats["a"]["avg_iki_ms"] == pytest.approx(0.0)
