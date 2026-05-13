from uuid import uuid4

from src.domain.models.skill import AdaptationStrategy
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.adaptation import choose_strategy

_USER = uuid4()


def motor(wpm: float) -> MotorSkillProfile:
    return MotorSkillProfile(
        user_id=_USER,
        overall_wpm=wpm,
        overall_accuracy=0.90,
        key_profiles={},
        bigram_stats={},
    )


def cognitive(level: int) -> CognitiveSkillProfile:
    return CognitiveSkillProfile(
        user_id=_USER,
        grammar_level=level,
        vocabulary_tier=level,
        weak_areas=(),
        strong_areas=(),
    )


class TestChooseStrategy:
    def test_slow_typist_gets_motor_challenge(self):
        # wpm=20 < grammar_level=3 * 10=30 → CHALLENGE_MOTOR
        result = choose_strategy(motor(20.0), cognitive(3))
        assert result == AdaptationStrategy.CHALLENGE_MOTOR

    def test_fast_typist_low_grammar_gets_cognitive_challenge(self):
        # wpm=80 > grammar_level=1 * 10=10 → CHALLENGE_COGNITIVE
        result = choose_strategy(motor(80.0), cognitive(1))
        assert result == AdaptationStrategy.CHALLENGE_COGNITIVE

    def test_balanced_skills_get_balanced_advance(self):
        # wpm=50, grammar_level=5 → 50 == 5 * 10 → BALANCED_ADVANCE
        result = choose_strategy(motor(50.0), cognitive(5))
        assert result == AdaptationStrategy.BALANCED_ADVANCE

    def test_slightly_ahead_on_motor_is_balanced(self):
        # wpm=55, grammar_level=5 * 10=50 → within tolerance → BALANCED_ADVANCE
        result = choose_strategy(motor(55.0), cognitive(5))
        assert result == AdaptationStrategy.BALANCED_ADVANCE
