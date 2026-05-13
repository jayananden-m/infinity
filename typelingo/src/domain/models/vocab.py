from dataclasses import dataclass

CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


@dataclass(frozen=True)
class VocabWord:
    word: str
    cefr_level: str
    pos: str
    definition: str
    etymology: str
    register: str
    contrast_note: str
    memory_hook: str
    examples: tuple[str, ...]
    sentence_stem: str
    sentence_answer: str


@dataclass(frozen=True)
class AssessmentQuestion:
    sentence: str
    options: tuple[str, ...]
    correct_index: int
    cefr_level: str
    explanation: str
