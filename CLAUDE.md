# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: TypeLingo

An adaptive typing + English learning application. The user builds it as a vehicle for learning backend engineering patterns. The project is currently in the **learning and planning phase** — `circuit_breaker.py` is the first implementation exercise, with the full application not yet started.

## Tech Stack (planned)

- **Backend**: Python 3.12 + FastAPI (async)
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0 (async) + Alembic migrations
- **Cache / Queue broker**: Redis 7
- **Task queue**: Celery (for async LLM passage generation)
- **LLM**: Anthropic Claude API (passage generation)
- **NLP**: spaCy (grammar tagging, sentence analysis)
- **Frontend**: Next.js + TypeScript
- **Testing**: pytest + pytest-asyncio
- **Linting/formatting**: ruff
- **Type checking**: mypy (strict)
- **Logging**: structlog (structured JSON)
- **Metrics**: prometheus-client

## Development Commands (when the app exists)

```bash
# Install dependencies
pip install -e ".[dev]"

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/ --strict

# Run unit tests only
pytest tests/unit/ -v --cov=src/domain --cov-fail-under=90

# Run integration tests (requires live Postgres + Redis)
pytest tests/integration/ -v

# Run a single test
pytest tests/unit/domain/test_scoring.py::test_wpm_calculation_basic -v

# Run tests by marker
pytest -m integration -v
pytest -m e2e -v

# Database migrations
alembic upgrade head
alembic downgrade -1

# Start services (once docker-compose exists)
docker-compose up -d
```

## Architecture: Modular Monolith with Hexagonal Architecture

The codebase is organized into three concentric layers — dependencies point inward only:

```
API Layer (adapters IN)
    ↓
Domain Layer (pure business logic — zero external dependencies)
    ↓ (via interfaces/ports)
Infrastructure Layer (adapters OUT: PostgreSQL, Redis, Anthropic, Celery)
```

**Planned source layout** (under `typelingo/src/`):
- `api/v1/` — thin routes (validation + routing only, no business logic)
- `domain/models/` — domain entities (distinct from ORM models)
- `domain/services/` — business rules: `adaptation.py`, `scoring.py`, `passage_selector.py`, `skill_updater.py`
- `domain/interfaces/` — abstract base classes (ports) for repos, cache, LLM client
- `infrastructure/database/repositories/` — SQLAlchemy implementations
- `infrastructure/cache/` — Redis implementation
- `infrastructure/llm/` — Anthropic client + prompt templates
- `infrastructure/queue/` — Celery app + tasks
- `websocket/` — real-time keystroke handler

## Core Domain Concept: The Dual-Skill Model

TypeLingo tracks two orthogonal skills per user:
- **Motor skill**: WPM, accuracy, per-key error rates, bigram speed (stored as JSONB)
- **Cognitive skill**: grammar level, vocabulary tier, grammar construct mastery (stored as JSONB)

The **adaptation engine** (`domain/services/adaptation.py`) challenges whichever skill is weaker while keeping the stronger skill in the comfort zone. This is the intellectual core of the system.

Motor and cognitive skill updates both use **exponential moving average** (`alpha=0.3`) to smooth variance. Disentangling whether an error is motor (fast typo + backspace) vs. cognitive (pause before word, consistent substitution) is done via timing and pattern heuristics.

## Testing Philosophy

- **Unit tests** (`tests/unit/`): pure domain logic, no I/O. Use in-memory repository implementations.
- **Integration tests** (`tests/integration/`): real PostgreSQL + Redis via Testcontainers or Docker services.
- **E2E tests** (`tests/e2e/`): full user flows through the API.
- TDD is the intended workflow: write failing test → minimal implementation → refactor.
- Domain layer should be testable with zero infrastructure (inject mock adapters).
- Do not mock the database in integration tests — test against a real instance.

## Passage Pipeline

Passages are expensive (LLM-generated). The retrieval order is:
1. Redis cache (key = hash of quantized difficulty vector, TTL 24h)
2. PostgreSQL passage store
3. Pre-seeded fallback corpus
4. Async generation via Celery → Anthropic API (circuit breaker wraps the LLM call)

Difficulty vectors are **quantized** before caching to increase hit rate.

## Learning Context

The `learning/` directory contains the user's personal notes:
- `progress.md` — session-by-session learning log
- `struggles.md` — patterns and weak areas to revisit
- `analogies.md` — mental models that worked

`typelingo-system-design.md` is the full architecture reference. `typelingo-study-guide.md` is the self-directed learning curriculum (phased). These documents are the source of truth for design decisions until code supersedes them.