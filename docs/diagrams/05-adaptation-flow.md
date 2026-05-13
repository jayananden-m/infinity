# Adaptation Algorithm

The intellectual core of TypeLingo. Selects the next passage by challenging whichever skill is weaker.

```mermaid
flowchart TD
    A[Session Completed] --> B[Compute motor_level\nnormalize WPM + accuracy → 0–1]
    A --> C[Compute cognitive_level\nnormalize grammar + vocab → 0–1]
    B --> D{Compare skill gap}
    C --> D

    D -->|gap < 0.1 threshold| E[BALANCED_ADVANCE\nboth skills +slight stretch]
    D -->|motor_level > cognitive_level| F[CHALLENGE_COGNITIVE\nmotor stays in comfort zone\ncognitive pushed to next level]
    D -->|cognitive_level > motor_level| G[CHALLENGE_MOTOR\ncognitive stays in comfort zone\nmotor pushed, focus weak keys]

    F --> H[Apply spaced repetition\nfor weak grammar areas]
    G --> H
    E --> H

    H --> I[DifficultyVector\nquantized for cache efficiency]
    I --> J[Passage selector\nRedis → PostgreSQL → fallback]
```

## Skill update after session (EMA)

```
new_value = alpha * observation + (1 - alpha) * old_value
alpha = 0.3
```

- High alpha (0.3) → recent sessions matter more
- Low alpha → smoother but slower to adapt
- Applied to: WPM, accuracy, per-key avg_ms, per-key error_rate

## Motor vs cognitive error disentanglement

When a user errors on a word — is it a typo (motor) or confusion (cognitive)?

| Signal | Motor error | Cognitive error |
|---|---|---|
| Timing | Fast keystroke + quick backspace (<500ms) | Long pause before the word |
| Pattern | Random character substitution | Consistent wrong word (e.g. "their" → "they're") |
| Context | Key appears in weak_keys profile | Grammar tag appears in weak_areas |
