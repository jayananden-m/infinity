# Dependency Rule

Dependencies point **inward only**. The domain layer has zero knowledge of any framework or infrastructure.

```mermaid
graph TD
    A[API Layer\nFastAPI routes · WebSocket handlers · Pydantic schemas]
    B[Domain Layer\nPure business logic · frozen dataclasses · zero I/O]
    C[Infrastructure Layer\nPostgreSQL · Redis · Anthropic · Celery]

    A -->|calls| B
    B -->|depends on abstract interfaces only| C

    style A fill:#1d3557,color:#fff
    style B fill:#2d6a4f,color:#fff
    style C fill:#457b9d,color:#fff
```

## Why this matters

| If domain depends on... | Problem |
|---|---|
| PostgreSQL | Can't test without a running database |
| FastAPI | Can't reuse domain logic in CLI tools or background jobs |
| Anthropic SDK | Can't swap LLM provider without touching business logic |

**The fix:** Domain defines *interfaces* (abstract base classes). Infrastructure *implements* them. Domain never imports from infrastructure.
