import json
from typing import Any

from groq import AsyncGroq, RateLimitError

from src.config import settings
from src.domain.models.passage import DifficultyVector, Passage, PassageSource
from src.domain.models.vocab import AssessmentQuestion, VocabWord

# ── Passage generation ──────────────────────────────────────────────────────

_PASSAGE_PROMPT = """Write a typing practice passage with these constraints:
- Target typing speed: {wpm} WPM (word complexity should reflect this)
- Grammar level: {grammar_level}/10
- Grammar constructs to include: {grammar_targets}
- Emphasize these characters: {key_focus}
- Length: approximately {word_count} words
- Plain prose only — no markdown, no bullet points, no headings

Respond with ONLY the passage text."""


def _build_passage_prompt(vector: DifficultyVector, target_words: int = 80) -> str:
    return _PASSAGE_PROMPT.format(
        wpm=int(vector.motor.target_wpm),
        grammar_level=vector.cognitive.grammar_level,
        grammar_targets=", ".join(vector.cognitive.grammar_targets) or "general",
        key_focus=", ".join(vector.motor.key_focus) or "standard",
        word_count=target_words,
    )


async def generate_passage(
    vector: DifficultyVector,
    grammar_tags: tuple[str, ...],
) -> Passage:
    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = _build_passage_prompt(vector)

    async def _call(model: str) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    try:
        content = await _call(settings.groq_model_primary)
    except RateLimitError:
        content = await _call(settings.groq_model_fallback)

    return Passage.create(
        content=content.strip(),
        difficulty=vector,
        grammar_tags=grammar_tags,
        source=PassageSource.LLM,
    )


# ── Vocab generation ─────────────────────────────────────────────────────────

_VOCAB_BATCH_PROMPT = """Pick {n} genuinely interesting English words for a CEFR {level} learner.
Avoid these already-learned words: {avoid}.

Go for words that are surprising, have a great backstory, come from unexpected origins, or unlock
a whole family of related words. Mix domains — pull from science, history, philosophy, art, law,
nature, medicine. Avoid basic everyday vocabulary (no "happy", "house", "walk").

For each word produce a teaching card. Return ONLY a valid JSON array, no markdown.
Each object must have exactly these keys:
  word           — the word itself (lowercase)
  cefr_level     — "{level}"
  pos            — part of speech (noun / verb / adjective / adverb / etc.)
  definition     — 1 sharp, opinionated sentence. Make the meaning crystal-clear and memorable,
                   not a bland dictionary entry.
  etymology      — 1 sentence on the word's origin. Prioritise surprising or counterintuitive facts.
  register       — one of: formal / informal / neutral / literary / technical / colloquial
  contrast_note  — "word ≠ similar_word: one crisp sentence on why they differ"
  memory_hook    — 1 vivid, concrete mnemonic. Use imagery, sound, or story — not abstract tips.
  examples       — array of exactly 2 sentences that show the word in genuine context (not textbook filler)
  sentence_stem  — one of the example sentences with the target word replaced by ___
  sentence_answer — the word that fills the blank"""

_VOCAB_WORD_PROMPT = """Create a vocabulary teaching card for the word "{word}" at CEFR {level} level.

Return ONLY a valid JSON array with exactly 1 object. Keys:
  word           — "{word}"
  cefr_level     — "{level}"
  pos            — part of speech
  definition     — 1 sharp, memorable sentence (not a bland dictionary entry)
  etymology      — 1 sentence; prioritise surprising or counterintuitive origin facts
  register       — formal / informal / neutral / literary / technical / colloquial
  contrast_note  — "{word} ≠ similar_word: one crisp sentence on the difference"
  memory_hook    — 1 vivid, concrete mnemonic using imagery or story
  examples       — array of exactly 2 rich, contextual sentences
  sentence_stem  — one example sentence with "{word}" replaced by ___
  sentence_answer — "{word}" """


async def generate_vocab_batch(
    level: str,
    n: int = 5,
    avoid: list[str] | None = None,
    target_word: str | None = None,
) -> list[VocabWord]:
    client = AsyncGroq(api_key=settings.groq_api_key)
    if target_word:
        prompt = _VOCAB_WORD_PROMPT.format(word=target_word, level=level)
    else:
        prompt = _VOCAB_BATCH_PROMPT.format(n=n, level=level, avoid=", ".join(avoid or []) or "none")

    async def _call(model: str) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2400,
            temperature=0.9,
        )
        return response.choices[0].message.content or "[]"

    try:
        raw = await _call(settings.groq_model_primary)
    except RateLimitError:
        raw = await _call(settings.groq_model_fallback)

    data: list[dict[str, Any]] = json.loads(raw.strip())
    return [
        VocabWord(
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
        for d in data
    ]


# ── Sentence Mining session ──────────────────────────────────────────────────

_MINE_PROMPT = """The user is a CEFR {level} English learner. They recently practiced these vocabulary words:
{words}

Write a 60-80 word passage that naturally uses at least {n} of these words in meaningful context.
The passage must be coherent, interesting prose — not a forced word list. Plain text only, no markdown.

Respond ONLY with valid JSON (no markdown fences):
{{"passage": "<the passage>", "target_words": ["word1", "word2", ...]}}

target_words must be the exact lowercase subset of the provided words that appear verbatim in the passage."""


async def generate_mine_passage(level: str, vocab_words: list[str]) -> dict[str, Any]:
    client = AsyncGroq(api_key=settings.groq_api_key)
    n = min(len(vocab_words), 4)
    prompt = _MINE_PROMPT.format(level=level, words=", ".join(vocab_words), n=n)

    async def _call(model: str) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7,
        )
        return response.choices[0].message.content or "{}"

    try:
        raw = await _call(settings.groq_model_primary)
    except RateLimitError:
        raw = await _call(settings.groq_model_fallback)

    return json.loads(raw.strip())  # type: ignore[no-any-return]


# ── Cloze Recovery session ────────────────────────────────────────────────────

_CLOZE_PROMPT = """Create {n} fill-in-the-blank sentences for a CEFR {level} English learner.
Use exactly these words (one word per sentence): {words}

Rules:
- Each sentence should be natural, contextually rich prose (not textbook filler)
- The missing word must be the only reasonable answer — no ambiguity
- Vary where the blank falls: sometimes start, middle, end

Return ONLY a valid JSON array (no markdown fences). Each object must have exactly these keys:
{{"full": "<complete sentence>", "stem": "<sentence with target word replaced by ___>",
"answer": "<target word lowercase>"}}"""


async def generate_cloze_items(level: str, vocab_words: list[str]) -> list[dict[str, str]]:
    client = AsyncGroq(api_key=settings.groq_api_key)
    n = min(len(vocab_words), 5)
    words = vocab_words[:n]
    prompt = _CLOZE_PROMPT.format(n=n, level=level, words=", ".join(words))

    async def _call(model: str) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.6,
        )
        return response.choices[0].message.content or "[]"

    try:
        raw = await _call(settings.groq_model_primary)
    except RateLimitError:
        raw = await _call(settings.groq_model_fallback)

    return json.loads(raw.strip())  # type: ignore[no-any-return]


# ── Grammar Drill session ─────────────────────────────────────────────────────

_DRILL_PROMPT = """Create a 3-round grammar drill targeting "{grammar_target}" for a CEFR {level} learner.

Round 1 (model): A clear, well-crafted sentence that demonstrates {grammar_target}.
Learner types it to encode the pattern.
Round 2 (vary): A different sentence using the same construct in a fresh context.
Round 3 (produce): Give only a sentence stem ending with ___ —
the learner completes it from memory using {grammar_target}.

Return ONLY valid JSON (no markdown fences):
{{"grammar_target": "{grammar_target}", "rounds": [
  {{"round_type": "model", "text": "<full model sentence>"}},
  {{"round_type": "vary", "text": "<full variation sentence>"}},
  {{"round_type": "produce", "text": "<full correct completion sentence>",
   "stem": "<sentence stem ending with ___ that the learner sees as a cue>",
   "target_word": "<key word or phrase the learner must supply>"}}
]}}"""


async def generate_drill_session(grammar_target: str, level: str) -> dict[str, Any]:
    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = _DRILL_PROMPT.format(grammar_target=grammar_target, level=level)

    async def _call(model: str) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.5,
        )
        return response.choices[0].message.content or "{}"

    try:
        raw = await _call(settings.groq_model_primary)
    except RateLimitError:
        raw = await _call(settings.groq_model_fallback)

    return json.loads(raw.strip())  # type: ignore[no-any-return]


# ── Assessment question generation ───────────────────────────────────────────

_ASSESS_PROMPT = """Generate {n} fill-in-the-blank questions to assess CEFR {level} competency.
Each question tests grammar or vocabulary typical of {level}.
Return ONLY a JSON array. Each object must have exactly these keys:
sentence (text with blank as ___), options (array of exactly 4 strings),
correct_index (0-based integer), cefr_level ("{level}"),
explanation (1 sentence explaining the correct answer)."""


async def generate_assess_questions(level: str, n: int = 2) -> list[AssessmentQuestion]:
    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = _ASSESS_PROMPT.format(n=n, level=level)

    async def _call(model: str) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.4,
        )
        return response.choices[0].message.content or "[]"

    try:
        raw = await _call(settings.groq_model_primary)
    except RateLimitError:
        raw = await _call(settings.groq_model_fallback)

    data: list[dict[str, Any]] = json.loads(raw.strip())
    return [
        AssessmentQuestion(
            sentence=d["sentence"],
            options=tuple(d["options"]),
            correct_index=d["correct_index"],
            cefr_level=d["cefr_level"],
            explanation=d["explanation"],
        )
        for d in data
    ]
