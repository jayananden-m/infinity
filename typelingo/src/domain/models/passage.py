from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PassageSource(Enum):
    LLM = "llm"
    SEED = "seed"
    CACHE = "cache"


@dataclass(frozen=True)
class MotorTarget:
    target_wpm: float
    key_focus: tuple[str, ...]
    bigram_focus: tuple[str, ...]
    word_length_avg: float

    def quantize(self) -> "MotorTarget":
        """Round to discrete levels to increase cache hit rate."""
        return MotorTarget(
            target_wpm=round(self.target_wpm / 5) * 5,
            key_focus=self.key_focus,
            bigram_focus=self.bigram_focus,
            word_length_avg=round(self.word_length_avg),
        )


@dataclass(frozen=True)
class CognitiveTarget:
    grammar_level: int
    vocabulary_tier: int
    grammar_targets: tuple[str, ...]
    sentence_complexity: float

    def quantize(self) -> "CognitiveTarget":
        return CognitiveTarget(
            grammar_level=self.grammar_level,
            vocabulary_tier=self.vocabulary_tier,
            grammar_targets=self.grammar_targets,
            sentence_complexity=round(self.sentence_complexity * 2) / 2,
        )


@dataclass(frozen=True)
class DifficultyVector:
    motor: MotorTarget
    cognitive: CognitiveTarget

    def quantize(self) -> "DifficultyVector":
        """Quantize all dimensions to maximize Redis cache hit rate."""
        return DifficultyVector(
            motor=self.motor.quantize(),
            cognitive=self.cognitive.quantize(),
        )

    def cache_key(self) -> str:
        q = self.quantize()
        keys = "_".join(sorted(q.motor.key_focus))
        return (
            f"passage"
            f":wpm{int(q.motor.target_wpm)}"
            f":g{q.cognitive.grammar_level}"
            f":v{q.cognitive.vocabulary_tier}"
            f":keys_{keys}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "motor": {
                "target_wpm": self.motor.target_wpm,
                "key_focus": list(self.motor.key_focus),
                "bigram_focus": list(self.motor.bigram_focus),
                "word_length_avg": self.motor.word_length_avg,
            },
            "cognitive": {
                "grammar_level": self.cognitive.grammar_level,
                "vocabulary_tier": self.cognitive.vocabulary_tier,
                "grammar_targets": list(self.cognitive.grammar_targets),
                "sentence_complexity": self.cognitive.sentence_complexity,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DifficultyVector":
        m = data["motor"]
        c = data["cognitive"]
        return cls(
            motor=MotorTarget(
                target_wpm=m["target_wpm"],
                key_focus=tuple(m["key_focus"]),
                bigram_focus=tuple(m["bigram_focus"]),
                word_length_avg=m["word_length_avg"],
            ),
            cognitive=CognitiveTarget(
                grammar_level=c["grammar_level"],
                vocabulary_tier=c["vocabulary_tier"],
                grammar_targets=tuple(c["grammar_targets"]),
                sentence_complexity=c["sentence_complexity"],
            ),
        )


@dataclass(frozen=True)
class Passage:
    id: UUID
    content: str
    difficulty: DifficultyVector
    grammar_tags: tuple[str, ...]
    word_count: int
    source: PassageSource
    created_at: datetime

    @classmethod
    def create(
        cls,
        content: str,
        difficulty: DifficultyVector,
        grammar_tags: tuple[str, ...],
        source: PassageSource,
    ) -> "Passage":
        return cls(
            id=uuid4(),
            content=content,
            difficulty=difficulty,
            grammar_tags=grammar_tags,
            word_count=len(content.split()),
            source=source,
            created_at=datetime.now(UTC),
        )
