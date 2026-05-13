import random
from collections.abc import Callable

from src.domain.interfaces.cache import IPassageCache
from src.domain.interfaces.repositories import IPassageRepository
from src.domain.models.passage import (
    CognitiveTarget,
    DifficultyVector,
    MotorTarget,
    Passage,
)
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile


class NoPassageAvailableError(Exception):
    pass


def _build_vector(motor: MotorSkillProfile, cognitive: CognitiveSkillProfile) -> DifficultyVector:
    return DifficultyVector(
        motor=MotorTarget(
            target_wpm=motor.stretch_wpm(),
            key_focus=tuple(motor.weakest_keys(n=2)),
            bigram_focus=tuple(motor.slowest_bigrams(n=2)),
            word_length_avg=5.0,
        ),
        cognitive=CognitiveTarget(
            grammar_level=cognitive.stretch_grammar_level(),
            vocabulary_tier=cognitive.vocabulary_tier,
            grammar_targets=tuple(cognitive.weakest_areas(n=2)),
            sentence_complexity=0.5,
        ),
    )


async def select_passage(
    motor: MotorSkillProfile,
    cognitive: CognitiveSkillProfile,
    repo: IPassageRepository,
    cache: IPassageCache | None = None,
    enqueue_generation: Callable[[DifficultyVector], None] | None = None,
) -> Passage:
    vector = _build_vector(motor, cognitive).quantize()
    key = vector.cache_key()

    candidates = await repo.find_by_difficulty(vector, limit=10)
    if candidates:
        passage = random.choice(candidates)  # noqa: S311
        if cache is not None:
            await cache.set(key, passage)
        return passage

    # DB empty — use cache as fallback before giving up
    if cache is not None:
        cached = await cache.get(key)
        if cached is not None:
            return cached

    if enqueue_generation is not None:
        enqueue_generation(vector)
    raise NoPassageAvailableError("no passages available — generation queued")
