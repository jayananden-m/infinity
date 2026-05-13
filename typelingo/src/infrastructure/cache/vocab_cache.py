import json

from redis.asyncio import Redis

from src.domain.models.vocab import AssessmentQuestion, VocabWord

_VOCAB_POOL_KEY = "vocab_pool:{level}"
_ASSESS_KEY = "assess_questions:{level}"
_POOL_TTL = 7 * 24 * 3600
_ASSESS_TTL = 7 * 24 * 3600


class RedisVocabCache:
    def __init__(self, redis_url: str) -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)

    async def pop_vocab_word(self, level: str) -> VocabWord | None:
        raw: str | None = await self._redis.lpop(_VOCAB_POOL_KEY.format(level=level))  # type: ignore[misc]
        return _word_from_json(raw) if raw else None

    async def push_vocab_words(self, level: str, words: list[VocabWord]) -> None:
        key = _VOCAB_POOL_KEY.format(level=level)
        if words:
            await self._redis.rpush(key, *[_word_to_json(w) for w in words])  # type: ignore[misc]
            await self._redis.expire(key, _POOL_TTL)

    async def pool_size(self, level: str) -> int:
        size: int = await self._redis.llen(_VOCAB_POOL_KEY.format(level=level))  # type: ignore[misc]
        return size

    async def get_assess_questions(self, level: str) -> list[AssessmentQuestion] | None:
        raw = await self._redis.get(_ASSESS_KEY.format(level=level))
        if raw is None:
            return None
        return [_question_from_dict(d) for d in json.loads(raw)]

    async def set_assess_questions(self, level: str, questions: list[AssessmentQuestion]) -> None:
        serialized = json.dumps([_question_to_dict(q) for q in questions])
        await self._redis.set(_ASSESS_KEY.format(level=level), serialized, ex=_ASSESS_TTL)

    async def close(self) -> None:
        await self._redis.aclose()


def _word_to_json(w: VocabWord) -> str:
    return json.dumps(
        {
            "word": w.word,
            "cefr_level": w.cefr_level,
            "pos": w.pos,
            "definition": w.definition,
            "etymology": w.etymology,
            "register": w.register,
            "contrast_note": w.contrast_note,
            "memory_hook": w.memory_hook,
            "examples": list(w.examples),
            "sentence_stem": w.sentence_stem,
            "sentence_answer": w.sentence_answer,
        }
    )


def _word_from_json(raw: str) -> VocabWord:
    d = json.loads(raw)
    return VocabWord(
        word=d["word"],
        cefr_level=d["cefr_level"],
        pos=d["pos"],
        definition=d.get("definition", ""),
        etymology=d["etymology"],
        register=d["register"],
        contrast_note=d["contrast_note"],
        memory_hook=d["memory_hook"],
        examples=tuple(d["examples"]),
        sentence_stem=d["sentence_stem"],
        sentence_answer=d["sentence_answer"],
    )


def _question_to_dict(q: AssessmentQuestion) -> dict:  # type: ignore[type-arg]
    return {
        "sentence": q.sentence,
        "options": list(q.options),
        "correct_index": q.correct_index,
        "cefr_level": q.cefr_level,
        "explanation": q.explanation,
    }


def _question_from_dict(d: dict) -> AssessmentQuestion:  # type: ignore[type-arg]
    return AssessmentQuestion(
        sentence=d["sentence"],
        options=tuple(d["options"]),
        correct_index=d["correct_index"],
        cefr_level=d["cefr_level"],
        explanation=d["explanation"],
    )
