"""Seed the database with starter passages."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.domain.models.passage import (
    CognitiveTarget,
    DifficultyVector,
    MotorTarget,
    Passage,
    PassageSource,
)
from src.infrastructure.database.repositories.passage_repository import (
    PostgresPassageRepository,
)

_PASSAGES = [
    (
        "The cat sat on the mat and looked at the sun. It was a warm day and the air smelled of grass.",
        DifficultyVector(
            motor=MotorTarget(
                target_wpm=30.0,
                key_focus=("t", "a"),
                bigram_focus=("th",),
                word_length_avg=3.5,
            ),
            cognitive=CognitiveTarget(
                grammar_level=1,
                vocabulary_tier=1,
                grammar_targets=("present_simple",),
                sentence_complexity=0.3,
            ),
        ),
        ("present_simple",),
    ),
    (
        "She walked to the market every morning to buy fresh bread. The baker always saved her the best loaf.",
        DifficultyVector(
            motor=MotorTarget(
                target_wpm=40.0,
                key_focus=("e", "r"),
                bigram_focus=("er", "ed"),
                word_length_avg=4.5,
            ),
            cognitive=CognitiveTarget(
                grammar_level=2,
                vocabulary_tier=2,
                grammar_targets=("past_simple",),
                sentence_complexity=0.4,
            ),
        ),
        ("past_simple",),
    ),
    (
        "Although the storm had passed, the streets were still flooded and no one could drive through the town centre.",
        DifficultyVector(
            motor=MotorTarget(
                target_wpm=50.0,
                key_focus=("s", "h"),
                bigram_focus=("th", "st"),
                word_length_avg=5.0,
            ),
            cognitive=CognitiveTarget(
                grammar_level=3,
                vocabulary_tier=3,
                grammar_targets=("past_perfect", "although"),
                sentence_complexity=0.6,
            ),
        ),
        ("past_perfect", "conjunctions"),
    ),
    (
        "By the time the engineers had reviewed the specifications, "
        "the project deadline had already been moved forward twice.",
        DifficultyVector(
            motor=MotorTarget(
                target_wpm=60.0,
                key_focus=("i", "n"),
                bigram_focus=("in", "on"),
                word_length_avg=6.0,
            ),
            cognitive=CognitiveTarget(
                grammar_level=4,
                vocabulary_tier=4,
                grammar_targets=("past_perfect", "passive_voice"),
                sentence_complexity=0.7,
            ),
        ),
        ("past_perfect", "passive_voice"),
    ),
    (
        "Quick brown foxes jump over lazy dogs. Pack my box with five dozen liquor jugs.",
        DifficultyVector(
            motor=MotorTarget(
                target_wpm=35.0,
                key_focus=("q", "z"),
                bigram_focus=("qu", "oz"),
                word_length_avg=4.0,
            ),
            cognitive=CognitiveTarget(
                grammar_level=1,
                vocabulary_tier=2,
                grammar_targets=("present_simple",),
                sentence_complexity=0.3,
            ),
        ),
        ("present_simple",),
    ),
]


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session, session.begin():
        repo = PostgresPassageRepository(session)
        for content, difficulty, tags in _PASSAGES:
            passage = Passage.create(content, difficulty, tags, PassageSource.SEED)
            await repo.save(passage)
            print(f"  seeded: {content[:60]}...")

    await engine.dispose()
    print(f"\n✓ {len(_PASSAGES)} passages seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
