from datetime import UTC

import pytest

from src.domain.models.skill import BigramProfile, KeyProfile, SkillDelta


class TestKeyProfile:
    def test_default_has_zero_samples(self):
        profile = KeyProfile.default()
        assert profile.samples == 0

    def test_default_has_zero_error_rate(self):
        profile = KeyProfile.default()
        assert profile.error_rate == 0.0

    def test_updated_increases_sample_count(self):
        profile = KeyProfile.default()
        updated = profile.updated(new_avg_ms=80.0, new_error_rate=0.0)
        assert updated.samples == 1

    def test_updated_applies_ema_to_avg_ms(self):
        profile = KeyProfile(avg_ms=100.0, error_rate=0.0, samples=10)
        updated = profile.updated(new_avg_ms=50.0, new_error_rate=0.0)
        # EMA: 0.3 * 50 + 0.7 * 100 = 85.0
        assert updated.avg_ms == pytest.approx(85.0)

    def test_updated_applies_ema_to_error_rate(self):
        profile = KeyProfile(avg_ms=100.0, error_rate=0.0, samples=10)
        updated = profile.updated(new_avg_ms=100.0, new_error_rate=1.0)
        # EMA: 0.3 * 1.0 + 0.7 * 0.0 = 0.3
        assert updated.error_rate == pytest.approx(0.3)

    def test_updated_returns_new_instance(self):
        profile = KeyProfile.default()
        updated = profile.updated(new_avg_ms=80.0, new_error_rate=0.0)
        assert updated is not profile
        assert profile.samples == 0  # original unchanged

    def test_is_immutable(self):
        profile = KeyProfile.default()
        with pytest.raises(AttributeError):
            profile.avg_ms = 50.0  # type: ignore[misc]


class TestBigramProfile:
    def test_default_has_zero_samples(self):
        profile = BigramProfile.default()
        assert profile.samples == 0

    def test_updated_applies_ema(self):
        profile = BigramProfile(avg_ms=200.0, samples=5)
        updated = profile.updated(new_avg_ms=100.0)
        # EMA: 0.3 * 100 + 0.7 * 200 = 170.0
        assert updated.avg_ms == pytest.approx(170.0)

    def test_updated_returns_new_instance(self):
        profile = BigramProfile.default()
        updated = profile.updated(new_avg_ms=100.0)
        assert updated is not profile
        assert profile.samples == 0


class TestSkillDelta:
    def test_has_utc_timestamp(self):
        delta = SkillDelta(wpm_delta=1.5, accuracy_delta=0.01, grammar_level_delta=0)
        assert delta.updated_at.tzinfo is UTC
