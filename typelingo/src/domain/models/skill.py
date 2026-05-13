from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class AdaptationStrategy(Enum):
    CHALLENGE_MOTOR = "challenge_motor"
    CHALLENGE_COGNITIVE = "challenge_cognitive"
    BALANCED_ADVANCE = "balanced_advance"


@dataclass(frozen=True)
class KeyProfile:
    avg_ms: float
    error_rate: float
    samples: int

    @classmethod
    def default(cls) -> "KeyProfile":
        return cls(avg_ms=100.0, error_rate=0.0, samples=0)

    def updated(self, new_avg_ms: float, new_error_rate: float) -> "KeyProfile":
        """Return a new KeyProfile with EMA-updated stats. alpha=0.3"""
        alpha = 0.3
        return KeyProfile(
            avg_ms=alpha * new_avg_ms + (1 - alpha) * self.avg_ms,
            error_rate=alpha * new_error_rate + (1 - alpha) * self.error_rate,
            samples=self.samples + 1,
        )


@dataclass(frozen=True)
class BigramProfile:
    avg_ms: float
    samples: int

    @classmethod
    def default(cls) -> "BigramProfile":
        return cls(avg_ms=150.0, samples=0)

    def updated(self, new_avg_ms: float) -> "BigramProfile":
        alpha = 0.3
        return BigramProfile(
            avg_ms=alpha * new_avg_ms + (1 - alpha) * self.avg_ms,
            samples=self.samples + 1,
        )


@dataclass(frozen=True)
class SkillDelta:
    """Represents the change in a skill dimension after a session."""

    wpm_delta: float
    accuracy_delta: float
    grammar_level_delta: int
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
