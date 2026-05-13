# Passage Pipeline

How TypeLingo selects, generates, and caches passages.

```mermaid
flowchart TD
    Start[POST /sessions] --> Build[Build DifficultyVector\nfrom motor + cognitive profiles]
    Build --> Quantize[Quantize vector\nfor cache key stability]
    Quantize --> DB[find_by_difficulty\nPostgreSQL limit=10]

    DB -->|candidates found| Random[random.choice candidates]
    Random --> CacheSet[SET Redis cache_key\nTTL 24h]
    CacheSet --> Return201[201 passage_content]

    DB -->|empty| CacheFallback[GET Redis cache_key]
    CacheFallback -->|cache hit| Return201

    CacheFallback -->|cache miss| Enqueue[enqueue Celery task\ngenerate_passage_task.delay]
    Enqueue --> Return503[503 no passages available]

    Enqueue -.->|async ~0.8s| GroqAPI[Groq API\nllama-3.3-70b-versatile]
    GroqAPI -.-> SaveDB[save to PostgreSQL]
    SaveDB -.-> SaveRedis[SET Redis cache_key]
    SaveRedis -.-> ReadyNext[available for next session]

    style Return201 fill:#2d6a4f,color:#fff
    style Return503 fill:#9b2335,color:#fff
    style GroqAPI fill:#457b9d,color:#fff
```

## Difficulty vector quantization

Before using a vector as a cache key, values are rounded to reduce the key space:

| Field | Quantization |
|---|---|
| `target_wpm` | rounded to nearest 5 |
| `grammar_level` | rounded to nearest 1 (already int) |
| `vocabulary_tier` | rounded to nearest 1 (already int) |

This means a user at 37.2 WPM and a user at 38.9 WPM share the same cache key (both → 40).
Higher cache hit rate at the cost of less precise targeting.

## Circuit breaker around Groq

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> OPEN : failure_count >= threshold
    OPEN --> HALF_OPEN : timeout elapsed
    HALF_OPEN --> CLOSED : probe succeeds
    HALF_OPEN --> OPEN : probe fails
    CLOSED --> CLOSED : success (reset count)
```

When OPEN: Celery task raises `CircuitBreakerOpen` immediately — no HTTP call made.
When HALF_OPEN: one probe attempt; if Groq responds, circuit closes.

## Passage sources

| Source | When used |
|---|---|
| `SEED` | Pre-seeded passages via `make seed` (5 passages, levels 1–4) |
| `LLM` | Groq-generated, difficulty-targeted, stored permanently |
