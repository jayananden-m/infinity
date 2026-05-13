from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.domain.models.skill import BigramProfile, KeyProfile

COMFORT_ZONE_FACTOR = 0.9
STRETCH_FACTOR = 1.1
WEAK_KEY_THRESHOLD_MS = 150.0
WEAK_KEY_ERROR_THRESHOLD = 0.05


@dataclass(frozen=True)
class MotorSkillProfile:
    user_id: UUID
    overall_wpm: float
    overall_accuracy: float
    key_profiles: dict[str, KeyProfile]
    bigram_stats: dict[str, BigramProfile]
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def comfort_wpm(self) -> float:
        return self.overall_wpm * COMFORT_ZONE_FACTOR

    def stretch_wpm(self) -> float:
        return self.overall_wpm * STRETCH_FACTOR

    def weakest_keys(self, n: int) -> list[str]:
        """Return the n keys with highest error rate or slowest avg_ms."""
        scored = {
            key: profile.error_rate * 10 + profile.avg_ms / 100
            for key, profile in self.key_profiles.items()
            if profile.samples > 0
        }
        return sorted(scored, key=lambda k: scored[k], reverse=True)[:n]

    def slowest_bigrams(self, n: int) -> list[str]:
        scored = {bigram: profile.avg_ms for bigram, profile in self.bigram_stats.items() if profile.samples > 0}
        return sorted(scored, key=lambda k: scored[k], reverse=True)[:n]

    @classmethod
    def initial(cls, user_id: UUID) -> "MotorSkillProfile":
        return cls(
            user_id=user_id,
            overall_wpm=30.0,
            overall_accuracy=0.90,
            key_profiles={},
            bigram_stats={},
        )


@dataclass(frozen=True)
class CognitiveSkillProfile:
    user_id: UUID
    grammar_level: int
    vocabulary_tier: int
    weak_areas: tuple[str, ...]
    strong_areas: tuple[str, ...]
    cefr_level: str = "A1"
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def comfort_grammar_level(self) -> int:
        return max(1, self.grammar_level - 1)

    def stretch_grammar_level(self) -> int:
        return min(10, self.grammar_level + 1)

    def weakest_areas(self, n: int) -> list[str]:
        return list(self.weak_areas[:n])

    @classmethod
    def initial(cls, user_id: UUID) -> "CognitiveSkillProfile":
        return cls(
            user_id=user_id,
            grammar_level=1,
            vocabulary_tier=1,
            weak_areas=(),
            strong_areas=(),
            cefr_level="A1",
        )


_GUEST_TTL_DAYS = 7


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    display_name: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    is_guest: bool = False
    guest_expires_at: datetime | None = None

    @classmethod
    def create(cls, email: str, display_name: str, hashed_password: str) -> "User":
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            email=email,
            display_name=display_name,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def create_guest(cls) -> "User":
        now = datetime.now(UTC)
        uid = uuid4()
        return cls(
            id=uid,
            email=f"guest_{uid.hex}@guest.typelingo",
            display_name="guest",
            hashed_password="",
            is_guest=True,
            guest_expires_at=now + timedelta(days=_GUEST_TTL_DAYS),
            created_at=now,
            updated_at=now,
        )
