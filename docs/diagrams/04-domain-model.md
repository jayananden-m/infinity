# Domain Model

All domain models are **frozen dataclasses** — immutable, zero external dependencies.

```mermaid
classDiagram
    class User {
        +UUID id
        +str email
        +str display_name
        +str hashed_password
        +datetime created_at
        +datetime updated_at
        +create(email, display_name, hashed_password) User$
    }

    class MotorSkillProfile {
        +UUID user_id
        +float overall_wpm
        +float overall_accuracy
        +dict key_profiles
        +dict bigram_stats
        +datetime updated_at
        +comfort_wpm() float
        +stretch_wpm() float
        +weakest_keys(n) list
        +slowest_bigrams(n) list
        +initial(user_id) MotorSkillProfile$
    }

    class CognitiveSkillProfile {
        +UUID user_id
        +int grammar_level
        +int vocabulary_tier
        +tuple weak_areas
        +tuple strong_areas
        +datetime updated_at
        +comfort_grammar_level() int
        +stretch_grammar_level() int
        +weakest_areas(n) list
        +initial(user_id) CognitiveSkillProfile$
    }

    class KeyProfile {
        +float avg_ms
        +float error_rate
        +int samples
        +default() KeyProfile$
        +updated(new_avg_ms, new_error_rate) KeyProfile
    }

    class BigramProfile {
        +float avg_ms
        +int samples
        +default() BigramProfile$
        +updated(new_avg_ms) BigramProfile
    }

    class SkillDelta {
        +float wpm_delta
        +float accuracy_delta
        +int grammar_level_delta
        +datetime updated_at
    }

    class DifficultyVector {
        +MotorTarget motor
        +CognitiveTarget cognitive
        +quantize() DifficultyVector
        +cache_key() str
    }

    class MotorTarget {
        +float target_wpm
        +tuple key_focus
        +tuple bigram_focus
        +float word_length_avg
        +quantize() MotorTarget
    }

    class CognitiveTarget {
        +int grammar_level
        +int vocabulary_tier
        +tuple grammar_targets
        +float sentence_complexity
        +quantize() CognitiveTarget
    }

    class Passage {
        +UUID id
        +str content
        +DifficultyVector difficulty
        +tuple grammar_tags
        +int word_count
        +PassageSource source
        +datetime created_at
        +create(content, difficulty, grammar_tags, source) Passage$
    }

    class PassageSource {
        <<enumeration>>
        LLM
        SEED
        CACHE
    }

    class TypingSession {
        +UUID id
        +UUID user_id
        +UUID passage_id
        +SessionStatus status
        +datetime started_at
        +tuple keystrokes
        +datetime completed_at
        +SessionMetrics metrics
        +start(user_id, passage_id) TypingSession$
        +complete(keystrokes, metrics) TypingSession
        +abandon() TypingSession
    }

    class SessionStatus {
        <<enumeration>>
        STARTED
        COMPLETED
        ABANDONED
    }

    class KeystrokeEvent {
        +str key
        +int timestamp_ms
        +bool correct
    }

    class SessionMetrics {
        +float wpm
        +float accuracy
        +float duration_seconds
        +dict per_key_stats
    }

    class AdaptationStrategy {
        <<enumeration>>
        CHALLENGE_MOTOR
        CHALLENGE_COGNITIVE
        BALANCED_ADVANCE
    }

    User "1" --> "1" MotorSkillProfile
    User "1" --> "1" CognitiveSkillProfile
    MotorSkillProfile --> KeyProfile
    MotorSkillProfile --> BigramProfile
    TypingSession --> User
    TypingSession --> Passage
    TypingSession --> SessionStatus
    TypingSession "1" --> "many" KeystrokeEvent
    TypingSession --> SessionMetrics
    Passage --> DifficultyVector
    Passage --> PassageSource
    DifficultyVector --> MotorTarget
    DifficultyVector --> CognitiveTarget
```

## Design decisions

| Decision | Choice | Reason |
|---|---|---|
| `frozen=True` | Yes on all models | Domain facts are immutable — `session.complete()` returns a *new* session |
| IDs | `UUID` | No info leakage, safe across services |
| `datetime` | Always UTC-aware | `S` rules enforce this; naive datetimes cause bugs at timezone boundaries |
| Lists vs tuples | `tuple` for ordered immutable sequences | Frozen dataclasses can't contain mutable `list` fields |
| State transitions | Methods return new instances | `session.complete()` enforces `STARTED → COMPLETED` invariant |
