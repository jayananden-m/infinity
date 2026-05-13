from src.domain.models.skill import AdaptationStrategy
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile

_WPM_PER_GRAMMAR_LEVEL = 10
_BALANCE_TOLERANCE = 0.15


def choose_strategy(
    motor: MotorSkillProfile,
    cognitive: CognitiveSkillProfile,
) -> AdaptationStrategy:
    expected_wpm = cognitive.grammar_level * _WPM_PER_GRAMMAR_LEVEL
    ratio = motor.overall_wpm / expected_wpm if expected_wpm > 0 else 1.0

    if ratio < (1.0 - _BALANCE_TOLERANCE):
        return AdaptationStrategy.CHALLENGE_MOTOR
    if ratio > (1.0 + _BALANCE_TOLERANCE):
        return AdaptationStrategy.CHALLENGE_COGNITIVE
    return AdaptationStrategy.BALANCED_ADVANCE
