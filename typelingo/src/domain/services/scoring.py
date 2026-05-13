from collections import defaultdict
from datetime import datetime

from src.domain.models.session import KeystrokeEvent, SessionMetrics

_CHARS_PER_WORD = 5


def score_session(
    keystrokes: tuple[KeystrokeEvent, ...],
    started_at: datetime,
    completed_at: datetime,
) -> SessionMetrics:
    duration_seconds = (completed_at - started_at).total_seconds()
    return SessionMetrics(
        wpm=_compute_wpm(keystrokes, duration_seconds),
        accuracy=_compute_accuracy(keystrokes),
        duration_seconds=duration_seconds,
        per_key_stats=_compute_per_key_stats(keystrokes),
    )


def _compute_wpm(keystrokes: tuple[KeystrokeEvent, ...], duration_seconds: float) -> float:
    if not keystrokes or duration_seconds <= 0:
        return 0.0
    correct_chars = sum(1 for k in keystrokes if k.correct)
    duration_minutes = duration_seconds / 60
    return (correct_chars / _CHARS_PER_WORD) / duration_minutes


def _compute_accuracy(keystrokes: tuple[KeystrokeEvent, ...]) -> float:
    if not keystrokes:
        return 0.0
    return sum(1 for k in keystrokes if k.correct) / len(keystrokes)


def _compute_per_key_stats(
    keystrokes: tuple[KeystrokeEvent, ...],
) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"samples": 0.0, "errors": 0.0, "iki_total_ms": 0.0, "iki_count": 0.0}
    )

    for i, event in enumerate(keystrokes):
        stats = totals[event.key]
        stats["samples"] += 1
        if not event.correct:
            stats["errors"] += 1
        if i > 0:
            iki = event.timestamp_ms - keystrokes[i - 1].timestamp_ms
            stats["iki_total_ms"] += iki
            stats["iki_count"] += 1

    return {
        key: {
            "samples": s["samples"],
            "error_rate": s["errors"] / s["samples"],
            "avg_iki_ms": (s["iki_total_ms"] / s["iki_count"] if s["iki_count"] > 0 else 0.0),
        }
        for key, s in totals.items()
    }
