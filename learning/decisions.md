# Decision Log

Every significant architectural or tooling decision lives here.

---

## Decision: Architecture Style
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Microservices** — independent deployable services, own DBs
2. **Modular monolith** — single deployable, clear internal module boundaries
3. **Pure monolith** — no internal structure enforced

### Chosen: Modular monolith

### Rationale
Single developer, early stage. Microservices add operational overhead (deployment, debugging, distributed transactions) before there's evidence any component needs independent scaling. Hexagonal architecture + clear module boundaries mean any component can be extracted later with minimal domain changes.

---

## Decision: Domain Model Representation
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Pydantic models everywhere** — one library for everything
2. **Frozen dataclasses in domain, Pydantic at API boundary** — separation of concerns
3. **SQLAlchemy models everywhere** — ORM objects as domain objects

### Chosen: Frozen dataclasses in domain, Pydantic at API boundary

### Rationale
Domain layer must have zero external dependencies. Pydantic is an infrastructure concern (serialization, validation). Using it in the domain would couple business logic to a library. Frozen dataclasses enforce immutability — domain facts don't mutate in place, state transitions return new objects.

---

## Decision: ID Strategy
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Auto-increment integer** — simple, small
2. **UUID v4** — random, no info leakage

### Chosen: UUID v4

### Rationale
Auto-increment IDs leak row counts (competitors can infer user growth). UUIDs are safe to expose in URLs and are portable across services if we ever extract a module. Storage cost difference is negligible.

---

## Decision: Skill Profile Storage
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Separate `key_stats` table** — one row per key per user
2. **JSONB column on skill profile** — full profile as one blob

### Chosen: JSONB column

### Rationale
Motor and cognitive profiles are always read and written atomically — we never query individual keys in isolation. JSONB avoids a 52-row join (one per keyboard key) on every session load. Trade-off accepted: can't efficiently filter users by per-key performance in SQL (not a required query).

---

## Decision: LLM Passage Strategy
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Real-time generation** — generate on every session request
2. **Pre-generated corpus** — generate offline, serve from DB
3. **Hybrid** — async generation + Redis cache + pre-seeded fallback

### Chosen: Hybrid

### Rationale
Real-time adds 3–10s latency to session start. Pre-generated corpus can't adapt to new difficulty vectors. Hybrid: serve from cache/DB immediately, generate async via Celery when cache misses, pre-seed fallback for cold start. Circuit breaker protects against LLM outages.

---

## Decision: Python Linting Toolchain
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **flake8 + isort + black** — traditional trio
2. **ruff** — single tool reimplementing all three + more

### Chosen: ruff

### Rationale
ruff is 10–100x faster, replaces 3 tools with one config block, and includes pyflakes (`F`), isort (`I`), pyupgrade (`UP`), security (`S`), pylint (`PL`) rules and more. No functional difference — ruff's `F` ruleset is a reimplementation of pyflakes.

---

## Decision: LLM Provider
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Anthropic Claude API** — original plan
2. **Groq** — OpenAI-compatible API, free tier, LPU hardware (fast inference)

### Chosen: Groq (`llama-3.3-70b-versatile`)

### Rationale
No API credits for Anthropic. Groq's free tier is sufficient for development. Groq uses custom LPU hardware — inference is significantly faster than GPU-based providers. OpenAI-compatible API means the integration is straightforward. Because the LLM client lives in `infrastructure/llm/` behind an interface, this is a one-file swap — zero domain changes.

---

## Decision: SECRET_KEY handling
**Date:** 2026-04-18 · **Status:** Decided

### Options
1. **Default value in config** — convenient but insecure
2. **Required env var, no default** — fails fast if misconfigured

### Chosen: Required env var, no default

### Rationale
A hardcoded default means a misconfigured production deployment silently uses a known secret key — every token it signs is compromised. Failing fast at startup (CrashLoopBackOff in K8s) is the correct behaviour — it surfaces misconfiguration immediately rather than at the first authenticated request.
