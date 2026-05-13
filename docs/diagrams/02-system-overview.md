# System Overview

```mermaid
graph TD
    Browser -->|HTTPS| Nginx[Nginx\nReverse Proxy]
    Nginx --> FastAPI[FastAPI App]

    FastAPI --> API[API Layer\nRoutes · Auth · Validation]
    API --> Domain[Domain Layer\nBusiness Logic]
    Domain --> Repos[Repository Interfaces\nAbstract Ports]

    Repos --> PG[(PostgreSQL 16\nUsers · Sessions · Passages)]
    Repos --> Redis[(Redis 7\nCache · Queue · Live stats)]
    Repos --> Celery[Celery Workers\nLLM generation · Analytics]
    Celery --> LLM[Anthropic Claude API]

    style Domain fill:#2d6a4f,color:#fff
    style API fill:#1d3557,color:#fff
    style Repos fill:#457b9d,color:#fff
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| Nginx | TLS termination, reverse proxy, static assets |
| FastAPI | HTTP routing, request validation, auth middleware |
| Domain Layer | Business rules — adaptation engine, scoring, skill updates |
| Repository interfaces | Abstract data access — domain never touches SQL directly |
| PostgreSQL | Source of truth for all persistent data |
| Redis | Passage cache (TTL 24h), rate limiting, live session stats |
| Celery | Async passage generation — decouples LLM latency from request path |
