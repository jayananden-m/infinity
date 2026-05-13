from uuid import uuid4

import pytest

from src.domain.models.session import SessionMetrics
from src.domain.models.skill import KeyProfile
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.skill_updater import update_cognitive_skill, update_motor_skill

_USER = uuid4()


def make_motor(**kwargs) -> MotorSkillProfile:  # type: ignore[no-untyped-def]
    defaults = dict(
        user_id=_USER,
        overall_wpm=40.0,
        overall_accuracy=0.90,
        key_profiles={},
        bigram_stats={},
    )
    defaults.update(kwargs)
    return MotorSkillProfile(**defaults)  # type: ignore[arg-type]


def make_cognitive(**kwargs) -> CognitiveSkillProfile:  # type: ignore[no-untyped-def]
    defaults = dict(
        user_id=_USER,
        grammar_level=3,
        vocabulary_tier=3,
        weak_areas=("past_perfect",),
        strong_areas=(),
    )
    defaults.update(kwargs)
    return CognitiveSkillProfile(**defaults)  # type: ignore[arg-type]


def make_metrics(**kwargs) -> SessionMetrics:  # type: ignore[no-untyped-def]
    defaults = dict(
        wpm=50.0,
        accuracy=0.92,
        duration_seconds=60.0,
        per_key_stats={},
    )
    defaults.update(kwargs)
    return SessionMetrics(**defaults)  # type: ignore[arg-type]


class TestUpdateMotorSkill:
    def test_wpm_updated_with_ema(self):
        profile = make_motor(overall_wpm=40.0)
        metrics = make_metrics(wpm=60.0)
        updated = update_motor_skill(profile, metrics)
        # EMA: 0.3 * 60 + 0.7 * 40 = 46.0
        assert updated.overall_wpm == pytest.approx(46.0)

    def test_accuracy_updated_with_ema(self):
        profile = make_motor(overall_accuracy=0.90)
        metrics = make_metrics(accuracy=1.0)
        updated = update_motor_skill(profile, metrics)
        # EMA: 0.3 * 1.0 + 0.7 * 0.90 = 0.93
        assert updated.overall_accuracy == pytest.approx(0.93)

    def test_returns_new_instance(self):
        profile = make_motor()
        updated = update_motor_skill(profile, make_metrics())
        assert updated is not profile

    def test_per_key_stats_create_new_key_profiles(self):
        profile = make_motor(key_profiles={})
        metrics = make_metrics(
            per_key_stats={
                "a": {"avg_iki_ms": 80.0, "error_rate": 0.05, "samples": 10.0},
            }
        )
        updated = update_motor_skill(profile, metrics)
        assert "a" in updated.key_profiles

    def test_per_key_stats_update_existing_key_profiles(self):
        existing = KeyProfile(avg_ms=100.0, error_rate=0.10, samples=20)
        profile = make_motor(key_profiles={"q": existing})
        metrics = make_metrics(
            per_key_stats={
                "q": {"avg_iki_ms": 50.0, "error_rate": 0.0, "samples": 5.0},
            }
        )
        updated = update_motor_skill(profile, metrics)
        # EMA on avg_ms: 0.3 * 50 + 0.7 * 100 = 85.0
        assert updated.key_profiles["q"].avg_ms == pytest.approx(85.0)

    def test_user_id_preserved(self):
        profile = make_motor()
        updated = update_motor_skill(profile, make_metrics())
        assert updated.user_id == profile.user_id


class TestUpdateCognitiveSkill:
    def test_high_accuracy_moves_tag_to_strong(self):
        profile = make_cognitive(weak_areas=("past_perfect",), strong_areas=())
        updated = update_cognitive_skill(profile, ("past_perfect",), make_metrics(accuracy=0.92))
        assert "past_perfect" not in updated.weak_areas
        assert "past_perfect" in updated.strong_areas

    def test_low_accuracy_moves_tag_to_weak(self):
        profile = make_cognitive(weak_areas=(), strong_areas=("present_simple",))
        updated = update_cognitive_skill(profile, ("present_simple",), make_metrics(accuracy=0.65))
        assert "present_simple" in updated.weak_areas
        assert "present_simple" not in updated.strong_areas

    def test_mid_accuracy_leaves_areas_unchanged(self):
        profile = make_cognitive(weak_areas=("past_perfect",), strong_areas=())
        updated = update_cognitive_skill(profile, ("past_perfect",), make_metrics(accuracy=0.80))
        assert updated.weak_areas == profile.weak_areas
        assert updated.strong_areas == profile.strong_areas

    def test_grammar_level_advances_on_high_accuracy_at_stretch(self):
        profile = make_cognitive(grammar_level=3)
        # stretch level = 4; passage was at stretch level
        updated = update_cognitive_skill(
            profile,
            (),
            make_metrics(accuracy=0.88),
            challenged_grammar_level=4,
        )
        assert updated.grammar_level == 4

    def test_grammar_level_does_not_advance_below_threshold(self):
        profile = make_cognitive(grammar_level=3)
        updated = update_cognitive_skill(
            profile,
            (),
            make_metrics(accuracy=0.80),
            challenged_grammar_level=4,
        )
        assert updated.grammar_level == 3

    def test_returns_new_instance(self):
        profile = make_cognitive()
        updated = update_cognitive_skill(profile, (), make_metrics())
        assert updated is not profile
