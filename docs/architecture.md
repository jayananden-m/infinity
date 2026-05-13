# TypeLingo — Architecture

> **Navigation:** Each section links to a dedicated diagram file. Open them in VS Code (`Cmd+Shift+V`) to render the diagrams.

---

## Build Status

| Phase | Description | Status |
|---|---|---|
| 1 | Project skeleton, Docker, pyproject.toml | ✅ Done |
| 2 | CI/CD pipeline, pre-commit, conventional commits | ✅ Done |
| 3 | Domain models (User, Session, Passage, Skill) | ✅ Done |
| 4 | Alembic migrations + DB schema | ✅ Done |
| 5 | Repository interfaces (ports) + in-memory implementations | ✅ Done |
| 6 | Auth (JWT + bcrypt + /refresh) | ✅ Done |
| 7 | Typing session API (REST + WebSocket) | ✅ Done |
| 8 | Scoring engine (TDD) | ✅ Done |
| 9 | WebSocket keystroke streaming + skill update on complete | ✅ Done |
| 10 | Skill update + adaptation engine (TDD) | ✅ Done |
| 11 | Redis cache (fallback-only, not primary path) | ✅ Done |
| 12 | Celery + Groq LLM pipeline (verified working ~0.8s) | ✅ Done |
| 13 | Skills API (GET /users/me/skills) | ✅ Done |
| 14 | Observability (structlog, Prometheus) | ✅ Done |
| 15 | Frontend (Next.js + TypeScript + terminal-dark UI) | ✅ Done |
| 16 | Frontend tests (Vitest + RTL, 20 component tests) | ✅ Done |
| 17 | Integration + E2E tests (wired to CI) | ✅ Done |
| 18 | Vocab system (Redis pool + Datamuse validation + Groq generation) | ✅ Done |
| 19 | Guest mode (7-day TTL, Celery cleanup task) | ✅ Done |
| 20 | Session modes: mine / cloze / drill (3 learning modes + random dispatch) | ✅ Done |

---

## Diagrams

### [01 — Dependency Rule](diagrams/01-dependency-rule.md)
Why domain has zero knowledge of infrastructure. The core architectural constraint everything else follows.

### [02 — System Overview](diagrams/02-system-overview.md)
Browser → FastAPI → Domain → PostgreSQL / Redis / Celery / Groq.

### [03 — Request Flow](diagrams/03-request-flow.md)
Full sequence: session start → passage retrieval (DB→cache fallback→LLM) → keystroke streaming → session completion → skill update.

### [04 — Domain Model](diagrams/04-domain-model.md)
All domain entities: `User`, `MotorSkillProfile`, `CognitiveSkillProfile`, `TypingSession`, `Passage`, `DifficultyVector`. Frozen dataclasses, zero external deps.

### [05 — Adaptation Flow](diagrams/05-adaptation-flow.md)
How the adaptation engine decides which skill to challenge next. EMA skill updates, motor vs cognitive error disentanglement.

### [06 — Circuit Breaker](diagrams/06-circuit-breaker.md)
State machine wrapping the Groq API: CLOSED → OPEN → HALF_OPEN. Graceful degradation chain.

### [07 — CI/CD Pipeline](diagrams/07-ci-pipeline.md)
GitHub Actions: quality → unit → security → frontend → integration → e2e. Pre-commit hooks for backend + frontend.

### [08 — Frontend Flow](diagrams/08-frontend-flow.md)
Terminal mode state machine (all modes + transitions), user journey (first visit → auth → level select → usage loop), component hierarchy, localStorage keys.

### [09 — Passage Pipeline](diagrams/09-passage-pipeline.md)
Full passage selection flow: DB → Redis fallback → Celery enqueue → Groq LLM → DB. Circuit breaker wrapping Groq.

### [10 — Session Modes](diagrams/10-session-modes.md)
Dispatch logic for `/session [mode]`, data flow per mode (mine / cloze / drill / regular), UX state machines, and results output.

### [11 — Terminal State Machine](diagrams/11-terminal-state-machine.md)
Complete `stateDiagram-v2` covering all mode transitions with triggers. Every mode has a cancel path to idle.

### [12 — Vocab & Learning Loop](diagrams/12-vocab-pipeline.md)
Vocab pool pipeline (Redis → Celery → Groq → Datamuse validation), on-demand word flow, and how practiced words feed mine/cloze sessions.

### [13 — User Journey](diagrams/13-user-journey.md)
End-to-end flows: first visit → auth paths → level select → usage loop. Shows how vocab, sessions, and skill adaptation connect.

---

## Key design decisions

Full decision log → [`../learning/decisions.md`](../learning/decisions.md)

| Date | Decision | Chosen | Supersedes |
|---|---|---|---|
| 2026-04-18 | Architecture style | Modular monolith | — |
| 2026-04-18 | Domain model representation | Frozen dataclasses | Pydantic in domain |
| 2026-04-18 | ID strategy | UUID v4 | Auto-increment int |
| 2026-04-18 | Skill storage | JSONB columns | Separate key_stats table |
| 2026-04-18 | LLM strategy | Hybrid (async generate + cache) | Real-time generation |
| 2026-04-18 | LLM provider | Groq (`llama-3.3-70b-versatile`) | Anthropic Claude |
| 2026-04-18 | Linting | ruff (replaces flake8 + isort + black) | pyflakes separately |
| 2026-04-18 | Secret management | Required env var, no default | Hardcoded default |
| 2026-04-22 | Passage selection | `random.choice(candidates)` from DB | `candidates[0]` (deterministic) |
| 2026-04-22 | Cache role | Fallback when DB empty, not primary path | Cache hit short-circuit |
| 2026-04-22 | localStorage namespacing | `tl_history_<user-uuid>` | Global `tl_history` key |
| 2026-05-01 | Session modes | mine/cloze/drill + random dispatch | single passage-copy sessions |
| 2026-05-01 | Vocab validation | Datamuse pre-check before LLM | LLM-only validation (unreliable) |
| 2026-05-01 | Level selection | Explicit user choice after login | Auto-assessment only |

---

## Test pyramid

```
         /\
        /E2E\        12 tests — full HTTP flows, real Postgres
       /------\
      /  Integ  \    7 tests — real Postgres + Redis
     /------------\
    /  Unit (141)  \  domain logic, zero infrastructure
   /----------------\
  / Frontend (20)    \  Vitest + RTL, component behaviour
 /--------------------\
```

## Service map

```
localhost:3000  ← Next.js dev server (typelingo-frontend/)
localhost:8000  ← FastAPI (uvicorn, typelingo/src/main.py)
localhost:5432  ← PostgreSQL 16
localhost:6379  ← Redis 7
                  Celery worker (same image as API)
                  Groq API (external, GROQ_API_KEY required)
```
