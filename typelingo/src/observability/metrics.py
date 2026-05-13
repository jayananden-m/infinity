"""Prometheus metrics definitions for TypeLingo."""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

__all__ = [
    "CONTENT_TYPE_LATEST",
    "HTTP_REQUEST_DURATION",
    "SESSIONS_ABANDONED",
    "SESSIONS_COMPLETED",
    "SESSIONS_STARTED",
    "WPM_HISTOGRAM",
    "generate_latest",
]

SESSIONS_STARTED: Counter = Counter(
    "typelingo_sessions_started_total",
    "Sessions started",
)
SESSIONS_COMPLETED: Counter = Counter(
    "typelingo_sessions_completed_total",
    "Sessions completed",
)
SESSIONS_ABANDONED: Counter = Counter(
    "typelingo_sessions_abandoned_total",
    "Sessions abandoned",
)
WPM_HISTOGRAM: Histogram = Histogram(
    "typelingo_session_wpm",
    "WPM distribution",
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 100, 120],
)
HTTP_REQUEST_DURATION: Histogram = Histogram(
    "typelingo_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path", "status"],
)
