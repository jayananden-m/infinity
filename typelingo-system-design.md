# TypeLingo — System Design Document
### An Adaptive Typing & English Learning Application

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Design (HLD)](#2-high-level-design)
3. [Low-Level Design (LLD)](#3-low-level-design)
4. [Data Model & Database Design](#4-data-model--database-design)
5. [Adaptive Algorithm Design](#5-adaptive-algorithm-design)
6. [LLM Integration & Passage Pipeline](#6-llm-integration--passage-pipeline)
7. [Distributed Systems Patterns](#7-distributed-systems-patterns)
8. [API Design](#8-api-design)
9. [SRE & Observability](#9-sre--observability)
10. [TDD & Testing Strategy](#10-tdd--testing-strategy)
11. [CI/CD Pipeline](#11-cicd-pipeline)
12. [Security](#12-security)
13. [Tech Stack Summary](#13-tech-stack-summary)
14. [Project Phases & Milestones](#14-project-phases--milestones)

---

## 1. System Overview

### Problem Statement

Existing typing tutors model users on a single dimension (keystroke performance). Language apps don't consider typing ability. TypeLingo combines both into a single adaptive system where the user model accounts for the interplay between a **motor skill** (typing) and a **cognitive skill** (English proficiency). These two skills are acquired differently and progress at different rates, creating a richer adaptation problem.

### Core Concept — The Dual-Skill Model

```
┌─────────────────────────────────────────────────────┐
│                   USER MODEL                        │
│                                                     │
│  ┌──────────────────┐    ┌───────────────────────┐  │
│  │   MOTOR SKILL    │    │   COGNITIVE SKILL     │  │
│  │                  │    │                       │  │
│  │  - WPM           │    │  - Grammar level      │  │
│  │  - Accuracy %    │    │  - Vocabulary tier     │  │
│  │  - Per-key error  │    │  - Sentence complexity │  │
│  │    heatmap       │    │  - Error patterns      │  │
│  │  - Bigram speed  │    │  - Comprehension score │  │
│  │  - Fatigue curve │    │                       │  │
│  └──────────────────┘    └───────────────────────┘  │
│                                                     │
│           ┌─────────────────────┐                   │
│           │  ADAPTATION ENGINE  │                   │
│           │                     │                   │
│           │  Selects passages   │                   │
│           │  that challenge the │                   │
│           │  weaker skill while │                   │
│           │  staying comfortable│                   │
│           │  on the stronger    │                   │
│           └─────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

### Example Adaptation Scenarios

| User Profile | Passage Characteristics |
|---|---|
| Fast typist, weak grammar | Targets grammar structures at learning edge. Full typing speed. Complex words are fine. |
| Slow typist, strong English | Familiar vocabulary, simpler grammar. Focuses on problematic key combinations. |
| Weak at 'q','z' keys + learning past tense | Passages rich in 'q'/'z' words AND past tense constructions. |
| Both skills strong | Introduces advanced grammar (subjunctive, conditionals) with challenging key patterns. |

---

## 2. High-Level Design

### Architecture: Modular Monolith (Microservice-Ready)

We start with a **modular monolith** — a single deployable unit with clearly separated internal modules that communicate through defined interfaces. This gives us the simplicity of a monolith with the future ability to extract any module into its own service.

```
                    ┌─────────────┐
                    │   Browser   │
                    │  (React /   │
                    │  Next.js)   │
                    └──────┬──────┘
                           │ HTTPS
                           ▼
                    ┌─────────────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
                           ▼
              ┌────────────────────────┐
              │      FastAPI App       │
              │                        │
              │  ┌──────────────────┐  │
              │  │   API Layer      │  │  ← Routes, request validation, auth
              │  └────────┬─────────┘  │
              │           │            │
              │  ┌────────▼─────────┐  │
              │  │  Service Layer   │  │  ← Business logic, orchestration
              │  │                  │  │
              │  │ ┌─────────────┐  │  │
              │  │ │ Typing Svc  │  │  │  ← Session mgmt, keystroke processing
              │  │ ├─────────────┤  │  │
              │  │ │ User Model  │  │  │  ← Dual-skill tracking, adaptation
              │  │ │ Service     │  │  │
              │  │ ├─────────────┤  │  │
              │  │ │ Passage Svc │  │  │  ← Retrieval, generation, caching
              │  │ ├─────────────┤  │  │
              │  │ │ Analytics   │  │  │  ← Progress tracking, insights
              │  │ │ Service     │  │  │
              │  │ └─────────────┘  │  │
              │  └────────┬─────────┘  │
              │           │            │
              │  ┌────────▼─────────┐  │
              │  │ Repository Layer │  │  ← Data access abstraction
              │  └────────┬─────────┘  │
              └───────────┼────────────┘
                          │
            ┌─────────────┼──────────────┐
            │             │              │
            ▼             ▼              ▼
     ┌────────────┐ ┌──────────┐ ┌────────────┐
     │ PostgreSQL │ │  Redis   │ │   Celery   │
     │            │ │          │ │  Workers   │
     │ - Users    │ │ - Cache  │ │            │
     │ - Sessions │ │ - Queue  │ │ - LLM gen  │
     │ - Passages │ │ - Live   │ │ - Analytics│
     │ - Metrics  │ │   stats  │ │ - Batch    │
     └────────────┘ └──────────┘ └──────┬─────┘
                                        │
                                        ▼
                                 ┌─────────────┐
                                 │ Anthropic /  │
                                 │ OpenAI API   │
                                 │ (LLM)        │
                                 └─────────────┘
```

### Request Flow — A Typical Typing Session

```
1. User opens app → GET /api/v1/sessions/new
   └─→ Service fetches user model from PostgreSQL
   └─→ Adaptation engine computes target difficulty vector
   └─→ Passage service queries cache/DB for matching passage
       ├─→ Cache HIT: Return cached passage from Redis
       └─→ Cache MISS: Check PostgreSQL passage store
           ├─→ DB HIT: Return stored passage, cache it
           └─→ DB MISS: Enqueue LLM generation job
               └─→ Return a fallback passage (pre-seeded)
               └─→ Async: Celery worker generates via LLM
               └─→ Store in DB + Redis for future use

2. User types → WebSocket: keystroke events streamed
   └─→ Server processes in real-time
   └─→ Per-key timing, accuracy tracked in memory
   └─→ Periodic flush to Redis (live stats)

3. User finishes → POST /api/v1/sessions/{id}/complete
   └─→ Compute session metrics (WPM, accuracy, per-key stats)
   └─→ Update user model (both motor + cognitive dimensions)
   └─→ Persist to PostgreSQL
   └─→ Enqueue background analytics job
   └─→ Pre-generate next passages based on updated model
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Architecture style | Modular monolith | Simplicity now, extractable later. Clear module boundaries. |
| API protocol | REST + WebSocket | REST for CRUD, WebSocket for real-time keystroke streaming. |
| Passage strategy | Hybrid (generate + cache) | LLM is expensive/slow; cache aggressively, generate async. |
| Background jobs | Celery + Redis broker | Decouples LLM generation from request path. |
| Database | PostgreSQL | ACID for user data, JSONB for flexible skill models. |
| Cache | Redis | Fast reads for passages, live session stats, rate limiting. |
| Auth | JWT + httponly cookies | Stateless auth, secure token storage. |

---

## 3. Low-Level Design

### 3.1 Project Structure (Domain-Driven)

```
typelingo/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Settings (pydantic-settings)
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/                    # API Layer (thin — validation + routing only)
│   │   ├── __init__.py
│   │   ├── middleware/
│   │   │   ├── rate_limiter.py
│   │   │   ├── request_id.py   # Attach trace ID to every request
│   │   │   └── error_handler.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Aggregates all v1 routes
│   │       ├── auth.py
│   │       ├── sessions.py
│   │       ├── passages.py
│   │       ├── users.py
│   │       └── analytics.py
│   │
│   ├── domain/                 # Core business logic (ZERO external dependencies)
│   │   ├── __init__.py
│   │   ├── models/             # Domain entities (not ORM models)
│   │   │   ├── user.py         # User, MotorSkillProfile, CognitiveSkillProfile
│   │   │   ├── session.py      # TypingSession, KeystrokeEvent
│   │   │   ├── passage.py      # Passage, DifficultyVector
│   │   │   └── skill.py        # SkillLevel, SkillDelta
│   │   ├── services/           # Business rules, orchestration
│   │   │   ├── adaptation.py   # The core adaptive algorithm
│   │   │   ├── scoring.py      # WPM calculation, accuracy, per-key analysis
│   │   │   ├── passage_selector.py  # Matches passages to user model
│   │   │   └── skill_updater.py     # Updates user model after session
│   │   └── interfaces/         # Abstract base classes (ports)
│   │       ├── passage_repo.py
│   │       ├── user_repo.py
│   │       ├── session_repo.py
│   │       ├── cache.py
│   │       └── llm_client.py
│   │
│   ├── infrastructure/         # Implementations (adapters)
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── connection.py   # SQLAlchemy async engine
│   │   │   ├── models.py       # ORM models (separate from domain models)
│   │   │   └── repositories/
│   │   │       ├── user_repo.py
│   │   │       ├── session_repo.py
│   │   │       └── passage_repo.py
│   │   ├── cache/
│   │   │   └── redis_cache.py
│   │   ├── llm/
│   │   │   ├── anthropic_client.py
│   │   │   └── prompt_templates.py
│   │   ├── queue/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py        # Background task definitions
│   │   └── observability/
│   │       ├── logging.py      # Structured logging (structlog)
│   │       ├── metrics.py      # Prometheus metrics
│   │       └── tracing.py      # OpenTelemetry setup
│   │
│   └── websocket/
│       ├── __init__.py
│       └── typing_handler.py   # Real-time keystroke processing
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_adaptation.py
│   │   │   ├── test_scoring.py
│   │   │   └── test_skill_updater.py
│   │   └── api/
│   │       └── test_sessions.py
│   ├── integration/
│   │   ├── test_passage_pipeline.py
│   │   ├── test_session_flow.py
│   │   └── test_user_model_update.py
│   ├── e2e/
│   │   └── test_full_session.py
│   ├── conftest.py             # Shared fixtures
│   └── factories.py            # Test data factories
│
├── scripts/
│   ├── seed_passages.py        # Pre-seed passage database
│   └── load_test.py            # k6 / locust load test config
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── Makefile                    # Common commands
└── README.md
```

### 3.2 Why This Structure Matters (Hexagonal Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (Adapters IN)               │
│           REST routes, WebSocket handlers                │
└────────────────────────┬────────────────────────────────┘
                         │ calls
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  DOMAIN (Pure Business Logic)            │
│                                                         │
│   Services ←→ Models ←→ Interfaces (abstract)           │
│                                                         │
│   This layer has ZERO knowledge of:                     │
│   - PostgreSQL, Redis, HTTP, WebSockets                 │
│   - Which LLM provider we use                           │
│   - How data is serialized                              │
│                                                         │
│   It ONLY knows about:                                  │
│   - User skill models and how they evolve               │
│   - How to score a typing session                       │
│   - How to select/adapt passage difficulty               │
└────────────────────────┬────────────────────────────────┘
                         │ depends on (via interfaces)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Infrastructure (Adapters OUT)               │
│     PostgreSQL repos, Redis cache, Anthropic client,    │
│     Celery tasks, Prometheus metrics                    │
└─────────────────────────────────────────────────────────┘
```

**Why this matters for testing:** Your entire domain layer can be tested with pure unit tests — no database, no Redis, no API calls. You inject mock implementations of the interfaces. This is the foundation of TDD.

**Why this matters for distributed systems:** When you're ready to extract, say, the Passage Service into its own microservice, the interface boundary is already defined. You swap the in-process implementation for an HTTP/gRPC client. Zero changes to domain logic.

---

## 4. Data Model & Database Design

### 4.1 Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────────┐
│    users     │       │  typing_sessions │       │    passages     │
├──────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)      │──┐    │ id (PK)          │    ┌──│ id (PK)         │
│ email        │  │    │ user_id (FK)     │────┘  │ content         │
│ display_name │  │    │ passage_id (FK)  │───────│ difficulty_vec  │
│ created_at   │  │    │ started_at       │       │ grammar_tags[]  │
│ updated_at   │  │    │ completed_at     │       │ vocabulary_tier │
└──────────────┘  │    │ wpm              │       │ target_keys[]   │
                  │    │ accuracy         │       │ word_count      │
┌──────────────┐  │    │ raw_keystrokes   │       │ source (llm/    │
│ motor_skill  │  │    │   (JSONB)        │       │   seed/cached)  │
│ _profiles    │  │    │ session_metrics  │       │ generation_     │
├──────────────┤  │    │   (JSONB)        │       │   prompt (TEXT) │
│ id (PK)      │  │    └──────────────────┘       │ llm_model       │
│ user_id (FK) │──┘                               │ embedding       │
│ overall_wpm  │  │    ┌──────────────────┐       │   (vector)      │
│ overall_acc  │  │    │ cognitive_skill  │       │ created_at      │
│ key_profiles │  │    │ _profiles        │       │ usage_count     │
│   (JSONB)    │  │    ├──────────────────┤       └─────────────────┘
│ bigram_stats │  │    │ id (PK)          │
│   (JSONB)    │  │    │ user_id (FK)     │──┘
│ updated_at   │  │    │ grammar_level    │
└──────────────┘  │    │ vocabulary_tier  │
                  │    │ weak_areas[]     │
                  │    │   (JSONB)        │
                  │    │ strong_areas[]   │
                  │    │   (JSONB)        │
                  │    │ updated_at       │
                  │    └──────────────────┘
```

### 4.2 Key Schema Details

```sql
-- Motor skill: per-key performance stored as JSONB
-- This is a design decision: JSONB over a separate key_stats table
-- because we always read/write the full profile atomically.
-- Trade-off: Can't query individual keys efficiently, but we never need to.

key_profiles JSONB example:
{
  "a": { "avg_ms": 85, "error_rate": 0.02, "samples": 1420 },
  "b": { "avg_ms": 112, "error_rate": 0.08, "samples": 890 },
  "q": { "avg_ms": 210, "error_rate": 0.15, "samples": 45 },
  ...
}

bigram_stats JSONB example:
{
  "th": { "avg_ms": 95, "samples": 2100 },
  "qu": { "avg_ms": 240, "samples": 38 },
  ...
}

-- Passage difficulty vector: the "address" in difficulty space
difficulty_vec JSONB example:
{
  "motor": {
    "target_wpm": 45,
    "key_focus": ["q", "z", "x"],
    "bigram_focus": ["qu", "xp"],
    "word_length_avg": 5.2
  },
  "cognitive": {
    "grammar_level": 3,
    "grammar_targets": ["past_perfect", "conditionals"],
    "vocabulary_tier": 4,
    "sentence_complexity": 0.7
  }
}
```

### 4.3 Indexing Strategy

```sql
-- Primary queries and their indexes:

-- "Get user's latest skill profile" (every session start)
CREATE INDEX idx_motor_skill_user ON motor_skill_profiles(user_id);
CREATE INDEX idx_cognitive_skill_user ON cognitive_skill_profiles(user_id);

-- "Find passages matching difficulty vector" (passage selection)
-- GIN index on JSONB for flexible querying
CREATE INDEX idx_passage_difficulty ON passages USING GIN (difficulty_vec);
CREATE INDEX idx_passage_grammar_tags ON passages USING GIN (grammar_tags);

-- "Get user's recent sessions" (analytics, trend detection)
CREATE INDEX idx_sessions_user_time ON typing_sessions(user_id, completed_at DESC);

-- Partial index: only completed sessions for analytics
CREATE INDEX idx_sessions_completed ON typing_sessions(user_id, completed_at)
  WHERE completed_at IS NOT NULL;
```

### 4.4 Migration Strategy

Use **Alembic** with strict discipline:
- Every schema change = a migration file
- Migrations are version-controlled
- Both `upgrade()` and `downgrade()` are implemented
- Test migrations against a copy of production data before applying

---

## 5. Adaptive Algorithm Design

This is the intellectual heart of the system.

### 5.1 The Difficulty Vector

Every passage and every user state can be represented as a point in a multi-dimensional "difficulty space":

```
Motor Dimensions:              Cognitive Dimensions:
├── target_wpm (10-150)        ├── grammar_level (1-10)
├── key_difficulty (0-1)       ├── vocabulary_tier (1-10)
├── bigram_difficulty (0-1)    ├── sentence_complexity (0-1)
├── word_length_avg (3-12)     └── target_grammar_constructs[]
└── punctuation_density (0-1)
```

### 5.2 Adaptation Algorithm (Pseudocode)

```python
def select_next_passage(user_model: UserModel) -> DifficultyVector:
    """
    Core adaptation logic.

    Principle: Challenge the WEAKER skill while keeping the
    STRONGER skill in the comfort zone.
    """
    motor = user_model.motor_profile
    cognitive = user_model.cognitive_profile

    # Step 1: Compute relative skill levels (normalized 0-1)
    motor_level = normalize(motor.overall_wpm, motor.accuracy)
    cognitive_level = normalize(cognitive.grammar_level, cognitive.vocab_tier)

    # Step 2: Determine which skill to challenge
    skill_gap = motor_level - cognitive_level

    if abs(skill_gap) < THRESHOLD:
        # Skills are balanced — advance both slightly
        strategy = "balanced_advance"
    elif skill_gap > 0:
        # Motor > Cognitive — challenge English, keep typing easy
        strategy = "challenge_cognitive"
    else:
        # Cognitive > Motor — challenge typing, keep English easy
        strategy = "challenge_motor"

    # Step 3: Build target difficulty vector
    target = DifficultyVector()

    if strategy == "challenge_cognitive":
        target.motor = motor.comfort_zone()           # Stay comfortable
        target.cognitive = cognitive.next_level()      # Push the edge
        target.cognitive.grammar_targets = cognitive.weakest_areas(n=2)

    elif strategy == "challenge_motor":
        target.cognitive = cognitive.comfort_zone()    # Familiar English
        target.motor = motor.next_level()              # Push typing
        target.motor.key_focus = motor.weakest_keys(n=3)
        target.motor.bigram_focus = motor.slowest_bigrams(n=3)

    else:  # balanced
        target.motor = motor.slight_stretch()
        target.cognitive = cognitive.slight_stretch()

    # Step 4: Apply spaced repetition for weak areas
    target = apply_spaced_repetition(target, user_model.history)

    return target
```

### 5.3 Skill Update After Session

```python
def update_user_model(user_model: UserModel, session: CompletedSession):
    """
    Update both skill dimensions based on session performance.
    Uses exponential moving average to smooth out variance.
    """
    alpha = 0.3  # Learning rate — how much new data influences the model

    # Motor skill update
    motor = user_model.motor_profile
    motor.overall_wpm = ema(motor.overall_wpm, session.wpm, alpha)
    motor.overall_accuracy = ema(motor.overall_accuracy, session.accuracy, alpha)

    for key, stats in session.per_key_stats.items():
        existing = motor.key_profiles.get(key, KeyProfile.default())
        existing.avg_ms = ema(existing.avg_ms, stats.avg_ms, alpha)
        existing.error_rate = ema(existing.error_rate, stats.error_rate, alpha)
        existing.samples += stats.samples

    # Cognitive skill update
    # Inferred from typing behavior on grammar-tagged passages
    cognitive = user_model.cognitive_profile

    passage = session.passage
    if session.accuracy > MASTERY_THRESHOLD:
        # User typed grammar constructs accurately and quickly
        # → they likely understand them. Level up.
        for tag in passage.grammar_tags:
            cognitive.advance(tag)
    elif session.accuracy < STRUGGLE_THRESHOLD:
        # User stumbled on these constructs
        # Distinguish: was it motor difficulty or cognitive?
        if motor_was_comfortable(session):
            # Motor was fine, so errors likely cognitive
            for tag in passage.grammar_tags:
                cognitive.mark_weak(tag)

    return user_model
```

### 5.4 Disentangling Motor vs. Cognitive Errors

This is the hardest algorithmic challenge. When a user makes an error on "they're", is it a typo (motor) or a confusion with "their" (cognitive)?

Heuristics:
1. **Timing signal**: Motor errors tend to have fast, impulsive keystrokes followed by backspace. Cognitive hesitation shows long pauses before the word.
2. **Pattern signal**: If a user consistently types "their" when the passage says "they're", that's cognitive. Random character substitutions are motor.
3. **Context signal**: If the user's motor profile shows 'e' and 'r' are problematic keys, weight toward motor error.
4. **Correction signal**: Quick self-correction (backspace within 500ms) suggests motor slip. No correction suggests the user believes they're right (cognitive).

---

## 6. LLM Integration & Passage Pipeline

### 6.1 The Passage Pipeline

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Adaptation  │────▶│   Passage     │────▶│    Cache     │
│   Engine     │     │   Selector    │     │   (Redis)    │
│              │     │               │     │              │
│  Outputs:    │     │  1. Check     │     │  TTL: 24hr   │
│  Difficulty  │     │     Redis     │     │  Key: hash   │
│  Vector      │     │  2. Check DB  │     │  of diff_vec │
│              │     │  3. Generate  │     └──────────────┘
└──────────────┘     │     async     │
                     └───────┬───────┘
                             │ cache miss
                             ▼
                     ┌───────────────┐     ┌──────────────┐
                     │  Celery Task  │────▶│  Anthropic   │
                     │               │     │  Claude API  │
                     │  - Build      │     │              │
                     │    prompt     │     │  Model:      │
                     │  - Call LLM   │     │  claude-     │
                     │  - Validate   │     │  sonnet      │
                     │  - Tag grammar│     └──────────────┘
                     │  - Compute    │
                     │    metadata   │
                     │  - Store in   │
                     │    DB + Redis │
                     └───────────────┘
```

### 6.2 Prompt Engineering for Passage Generation

```python
PASSAGE_GENERATION_PROMPT = """
You are a typing practice passage generator for an adaptive learning system.

Generate a passage with these EXACT constraints:

MOTOR SKILL TARGETS:
- Word count: {word_count} (±5 words)
- Must include these characters frequently: {target_keys}
- Must include these bigrams frequently: {target_bigrams}
- Average word length: ~{avg_word_length} characters

COGNITIVE SKILL TARGETS:
- Grammar level: {grammar_level}/10
- Must use these grammar structures: {grammar_targets}
- Vocabulary tier: {vocab_tier}/10
- Sentence complexity: {complexity}/1.0

CONSTRAINTS:
- The passage must read naturally — not forced or awkward
- Topic should be engaging and informational
- No proper nouns (they bias typing difficulty)
- No numbers (they require different motor skills)
- Return ONLY the passage text, no explanations

TOPIC SUGGESTION: {topic}
"""
```

### 6.3 Passage Validation Pipeline

After LLM generates a passage, validate before storing:

```python
async def validate_passage(text: str, target: DifficultyVector) -> ValidationResult:
    checks = [
        check_word_count(text, target.word_count, tolerance=5),
        check_key_frequency(text, target.motor.key_focus),
        check_grammar_tags(text, target.cognitive.grammar_targets),  # use spaCy
        check_vocabulary_tier(text, target.cognitive.vocabulary_tier),
        check_no_proper_nouns(text),
        check_readability_score(text),  # Flesch-Kincaid
        check_not_duplicate(text),  # embedding similarity vs existing passages
    ]
    return ValidationResult(
        passed=all(c.passed for c in checks),
        failures=[c for c in checks if not c.passed]
    )
```

### 6.4 Caching Strategy

```
Cache key = hash(difficulty_vector_quantized)

Quantization: Round difficulty dimensions to discrete levels
to increase cache hit rate.

Example:
  Raw vector:    { wpm: 47.3, grammar: 3.7, vocab: 4.2 }
  Quantized:     { wpm: 45,   grammar: 4,   vocab: 4   }
  Cache key:     "passage:wpm45:g4:v4:keys_qz"

Cache stores a LIST of passages per key (not just one),
so users don't repeatedly see the same passage.

Eviction: LRU with 24-hour TTL.
Pre-warming: Background job generates passages for common
difficulty vectors during low-traffic hours.
```

---

## 7. Distributed Systems Patterns

Even though you're the only user, architect these patterns for learning.

### 7.1 Patterns Implemented in TypeLingo

| Pattern | Where Applied | What You'll Learn |
|---|---|---|
| **Queue-based load leveling** | Celery + Redis for LLM calls | Decouple producers from consumers, handle backpressure |
| **Circuit breaker** | LLM API client | Graceful degradation when external service is down |
| **Cache-aside** | Redis passage cache | Cache invalidation, thundering herd prevention |
| **CQRS (lightweight)** | Session writes vs. analytics reads | Separate write-optimized and read-optimized paths |
| **Event sourcing (lightweight)** | Keystroke event log | Immutable event stream, replay for analytics |
| **Saga pattern** | Passage generation pipeline | Multi-step async workflow with compensation |
| **Bulkhead** | Separate thread pools for DB/Cache/LLM | Failure isolation between dependencies |
| **Retry with exponential backoff** | All external calls | Resilient communication |
| **Health checks** | `/health`, `/ready` endpoints | Liveness vs. readiness probes |

### 7.2 Circuit Breaker Implementation

```python
class CircuitBreaker:
    """
    States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)

    When the LLM API fails repeatedly:
    1. CLOSED: Requests go through normally
    2. After N failures → OPEN: All requests fail immediately (no API call)
    3. After timeout → HALF_OPEN: Allow one test request
    4. If test succeeds → CLOSED. If fails → OPEN again.
    """
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.state = "CLOSED"
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time_since(self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit is OPEN, using fallback")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = now()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

### 7.3 Graceful Degradation Strategy

```
LLM API Down:
  └─→ Circuit breaker OPEN
  └─→ Serve passages from PostgreSQL cache
  └─→ If DB has no match, serve from pre-seeded fallback set
  └─→ Log degradation event, increment metric
  └─→ Background: retry LLM when circuit half-opens

Database Down:
  └─→ Serve passages from Redis cache
  └─→ Accept typing sessions, buffer in Redis
  └─→ Flush to DB when recovered
  └─→ Alert via metrics (p99 latency spike)

Redis Down:
  └─→ Fall through to PostgreSQL for everything
  └─→ Disable real-time stats (accept degradation)
  └─→ Log warning, continue serving
```

---

## 8. API Design

### 8.1 REST API Endpoints

```
Authentication:
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  POST   /api/v1/auth/refresh
  POST   /api/v1/auth/logout

User Profile:
  GET    /api/v1/users/me
  GET    /api/v1/users/me/skills          # Current dual-skill model
  GET    /api/v1/users/me/skills/history   # Skill progression over time

Typing Sessions:
  POST   /api/v1/sessions                 # Start new session (returns passage)
  GET    /api/v1/sessions/{id}            # Get session details
  POST   /api/v1/sessions/{id}/complete   # Submit completed session
  GET    /api/v1/sessions/history          # Past sessions with filters

Passages:
  GET    /api/v1/passages/next            # Get next adapted passage
  GET    /api/v1/passages/{id}            # Get specific passage

Analytics:
  GET    /api/v1/analytics/overview       # Dashboard data
  GET    /api/v1/analytics/motor          # Typing skill trends
  GET    /api/v1/analytics/cognitive      # Language skill trends
  GET    /api/v1/analytics/keys           # Per-key heatmap data

WebSocket:
  WS     /ws/v1/sessions/{id}/stream      # Real-time keystroke streaming
```

### 8.2 Request/Response Examples

```json
// POST /api/v1/sessions — Start a new typing session
// Response 201:
{
  "session_id": "sess_abc123",
  "passage": {
    "id": "pass_xyz789",
    "content": "The quiet fox realized that every experience...",
    "word_count": 42,
    "difficulty": {
      "motor": { "target_wpm": 45, "key_focus": ["q", "x"] },
      "cognitive": { "grammar_level": 3, "targets": ["past_simple"] }
    }
  },
  "adaptation_reason": "Challenging cognitive skill (grammar level 2→3) while maintaining motor comfort zone (45 WPM)"
}

// POST /api/v1/sessions/{id}/complete
// Request:
{
  "keystrokes": [
    { "key": "T", "timestamp_ms": 0, "correct": true },
    { "key": "h", "timestamp_ms": 85, "correct": true },
    { "key": "r", "timestamp_ms": 162, "correct": false },  // error
    { "key": "Backspace", "timestamp_ms": 230 },
    { "key": "e", "timestamp_ms": 310, "correct": true },
    ...
  ],
  "started_at": "2025-06-15T10:30:00Z",
  "completed_at": "2025-06-15T10:32:45Z"
}

// Response 200:
{
  "session_id": "sess_abc123",
  "results": {
    "wpm": 47.2,
    "accuracy": 0.943,
    "duration_seconds": 165,
    "per_key_performance": {
      "q": { "avg_ms": 195, "errors": 2, "total": 5 },
      "e": { "avg_ms": 78, "errors": 0, "total": 34 }
    },
    "skill_updates": {
      "motor": { "wpm_delta": +1.3, "accuracy_delta": -0.01 },
      "cognitive": { "grammar_level": "3 (no change)", "note": "past_simple mastery improving" }
    }
  },
  "next_recommendation": "Your 'q' key is still slow. Next session will include more q-heavy words."
}
```

### 8.3 API Versioning Strategy

Use URL-based versioning (`/api/v1/`, `/api/v2/`) for clarity. When introducing breaking changes, maintain the old version for a deprecation period. Non-breaking additions (new fields, new endpoints) go into the current version.

---

## 9. SRE & Observability

### 9.1 SLOs (Service Level Objectives)

| Metric | SLO | Measurement |
|---|---|---|
| Availability | 99.9% | Successful responses / total requests |
| API latency (p50) | < 50ms | Excluding LLM generation |
| API latency (p99) | < 200ms | Excluding LLM generation |
| Passage generation | < 10s | From request to passage available |
| WebSocket latency | < 20ms | Keystroke event round-trip |
| Data durability | 99.999% | No session data loss |

### 9.2 Structured Logging

```python
# Every log line is structured JSON with context
import structlog

logger = structlog.get_logger()

# Middleware attaches request context automatically
logger.info(
    "session_completed",
    user_id="usr_123",
    session_id="sess_abc",
    wpm=47.2,
    accuracy=0.943,
    passage_source="cache",      # cache | db | llm | fallback
    duration_ms=165000,
    request_id="req_xyz",        # Trace correlation
)

# Produces:
# {
#   "event": "session_completed",
#   "user_id": "usr_123",
#   "session_id": "sess_abc",
#   "wpm": 47.2,
#   "accuracy": 0.943,
#   "passage_source": "cache",
#   "duration_ms": 165000,
#   "request_id": "req_xyz",
#   "timestamp": "2025-06-15T10:32:45.123Z",
#   "level": "info"
# }
```

### 9.3 Prometheus Metrics

```python
# Key metrics to instrument

# RED method — for every endpoint
http_requests_total         # Counter: {method, endpoint, status}
http_request_duration_ms    # Histogram: {method, endpoint}
http_errors_total           # Counter: {method, endpoint, error_type}

# Business metrics
typing_sessions_completed   # Counter
typing_session_wpm          # Histogram (distribution of WPM scores)
typing_session_accuracy     # Histogram
passage_cache_hits_total    # Counter
passage_cache_misses_total  # Counter
passage_generation_duration # Histogram (LLM latency)
skill_level_updates         # Counter: {skill_type, direction}

# Infrastructure metrics
db_connection_pool_size     # Gauge
db_query_duration_ms        # Histogram: {query_name}
redis_connection_pool_size  # Gauge
celery_tasks_queued         # Gauge
celery_tasks_succeeded      # Counter
celery_tasks_failed         # Counter
circuit_breaker_state       # Gauge: 0=closed, 1=open, 2=half-open
```

### 9.4 Alerting Rules

```yaml
# Alert when things matter, not when they're noisy

- alert: HighErrorRate
  expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 2m
  summary: "Error rate above 5% for 2 minutes"

- alert: HighP99Latency
  expr: histogram_quantile(0.99, http_request_duration_ms) > 500
  for: 5m
  summary: "p99 latency above 500ms for 5 minutes"

- alert: LLMCircuitOpen
  expr: circuit_breaker_state == 1
  for: 1m
  summary: "LLM circuit breaker is OPEN — serving from cache"

- alert: PassageCacheHitRateLow
  expr: rate(passage_cache_hits_total[1h]) /
        (rate(passage_cache_hits_total[1h]) + rate(passage_cache_misses_total[1h])) < 0.5
  for: 30m
  summary: "Cache hit rate below 50% — check cache warming"
```

### 9.5 Dashboards (Grafana)

```
Dashboard 1: System Health
├── Request rate (req/s)
├── Error rate (%)
├── Latency percentiles (p50, p95, p99)
├── Active WebSocket connections
└── Resource utilization (CPU, memory, connections)

Dashboard 2: Passage Pipeline
├── Cache hit rate (%)
├── LLM generation latency distribution
├── Passages generated per hour
├── Circuit breaker state timeline
└── Celery queue depth

Dashboard 3: User Learning (Business)
├── Sessions completed per day
├── Average WPM trend
├── Average accuracy trend
├── Skill level distribution
└── Most common weak keys / grammar areas
```

---

## 10. TDD & Testing Strategy

### 10.1 Testing Pyramid

```
        ╱ ╲
       ╱ E2E ╲         2-3 tests: Full user flow through browser
      ╱───────╲
     ╱ Integr- ╲       10-15 tests: API → DB, Passage pipeline
    ╱  ation    ╲
   ╱─────────────╲
  ╱    Unit       ╲    50+ tests: Domain logic, pure functions
 ╱─────────────────╲
```

### 10.2 TDD Workflow Example

```python
# Step 1: RED — Write the failing test first

# tests/unit/domain/test_scoring.py
def test_wpm_calculation_basic():
    """WPM = (characters typed / 5) / minutes elapsed"""
    keystrokes = make_keystrokes(chars=250, duration_seconds=60)
    result = calculate_wpm(keystrokes)
    assert result == 50.0  # 250/5 = 50 words in 1 minute

def test_wpm_excludes_backspaced_characters():
    """Backspaced characters should not count toward WPM."""
    keystrokes = [
        *make_correct_keystrokes(240),
        make_keystroke("x", correct=False),
        make_keystroke("Backspace"),
        *make_correct_keystrokes(10),  # 250 correct chars total
    ]
    set_duration(keystrokes, seconds=60)
    result = calculate_wpm(keystrokes)
    assert result == 50.0  # Only 250 correct chars count

def test_accuracy_calculation():
    keystrokes = [
        *make_correct_keystrokes(95),
        *make_incorrect_keystrokes(5),
    ]
    result = calculate_accuracy(keystrokes)
    assert result == 0.95

# Step 2: GREEN — Write minimum code to pass
# src/domain/services/scoring.py
def calculate_wpm(keystrokes: list[KeystrokeEvent]) -> float:
    correct_chars = sum(1 for k in keystrokes if k.correct)
    words = correct_chars / 5
    minutes = (keystrokes[-1].timestamp - keystrokes[0].timestamp) / 60000
    return round(words / minutes, 1)

# Step 3: REFACTOR — Clean up while tests stay green
```

### 10.3 Test Categories

```python
# UNIT: Pure domain logic, no I/O
class TestAdaptationEngine:
    def test_challenges_cognitive_when_motor_is_stronger(self):
        user = make_user(motor_level=0.8, cognitive_level=0.3)
        vector = adaptation_engine.compute_target(user)
        assert vector.cognitive.grammar_level > user.cognitive.grammar_level
        assert vector.motor.target_wpm <= user.motor.comfort_wpm

    def test_challenges_motor_when_cognitive_is_stronger(self):
        user = make_user(motor_level=0.3, cognitive_level=0.8)
        vector = adaptation_engine.compute_target(user)
        assert vector.motor.target_wpm > user.motor.overall_wpm
        assert vector.cognitive.grammar_level <= user.cognitive.grammar_level

    def test_balanced_advance_when_skills_are_close(self):
        user = make_user(motor_level=0.5, cognitive_level=0.48)
        vector = adaptation_engine.compute_target(user)
        # Both should advance slightly
        assert vector.motor.target_wpm > user.motor.overall_wpm
        assert vector.cognitive.grammar_level >= user.cognitive.grammar_level


# INTEGRATION: Real DB, real cache
@pytest.mark.integration
class TestPassagePipeline:
    async def test_returns_cached_passage_on_hit(self, redis, db):
        passage = make_passage(difficulty=easy_vector)
        await redis.set(cache_key(easy_vector), passage)
        result = await passage_service.get_passage(easy_vector)
        assert result.id == passage.id
        assert result.source == "cache"

    async def test_falls_back_to_db_on_cache_miss(self, redis, db):
        passage = make_passage(difficulty=easy_vector)
        await db.store_passage(passage)
        # Redis is empty
        result = await passage_service.get_passage(easy_vector)
        assert result.id == passage.id
        assert result.source == "database"


# E2E: Full flow
@pytest.mark.e2e
class TestFullSession:
    async def test_complete_typing_session_updates_user_model(self, client):
        # Register and login
        token = await register_and_login(client)

        # Start session
        resp = await client.post("/api/v1/sessions", headers=auth(token))
        session_id = resp.json()["session_id"]
        passage = resp.json()["passage"]["content"]

        # Simulate typing
        keystrokes = simulate_typing(passage, wpm=40, accuracy=0.95)

        # Complete session
        resp = await client.post(
            f"/api/v1/sessions/{session_id}/complete",
            json={"keystrokes": keystrokes},
            headers=auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["results"]["wpm"] > 0

        # Verify skill model was updated
        resp = await client.get("/api/v1/users/me/skills", headers=auth(token))
        skills = resp.json()
        assert skills["motor"]["overall_wpm"] > 0
```

### 10.4 Test Fixtures & Factories

```python
# tests/factories.py — Test data builders
# Using the Factory pattern for readable, flexible test data

def make_user(
    motor_level: float = 0.5,
    cognitive_level: float = 0.5,
    weak_keys: list[str] | None = None,
    weak_grammar: list[str] | None = None,
) -> UserModel:
    return UserModel(
        id="test_user",
        motor_profile=MotorSkillProfile(
            overall_wpm=motor_level * 100,
            overall_accuracy=0.85 + motor_level * 0.1,
            key_profiles=make_key_profiles(weak_keys or []),
        ),
        cognitive_profile=CognitiveSkillProfile(
            grammar_level=int(cognitive_level * 10),
            vocabulary_tier=int(cognitive_level * 10),
            weak_areas=weak_grammar or [],
        ),
    )

def make_keystrokes(chars: int = 100, duration_seconds: int = 60) -> list:
    interval_ms = (duration_seconds * 1000) / chars
    return [
        KeystrokeEvent(key=chr(97 + (i % 26)), timestamp_ms=int(i * interval_ms), correct=True)
        for i in range(chars)
    ]
```

---

## 11. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml

name: TypeLingo CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint (ruff)
        run: ruff check src/ tests/

      - name: Format check (ruff)
        run: ruff format --check src/ tests/

      - name: Type check (mypy)
        run: mypy src/ --strict

  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src/domain --cov-fail-under=90

  test-integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: typelingo_test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/typelingo_test
          REDIS_URL: redis://localhost:6379

  deploy-staging:
    needs: [quality, test-unit, test-integration]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: echo "Deploy to staging environment"
        # Docker build → push → deploy to staging server
```

---

## 12. Security

### Authentication Flow

```
Registration:
  Client → POST /auth/register { email, password }
  Server → Hash password (bcrypt, cost=12)
  Server → Store user, return JWT pair (access + refresh)

Login:
  Client → POST /auth/login { email, password }
  Server → Verify bcrypt hash
  Server → Issue JWT (access: 15min, refresh: 7 days)
  Server → Set refresh token as httponly cookie

Protected Request:
  Client → GET /api/v1/... + Authorization: Bearer <access_token>
  Server → Verify JWT signature + expiration
  Server → Extract user_id from claims

Token Refresh:
  Client → POST /auth/refresh (httponly cookie sent automatically)
  Server → Verify refresh token
  Server → Issue new access token
```

### Security Checklist

- [ ] Passwords: bcrypt with cost factor 12+
- [ ] JWTs: RS256 (asymmetric), short-lived access tokens
- [ ] CORS: Whitelist only your frontend origin
- [ ] Rate limiting: Per-IP and per-user (Redis-backed)
- [ ] Input validation: Pydantic models on every endpoint
- [ ] SQL injection: SQLAlchemy parameterized queries (never raw SQL)
- [ ] XSS: Content-Security-Policy headers
- [ ] CSRF: SameSite cookies + CSRF token for state-changing requests
- [ ] Secrets: Environment variables, never in code
- [ ] Dependencies: Dependabot / pip-audit in CI
- [ ] HTTPS: Enforced everywhere (HSTS header)

---

## 13. Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | Next.js + TypeScript | SSR, great DX, strong typing |
| **Backend** | Python 3.12 + FastAPI | Async, type hints, rapid development |
| **Database** | PostgreSQL 16 | ACID, JSONB, mature, battle-tested |
| **Cache** | Redis 7 | Fast, versatile (cache + queue + pub/sub) |
| **Task Queue** | Celery + Redis broker | Async LLM generation, background jobs |
| **LLM** | Anthropic Claude API | Passage generation |
| **NLP** | spaCy | Grammar tagging, sentence analysis |
| **ORM** | SQLAlchemy 2.0 (async) | Type-safe queries, migration support |
| **Migrations** | Alembic | Version-controlled schema changes |
| **Auth** | python-jose + bcrypt | JWT handling + password hashing |
| **Testing** | pytest + pytest-asyncio | Async test support, fixtures, coverage |
| **Linting** | ruff | Fast, replaces flake8 + isort + black |
| **Type Check** | mypy (strict) | Catch bugs before runtime |
| **Logging** | structlog | Structured JSON logging |
| **Metrics** | prometheus-client | RED method metrics |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **CI/CD** | GitHub Actions | Automated quality gates |
| **Container** | Docker + docker-compose | Reproducible local dev environment |
| **Load Test** | Locust or k6 | Performance benchmarking |

---

## 14. Project Phases & Milestones

### Phase 1: Foundation (Weeks 1-2)
- [ ] Project setup: repo, Docker, CI pipeline, linting, type checking
- [ ] Database schema + Alembic migrations
- [ ] Domain models (User, MotorSkill, CognitiveSkill, Passage, Session)
- [ ] Repository interfaces + PostgreSQL implementations
- [ ] Auth endpoints (register, login, refresh)
- [ ] Health check endpoints
- [ ] Unit tests for all domain models
- **Milestone: Can register, login, and hit API endpoints**

### Phase 2: Core Typing Engine (Weeks 3-4)
- [ ] WebSocket handler for keystroke streaming
- [ ] Scoring service (WPM, accuracy, per-key stats) — TDD
- [ ] Session management (start, stream, complete)
- [ ] Skill update logic — TDD
- [ ] Pre-seed passage database (50-100 hand-crafted passages)
- [ ] Basic passage selection (random from appropriate difficulty)
- [ ] Integration tests for full session flow
- **Milestone: Can complete a typing session and see results**

### Phase 3: Adaptive Algorithm (Weeks 5-6)
- [ ] Difficulty vector model
- [ ] Adaptation engine (dual-skill targeting) — TDD
- [ ] Passage selector (match passages to difficulty vectors)
- [ ] Skill disentanglement heuristics
- [ ] Spaced repetition integration
- [ ] Unit tests for all adaptation scenarios
- **Milestone: Passages adapt to user performance**

### Phase 4: LLM Pipeline (Weeks 7-8)
- [ ] Celery setup with Redis broker
- [ ] LLM client with circuit breaker
- [ ] Prompt engineering for passage generation
- [ ] Passage validation pipeline
- [ ] Cache layer (Redis) with quantized keys
- [ ] Fallback chain (cache → DB → fallback set)
- [ ] Integration tests for full pipeline
- **Milestone: System generates and caches adapted passages**

### Phase 5: Observability & SRE (Weeks 9-10)
- [ ] Structured logging (structlog) across all services
- [ ] Prometheus metrics (RED method + business metrics)
- [ ] Grafana dashboards (system health, pipeline, business)
- [ ] Alerting rules
- [ ] OpenTelemetry tracing
- [ ] Load testing with Locust/k6
- [ ] Runbooks for common failure scenarios
- **Milestone: Full observability, can identify and diagnose issues**

### Phase 6: Frontend & Polish (Weeks 11-12)
- [ ] Typing interface (keystroke capture, real-time feedback)
- [ ] Dashboard (skill progression, per-key heatmap)
- [ ] Session history and analytics views
- [ ] Responsive design
- [ ] E2E tests
- **Milestone: Fully functional application**

### Phase 7: Advanced (Ongoing)
- [ ] Extract a service (e.g., Passage Service) into its own microservice with gRPC
- [ ] Implement event sourcing for keystroke events
- [ ] Add Kubernetes deployment manifests
- [ ] Implement A/B testing framework for adaptation algorithms
- [ ] Add difficulty vector embeddings for semantic passage matching
- [ ] Performance optimization based on load test results

---

## Appendix: Key Design Decisions Log

Document every significant decision. This is your engineering journal.

| Date | Decision | Options Considered | Chosen | Rationale |
|---|---|---|---|---|
| Day 1 | Architecture | Microservices, Modular monolith | Modular monolith | Single dev, need speed. Clear boundaries allow future extraction. |
| Day 1 | Database | PostgreSQL, MongoDB | PostgreSQL | ACID for user data, JSONB for flexibility. Structured + semi-structured. |
| Day 1 | Skill storage | Separate tables per key, JSONB blob | JSONB | Always read/written atomically. No need for per-key queries. |
| Day 1 | LLM strategy | Real-time, Pre-generated, Hybrid | Hybrid | Balance freshness with latency. Cache aggressively. |
| Day 1 | API versioning | URL, Header, Query param | URL (/v1/) | Most explicit, easiest to maintain. |
| ... | ... | ... | ... | ... |

**Keep adding to this table as you build. Future you will thank present you.**
