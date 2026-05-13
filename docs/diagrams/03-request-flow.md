# Request Flow — Full Typing Session

```mermaid
sequenceDiagram
    participant Browser
    participant API
    participant Domain
    participant Redis
    participant PostgreSQL
    participant Celery
    participant Groq

    Browser->>API: POST /api/v1/sessions (JWT)
    API->>PostgreSQL: get motor + cognitive skill profiles
    Note over API,PostgreSQL: initialise_user_profiles() — creates on first session
    API->>PostgreSQL: find_by_difficulty(vector, limit=10)
    alt DB has candidates
        PostgreSQL-->>API: list of passages
        API->>API: random.choice(candidates)
        API->>Redis: SET cache_key (for fallback)
    else DB empty
        API->>Redis: GET cache_key (fallback)
        alt Redis has passage
            Redis-->>API: cached passage
        else Redis also empty
            API->>Celery: enqueue generate_passage_task(vector)
            API-->>Browser: 503 no passages available
            Note over Celery,Groq: Async — does not block user
            Celery->>Groq: POST /openai/v1/chat/completions
            Groq-->>Celery: generated passage (~0.8s)
            Celery->>PostgreSQL: save passage
            Celery->>Redis: SET cache_key
        end
    end
    API-->>Browser: 201 { session_id, passage_content }

    Browser->>API: WS /api/v1/sessions/{id}/stream?token=...
    Note over Browser,API: WebSocket handshake + JWT auth
    API-->>Browser: connected

    loop Every keystroke
        Browser->>API: { key, timestamp_ms, correct }
        Note over API: buffered in memory
    end

    Browser->>API: { action: "complete" }
    API->>Domain: score(keystrokes) → SessionMetrics
    API->>PostgreSQL: save completed session
    API->>Domain: update_motor_skill(profile, metrics) EMA α=0.3
    API->>Domain: update_cognitive_skill(profile, tags, metrics)
    API->>PostgreSQL: save updated motor + cognitive profiles
    API-->>Browser: { status: completed, wpm, accuracy }

    Browser->>Browser: store tl_history_<uid> in localStorage
    Browser->>Browser: navigate to /results?wpm=X&accuracy=Y&prev_wpm=Z
```

## Key flow invariants

| Invariant | Where enforced |
|---|---|
| Session stays STARTED after WS disconnect | `handler.py` — no state change on disconnect |
| Same user cannot own another user's session | `session.user_id != user_id` → 404 |
| Completed/abandoned session cannot be re-completed | `session.complete()` raises if not STARTED |
| Passage selection is random, not deterministic | `random.choice(candidates)` |
| Cache is fallback only, not primary path | DB queried first on every request |
| JWT refreshed before expiry | Frontend 14-min interval, 15-min token TTL |
