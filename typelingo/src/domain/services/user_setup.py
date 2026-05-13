"""User profile initialisation service.

Creates motor and cognitive skill profiles for a user if they do not
already exist in the respective repositories.  This keeps the API
layer free of domain construction details.
"""

from uuid import UUID

from src.domain.interfaces.repositories import (
    ICognitiveSkillRepository,
    IMotorSkillRepository,
)
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile


async def initialise_user_profiles(
    user_id: UUID,
    motor_repo: IMotorSkillRepository,
    cognitive_repo: ICognitiveSkillRepository,
) -> tuple[MotorSkillProfile, CognitiveSkillProfile]:
    """Return (motor, cognitive) profiles for *user_id*.

    Profiles that do not yet exist are created with ``initial()`` defaults
    and persisted before being returned.
    """
    motor = await motor_repo.get_by_user(user_id)
    if motor is None:
        motor = MotorSkillProfile.initial(user_id)
        await motor_repo.save(motor)

    cognitive = await cognitive_repo.get_by_user(user_id)
    if cognitive is None:
        cognitive = CognitiveSkillProfile.initial(user_id)
        await cognitive_repo.save(cognitive)

    return motor, cognitive
