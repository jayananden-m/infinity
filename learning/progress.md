## Session 1 — 2026-03-01
### Covered
- Circuit breaker pattern (concept + attempted implementation)
- State machine thinking: CLOSED → OPEN → HALF_OPEN
- Guard clause pattern: check most restrictive state first
- Pseudocode-first development technique

### Status
- Circuit breaker: understand the concept, reviewed full solution,
  need to trace through by hand and re-implement solo
- Haven't started: cache-aside, repository pattern, message queues

### Next
- Trace through the circuit breaker code on paper (12 requests)
- Re-implement circuit breaker from scratch without looking at solution
- Start reading: "Architecture Patterns with Python" Chapter 1-2

---

## Sessions 2–N — March–April 2026
### Built (full backend + frontend, all phases)

**Architecture**
- Modular monolith with hexagonal architecture (domain → ports → adapters)
- Domain layer has zero external dependencies — all infrastructure injected via abstract interfaces
- Three concentric layers: API (adapters IN) → Domain (pure logic) → Infrastructure (adapters OUT)

**Domain Layer** (`src/domain/`)
- `models/`: Passage, TypingSession (state machine: STARTED → COMPLETED/ABANDONED),
  MotorSkillProfile, CognitiveSkillProfile, KeystrokeEvent, SessionMetrics — all frozen dataclasses
- `services/scoring.py`: WPM = (correct_chars/5)/duration_minutes, accuracy, per-key IKI stats
- `services/adaptation.py`: CHALLENGE_MOTOR / CHALLENGE_COGNITIVE / BALANCED_ADVANCE strategy
  based on ratio of motor_wpm vs cognitive_level×10; thresholds 0.85 / 1.15
- `services/skill_updater.py`: EMA (alpha=0.3) updates for both motor and cognitive skills
- `services/passage_selector.py`: cache-aside pattern (Redis → Postgres → raise + enqueue)
- `services/circuit_breaker.py`: CLOSED/OPEN/HALF_OPEN state machine wrapping LLM calls
- `services/user_setup.py`: initialises motor + cognitive profiles on first session

**Infrastructure Layer** (`src/infrastructure/`)
- PostgreSQL repositories for: passage, session, motor_skill, cognitive_skill, user
- Redis passage cache with JSON serialisation + 24h TTL
- Groq LLM client: primary (llama-3.3-70b-versatile) → fallback on RateLimitError (llama-3.1-8b-instant)
- Celery task for async passage generation → saves to DB + Redis

**API Layer** (`src/api/v1/`)
- `auth.py`: POST /register (bcrypt + JWT), POST /login, POST /refresh
- `sessions.py`: POST /sessions (start), GET /sessions/{id}, POST /sessions/{id}/complete,
  POST /sessions/{id}/abandon
- `users.py`: GET /users/me/skills — returns live motor + cognitive skill data
- `health.py`: GET /health
- JWT: stateless access tokens (15 min) + /refresh endpoint
- CORS middleware with `cors_origins` from settings

**WebSocket** (`src/websocket/handler.py`)
- `/api/v1/sessions/{id}/stream?token=...` — real-time keystroke streaming
- Buffers keystrokes in memory, scores on `{"action":"complete"}`
- Calls `_update_skills()` on session completion (EMA update wired end-to-end)
- Disconnect does NOT abandon session — user can reconnect (fixes React StrictMode double-connect bug)

**Observability**
- structlog JSON structured logging, bound with request_id per request
- Prometheus counters: SESSIONS_STARTED, SESSIONS_COMPLETED, SESSIONS_ABANDONED
- Prometheus histogram: WPM_HISTOGRAM
- RequestIDMiddleware: stamps X-Request-ID header, binds to structlog contextvars

**Database**
- Alembic migration: 5 tables (passages, users, motor_skill_profiles, cognitive_skill_profiles,
  typing_sessions) + GIN indexes on JSONB columns + partial index on completed_at
- JSONB for motor stats (per-key IKI) and cognitive stats (grammar mastery)

**Testing**
- 141 unit tests, 99% domain coverage, all passing
- 20 frontend component tests (Vitest + RTL) covering Label, Btn, TextLink, Field
- Integration tests: session_repository (4) + passage_selector (3)
- E2E tests: 12 tests covering auth flow, session lifecycle, skills endpoint
- In-memory fake repositories for domain tests (zero infrastructure)
- TDD workflow: red → green → refactor

**Tooling**
- ruff (full production ruleset, 88 char limit), mypy strict — both passing
- docker-compose.yml: postgres + redis + api + celery worker
- Dockerfile: multi-stage build
- Makefile: install, lint, typecheck, test-unit, test-integration, test-e2e, seed, run, up, down
- CI/CD: GitHub Actions (quality → unit → security → frontend → integration → e2e)
- Pre-commit hooks: ruff + mypy (backend), tsc + eslint (frontend), commitizen
- scripts/seed_passages.py: 5 passages at grammar levels 1–4 (`make seed`)

**Frontend** (`typelingo-frontend/`, Next.js + TypeScript)
- Terminal-dark design system: CSS variables, shimmer animations, boot sequence
- /register, /login, /dashboard, /session/[id], /session/[id]/results pages
- Dashboard: real skill bars from GET /users/me/skills (motor WPM + cognitive level)
- Session: live WPM, error count, progress bar, character-level correct/wrong highlighting
- Results: grade hero (S/A/B/C), metric reveal animation, real WPM delta vs previous baseline
- LocalStorage history namespaced by user ID (tl_history_<uuid>) — no cross-account leakage
- Token refresh every 14 min (before 15-min JWT expiry)
- Eye/show-password toggle on password fields

---

## Session — 2026-04-22 (today)
### What was verified working end-to-end
- Register → login → start session → type → results → dashboard updates
- Skill model (37.0 WPM after one session at 53 WPM — EMA smoothing visible)
- Celery + Groq LLM passage generation: truncated passages, hit 503, Groq fired in 0.8s
- Multi-user isolation: different accounts see separate history and skill bars
- Passage variety: randomised selection from candidates (fixed deterministic `candidates[0]` bug)

### Key bugs fixed this session
- `candidates[0]` always served same passage → fixed with `random.choice(candidates)`
- Cache short-circuit returned same passage for 24h → cache now only used as DB-empty fallback
- `tl_history` shared across users → namespaced to `tl_history_<user-uuid>`
- React StrictMode double-connect abandoned session on first connect → sessions stay STARTED on disconnect

### Next (future sessions)
- Bigram tracking in per-key stats (currently always empty dict)
- Prometheus/Grafana compose service for live metrics dashboard
- More seeded passages at levels 2–4 to test cognitive advancement
- Mobile-responsive layout
