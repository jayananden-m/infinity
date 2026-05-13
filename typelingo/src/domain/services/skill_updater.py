from src.domain.models.session import SessionMetrics
from src.domain.models.skill import KeyProfile
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile

_EMA_ALPHA = 0.3
_ACCURACY_MASTERY = 0.90
_ACCURACY_STRUGGLE = 0.70
_ACCURACY_ADVANCE = 0.85


def update_motor_skill(
    profile: MotorSkillProfile,
    metrics: SessionMetrics,
) -> MotorSkillProfile:
    new_wpm = _ema(metrics.wpm, profile.overall_wpm)
    new_accuracy = _ema(metrics.accuracy, profile.overall_accuracy)

    key_profiles = dict(profile.key_profiles)
    for key, stats in metrics.per_key_stats.items():
        existing = key_profiles.get(key)
        if existing is None:
            existing = KeyProfile.default()
        key_profiles[key] = existing.updated(
            new_avg_ms=stats["avg_iki_ms"],
            new_error_rate=stats["error_rate"],
        )

    return MotorSkillProfile(
        user_id=profile.user_id,
        overall_wpm=new_wpm,
        overall_accuracy=new_accuracy,
        key_profiles=key_profiles,
        bigram_stats=profile.bigram_stats,
    )


def update_cognitive_skill(
    profile: CognitiveSkillProfile,
    passage_grammar_tags: tuple[str, ...],
    metrics: SessionMetrics,
    challenged_grammar_level: int | None = None,
) -> CognitiveSkillProfile:
    weak = set(profile.weak_areas)
    strong = set(profile.strong_areas)

    if metrics.accuracy >= _ACCURACY_MASTERY:
        for tag in passage_grammar_tags:
            weak.discard(tag)
            strong.add(tag)
    elif metrics.accuracy < _ACCURACY_STRUGGLE:
        for tag in passage_grammar_tags:
            strong.discard(tag)
            weak.add(tag)

    new_level = profile.grammar_level
    if (
        challenged_grammar_level is not None
        and challenged_grammar_level == profile.stretch_grammar_level()
        and metrics.accuracy >= _ACCURACY_ADVANCE
    ):
        new_level = challenged_grammar_level

    return CognitiveSkillProfile(
        user_id=profile.user_id,
        grammar_level=new_level,
        vocabulary_tier=profile.vocabulary_tier,
        weak_areas=tuple(weak),
        strong_areas=tuple(strong),
    )


def _ema(new_value: float, current: float) -> float:
    return _EMA_ALPHA * new_value + (1 - _EMA_ALPHA) * current
