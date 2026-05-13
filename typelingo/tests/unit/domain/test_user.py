from datetime import UTC
from uuid import UUID, uuid4

import pytest

from src.domain.models.skill import BigramProfile, KeyProfile
from src.domain.models.user import (
    COMFORT_ZONE_FACTOR,
    STRETCH_FACTOR,
    CognitiveSkillProfile,
    MotorSkillProfile,
    User,
)


class TestUser:
    def test_create_generates_uuid(self):
        user = User.create("test@example.com", "Tester", "hashed")
        assert isinstance(user.id, UUID)

    def test_create_two_users_have_different_ids(self):
        a = User.create("a@example.com", "A", "hashed")
        b = User.create("b@example.com", "B", "hashed")
        assert a.id != b.id

    def test_create_timestamps_are_utc(self):
        user = User.create("test@example.com", "Tester", "hashed")
        assert user.created_at.tzinfo is UTC
        assert user.updated_at.tzinfo is UTC

    def test_is_immutable(self):
        user = User.create("test@example.com", "Tester", "hashed")
        with pytest.raises(AttributeError):
            user.email = "other@example.com"  # type: ignore[misc]


class TestMotorSkillProfile:
    def test_initial_sets_sensible_defaults(self):
        profile = MotorSkillProfile.initial(uuid4())
        assert profile.overall_wpm == 30.0
        assert profile.overall_accuracy == 0.90
        assert profile.key_profiles == {}

    def test_comfort_wpm_is_below_overall(self):
        profile = MotorSkillProfile.initial(uuid4())
        assert profile.comfort_wpm() == profile.overall_wpm * COMFORT_ZONE_FACTOR

    def test_stretch_wpm_is_above_overall(self):
        profile = MotorSkillProfile.initial(uuid4())
        assert profile.stretch_wpm() == profile.overall_wpm * STRETCH_FACTOR

    def test_weakest_keys_returns_n_keys(self):
        profile = MotorSkillProfile(
            user_id=uuid4(),
            overall_wpm=50.0,
            overall_accuracy=0.95,
            key_profiles={
                "q": KeyProfile(avg_ms=200.0, error_rate=0.15, samples=10),
                "z": KeyProfile(avg_ms=180.0, error_rate=0.10, samples=10),
                "a": KeyProfile(avg_ms=80.0, error_rate=0.01, samples=100),
            },
            bigram_stats={},
        )
        weak = profile.weakest_keys(n=2)
        assert len(weak) == 2
        assert "q" in weak
        assert "z" in weak

    def test_weakest_keys_excludes_zero_sample_keys(self):
        profile = MotorSkillProfile(
            user_id=uuid4(),
            overall_wpm=50.0,
            overall_accuracy=0.95,
            key_profiles={
                "q": KeyProfile(avg_ms=200.0, error_rate=0.15, samples=0),
                "a": KeyProfile(avg_ms=80.0, error_rate=0.01, samples=100),
            },
            bigram_stats={},
        )
        weak = profile.weakest_keys(n=2)
        assert "q" not in weak

    def test_slowest_bigrams_returns_n_bigrams(self):
        profile = MotorSkillProfile(
            user_id=uuid4(),
            overall_wpm=50.0,
            overall_accuracy=0.95,
            key_profiles={},
            bigram_stats={
                "qu": BigramProfile(avg_ms=300.0, samples=5),
                "th": BigramProfile(avg_ms=90.0, samples=50),
            },
        )
        slow = profile.slowest_bigrams(n=1)
        assert slow == ["qu"]


class TestCognitiveSkillProfile:
    def test_initial_starts_at_level_one(self):
        profile = CognitiveSkillProfile.initial(uuid4())
        assert profile.grammar_level == 1
        assert profile.vocabulary_tier == 1

    def test_comfort_level_is_one_below(self):
        profile = CognitiveSkillProfile(
            user_id=uuid4(),
            grammar_level=5,
            vocabulary_tier=4,
            weak_areas=(),
            strong_areas=(),
        )
        assert profile.comfort_grammar_level() == 4

    def test_comfort_level_never_goes_below_one(self):
        profile = CognitiveSkillProfile.initial(uuid4())
        assert profile.comfort_grammar_level() == 1

    def test_stretch_level_is_one_above(self):
        profile = CognitiveSkillProfile(
            user_id=uuid4(),
            grammar_level=5,
            vocabulary_tier=4,
            weak_areas=(),
            strong_areas=(),
        )
        assert profile.stretch_grammar_level() == 6

    def test_stretch_level_never_exceeds_ten(self):
        profile = CognitiveSkillProfile(
            user_id=uuid4(),
            grammar_level=10,
            vocabulary_tier=10,
            weak_areas=(),
            strong_areas=(),
        )
        assert profile.stretch_grammar_level() == 10

    def test_weakest_areas_returns_n_items(self):
        profile = CognitiveSkillProfile(
            user_id=uuid4(),
            grammar_level=3,
            vocabulary_tier=3,
            weak_areas=("past_perfect", "conditionals", "subjunctive"),
            strong_areas=(),
        )
        assert profile.weakest_areas(n=2) == ["past_perfect", "conditionals"]
