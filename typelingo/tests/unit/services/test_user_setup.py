"""Unit tests for domain/services/user_setup.py."""

from uuid import uuid4

import pytest

from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.user_setup import initialise_user_profiles
from tests.fakes.repositories import (
    InMemoryCognitiveSkillRepository,
    InMemoryMotorSkillRepository,
)


@pytest.mark.asyncio()
async def test_creates_profiles_when_missing() -> None:
    user_id = uuid4()
    motor_repo = InMemoryMotorSkillRepository()
    cognitive_repo = InMemoryCognitiveSkillRepository()

    motor, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)

    assert motor.user_id == user_id
    assert motor.overall_wpm == 30.0
    assert cognitive.user_id == user_id
    assert cognitive.grammar_level == 1

    # Profiles should be persisted
    assert await motor_repo.get_by_user(user_id) == motor
    assert await cognitive_repo.get_by_user(user_id) == cognitive


@pytest.mark.asyncio()
async def test_returns_existing_profiles_without_overwriting() -> None:
    user_id = uuid4()
    motor_repo = InMemoryMotorSkillRepository()
    cognitive_repo = InMemoryCognitiveSkillRepository()

    existing_motor = MotorSkillProfile(
        user_id=user_id,
        overall_wpm=75.0,
        overall_accuracy=0.98,
        key_profiles={},
        bigram_stats={},
    )
    existing_cognitive = CognitiveSkillProfile(
        user_id=user_id,
        grammar_level=5,
        vocabulary_tier=3,
        weak_areas=(),
        strong_areas=(),
    )
    await motor_repo.save(existing_motor)
    await cognitive_repo.save(existing_cognitive)

    motor, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)

    assert motor.overall_wpm == 75.0
    assert cognitive.grammar_level == 5


@pytest.mark.asyncio()
async def test_creates_cognitive_even_when_motor_exists() -> None:
    user_id = uuid4()
    motor_repo = InMemoryMotorSkillRepository()
    cognitive_repo = InMemoryCognitiveSkillRepository()

    existing_motor = MotorSkillProfile.initial(user_id)
    await motor_repo.save(existing_motor)

    motor, cognitive = await initialise_user_profiles(user_id, motor_repo, cognitive_repo)

    assert motor == existing_motor
    assert cognitive.user_id == user_id
    assert await cognitive_repo.get_by_user(user_id) == cognitive
