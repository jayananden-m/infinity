from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4


class SessionStatus(Enum):
    STARTED = "started"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class KeystrokeEvent:
    key: str
    timestamp_ms: int
    correct: bool


@dataclass(frozen=True)
class SessionMetrics:
    wpm: float
    accuracy: float
    duration_seconds: float
    per_key_stats: dict[str, dict[str, float]]


@dataclass(frozen=True)
class TypingSession:
    id: UUID
    user_id: UUID
    passage_id: UUID
    status: SessionStatus
    started_at: datetime
    keystrokes: tuple[KeystrokeEvent, ...]
    completed_at: datetime | None = None
    metrics: SessionMetrics | None = None

    @classmethod
    def start(cls, user_id: UUID, passage_id: UUID) -> "TypingSession":
        return cls(
            id=uuid4(),
            user_id=user_id,
            passage_id=passage_id,
            status=SessionStatus.STARTED,
            started_at=datetime.now(UTC),
            keystrokes=(),
        )

    def complete(self, keystrokes: tuple[KeystrokeEvent, ...], metrics: SessionMetrics) -> "TypingSession":
        if self.status != SessionStatus.STARTED:
            raise ValueError(f"Cannot complete a session with status {self.status.value}")
        return TypingSession(
            id=self.id,
            user_id=self.user_id,
            passage_id=self.passage_id,
            status=SessionStatus.COMPLETED,
            started_at=self.started_at,
            keystrokes=keystrokes,
            completed_at=datetime.now(UTC),
            metrics=metrics,
        )

    def abandon(self) -> "TypingSession":
        if self.status != SessionStatus.STARTED:
            raise ValueError(f"Cannot abandon a session with status {self.status.value}")
        return TypingSession(
            id=self.id,
            user_id=self.user_id,
            passage_id=self.passage_id,
            status=SessionStatus.ABANDONED,
            started_at=self.started_at,
            keystrokes=self.keystrokes,
            completed_at=datetime.now(UTC),
        )
