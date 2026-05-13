from uuid import uuid4

import pytest

from src.domain.models.passage import Passage, PassageSource
from src.domain.models.user import CognitiveSkillProfile, MotorSkillProfile
from src.domain.services.passage_selector import NoPassageAvailableError, select_passage
from tests.fakes.repositories import InMemoryPassageRepository
from tests.unit.domain.test_passage import make_vector


def make_motor(user_id=None, wpm: float = 40.0) -> MotorSkillProfile:
    uid = user_id or uuid4()
    return MotorSkillProfile.initial(uid)


def make_cognitive(user_id=None) -> CognitiveSkillProfile:
    uid = user_id or uuid4()
    return CognitiveSkillProfile.initial(uid)


class TestSelectPassage:
    @pytest.mark.asyncio()
    async def test_returns_passage_when_available(self):
        repo = InMemoryPassageRepository()
        passage = Passage.create("hello world", make_vector(), (), PassageSource.SEED)
        await repo.save(passage)

        result = await select_passage(make_motor(), make_cognitive(), repo)
        assert result == passage

    @pytest.mark.asyncio()
    async def test_raises_when_no_passages(self):
        repo = InMemoryPassageRepository()
        with pytest.raises(NoPassageAvailableError):
            await select_passage(make_motor(), make_cognitive(), repo)

    @pytest.mark.asyncio()
    async def test_returns_one_passage(self):
        repo = InMemoryPassageRepository()
        for i in range(3):
            p = Passage.create(f"passage {i}", make_vector(), (), PassageSource.SEED)
            await repo.save(p)

        result = await select_passage(make_motor(), make_cognitive(), repo)
        assert isinstance(result, Passage)
