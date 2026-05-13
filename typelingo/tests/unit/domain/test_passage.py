from datetime import UTC

import pytest

from src.domain.models.passage import (
    CognitiveTarget,
    DifficultyVector,
    MotorTarget,
    Passage,
    PassageSource,
)


def make_motor_target(**kwargs: object) -> MotorTarget:
    defaults = dict(
        target_wpm=47.3,
        key_focus=("q", "z"),
        bigram_focus=("qu",),
        word_length_avg=5.2,
    )
    defaults.update(kwargs)
    return MotorTarget(**defaults)  # type: ignore[arg-type]


def make_cognitive_target(**kwargs: object) -> CognitiveTarget:
    defaults = dict(
        grammar_level=3,
        vocabulary_tier=4,
        grammar_targets=("past_simple",),
        sentence_complexity=0.7,
    )
    defaults.update(kwargs)
    return CognitiveTarget(**defaults)  # type: ignore[arg-type]


def make_vector(**kwargs: object) -> DifficultyVector:
    return DifficultyVector(
        motor=make_motor_target(),
        cognitive=make_cognitive_target(),
        **kwargs,  # type: ignore[arg-type]
    )


class TestMotorTarget:
    def test_quantize_rounds_wpm_to_nearest_five(self):
        target = make_motor_target(target_wpm=47.3)
        assert target.quantize().target_wpm == 45.0

    def test_quantize_rounds_up(self):
        target = make_motor_target(target_wpm=48.0)
        assert target.quantize().target_wpm == 50.0

    def test_quantize_returns_new_instance(self):
        target = make_motor_target()
        assert target.quantize() is not target


class TestCognitiveTarget:
    def test_quantize_rounds_complexity_to_half(self):
        target = make_cognitive_target(sentence_complexity=0.7)
        assert target.quantize().sentence_complexity == 0.5

    def test_quantize_preserves_grammar_level(self):
        target = make_cognitive_target(grammar_level=3)
        assert target.quantize().grammar_level == 3


class TestDifficultyVector:
    def test_cache_key_is_deterministic(self):
        vector = make_vector()
        assert vector.cache_key() == vector.cache_key()

    def test_cache_key_reflects_wpm(self):
        vector = make_vector()
        assert "wpm45" in vector.cache_key()

    def test_cache_key_reflects_grammar_level(self):
        vector = make_vector()
        assert "g3" in vector.cache_key()

    def test_cache_key_sorts_keys_for_consistency(self):
        v1 = DifficultyVector(
            motor=make_motor_target(key_focus=("q", "z")),
            cognitive=make_cognitive_target(),
        )
        v2 = DifficultyVector(
            motor=make_motor_target(key_focus=("z", "q")),
            cognitive=make_cognitive_target(),
        )
        assert v1.cache_key() == v2.cache_key()

    def test_quantize_increases_cache_hit_rate(self):
        v1 = DifficultyVector(
            motor=make_motor_target(target_wpm=47.3),
            cognitive=make_cognitive_target(),
        )
        v2 = DifficultyVector(
            motor=make_motor_target(target_wpm=46.1),
            cognitive=make_cognitive_target(),
        )
        assert v1.quantize().cache_key() == v2.quantize().cache_key()


class TestPassage:
    def test_create_counts_words(self):
        passage = Passage.create(
            content="the quick brown fox jumps",
            difficulty=make_vector(),
            grammar_tags=("present_simple",),
            source=PassageSource.SEED,
        )
        assert passage.word_count == 5

    def test_create_sets_utc_timestamp(self):
        passage = Passage.create(
            content="hello world",
            difficulty=make_vector(),
            grammar_tags=(),
            source=PassageSource.SEED,
        )
        assert passage.created_at.tzinfo is UTC

    def test_create_generates_unique_ids(self):
        a = Passage.create("hello", make_vector(), (), PassageSource.SEED)
        b = Passage.create("hello", make_vector(), (), PassageSource.SEED)
        assert a.id != b.id

    def test_is_immutable(self):
        passage = Passage.create("hello", make_vector(), (), PassageSource.SEED)
        with pytest.raises(AttributeError):
            passage.content = "changed"  # type: ignore[misc]
