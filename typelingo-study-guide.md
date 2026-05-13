# TypeLingo — Study & Preparation Guide
### Everything you need to learn before (and while) building TypeLingo

The goal: you make every decision. This guide prepares you to understand the trade-offs deeply enough to choose confidently.

---

## How to Use This Guide

Each section maps to a real decision you'll face while building TypeLingo. For each topic:

1. **Study the material** — books, chapters, videos, hands-on exercises
2. **Answer the reflection questions** — these force you to think about trade-offs, not just memorize
3. **Do the mini-project** — a small, isolated exercise that gives you direct experience
4. **Then make your decision for TypeLingo** — document it in a decision log with your rationale

Don't study everything upfront. Follow the phase order. Learn what you need for the next decision, build, then learn the next thing.

---

## Phase 0: Foundations You Need Before Anything Else

### 0.1 — How the Internet Actually Works

Before building a web app, understand what happens when a user hits your URL.

**Study:**
- "How DNS Works" — comic by dnsimple (free, visual, 20 min): https://howdns.works/
- "What happens when you type google.com into your browser" — GitHub repo (the classic): https://github.com/alex/what-happens-when
- MDN: "How the Web Works": https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/How_the_Web_works
- HTTP crash course — Traversy Media (YouTube, 40 min)
- "High Performance Browser Networking" by Ilya Grigorik (free online): https://hpbn.co/ — Chapters 1-4 (TCP, TLS, HTTP)

**Reflection Questions:**
- What's the difference between TCP and UDP? Why does HTTP use TCP?
- What happens at each layer (DNS → TCP → TLS → HTTP) when your browser requests a page?
- What is a reverse proxy, and why would you put one in front of your app?
- What's the difference between HTTP/1.1, HTTP/2, and HTTP/3? Why does it matter?
- What is a WebSocket, and how does it differ from a regular HTTP connection? Why would you use one for real-time keystroke streaming?

**Mini-project:**
- Use `curl -v` to make a request and read every line of the output. Understand each header.
- Use Wireshark or `tcpdump` to capture a TCP handshake. See the SYN → SYN-ACK → ACK.
- Write a raw TCP server in Python using the `socket` module that responds to HTTP requests manually (no framework). This is eye-opening.

---

### 0.2 — Python Deep Dive (Beyond the Basics)

You're building in Python. Make sure your foundation is rock solid.

**Study:**
- "Fluent Python" by Luciano Ramalho — Chapters on data model, decorators, generators, async
- "Architecture Patterns with Python" by Harry Percival & Bob Gregory — THE book for your project. Covers repository pattern, service layer, unit of work, dependency injection, all in Python.
- Python `asyncio` docs + "asyncio in-depth" tutorial: understand event loops, coroutines, tasks, and `await`
- Type hints deep dive: `typing` module, generics, protocols, `TypeVar`, `ParamSpec`

**Reflection Questions:**
- What is the GIL and how does it affect your web server's concurrency?
- What's the difference between `threading`, `multiprocessing`, and `asyncio`? When would you use each?
- Why does FastAPI use `async def` for route handlers? What happens if you use `def` instead?
- What is a Python protocol (structural subtyping) and how does it differ from an ABC? Which would you use for your repository interfaces?
- What does `yield` do in a dependency injection context (FastAPI's `Depends`)?

**Mini-project:**
- Build a tiny async HTTP server using only `asyncio` (no framework). Handle 3 routes.
- Implement a repository pattern: define an abstract `UserRepository`, then implement `InMemoryUserRepository` and `PostgresUserRepository`. Write tests against the abstract interface that work with both.

---

### 0.3 — Git Mastery

You'll use Git every day. Go beyond `add`, `commit`, `push`.

**Study:**
- "Pro Git" book — Chapters 2, 3, 7 (free online): https://git-scm.com/book/en/v2
- "Oh Shit, Git!?" (practical fixes for common mistakes): https://ohshitgit.com/
- Conventional Commits specification: https://www.conventionalcommits.org/

**Reflection Questions:**
- What's the difference between `merge` and `rebase`? When would you use each?
- What does `git reflog` do and why is it your safety net?
- How does `git bisect` work and when would you use it to find a bug?
- What branching strategy will you use for TypeLingo? Why?

**Mini-project:**
- Create a repo, make 10 commits, then use `interactive rebase` to squash, reorder, and edit messages.
- Intentionally create a merge conflict, then resolve it manually. Do this 5 times until it's not scary.
- Use `git bisect` to find which commit introduced a bug in a sample project.

---

## Phase 1: Architecture & System Design

### 1.1 — Software Architecture Patterns

This is the biggest decision you'll make. Understand the options before choosing.

**Study:**
- "Fundamentals of Software Architecture" by Mark Richards & Neal Ford — Chapters 1-5, 9-12. Covers monolith, microservices, service-based, event-driven, and how to evaluate trade-offs.
- "Building Microservices" by Sam Newman — Chapters 1-3 (read even if you don't go microservices — it teaches you what problems they solve and what problems they create)
- "Monolith First" by Martin Fowler (article): https://martinfowler.com/bliki/MonolithFirst.html
- "The Majestic Monolith" by DHH (article): https://signalvnoise.com/svn3/the-majestic-monolith/
- "Modular Monolith" by Kamil Grzybek (GitHub + articles): https://github.com/kgrzybek/modular-monolith-with-ddd

**Reflection Questions:**
- What are the operational costs of microservices that a monolith doesn't have? (Think: deployment, debugging, data consistency, latency)
- What does "distributed monolith" mean and why is it the worst of both worlds?
- If you start with a monolith, what design decisions now will make it easier to extract services later?
- For TypeLingo specifically: which components might need to scale independently? Does that justify microservices today or is it premature?
- What is the difference between a "modular monolith" and just "good code organization"?

**Mini-project:**
- Draw 3 different architecture diagrams for TypeLingo: (a) pure monolith, (b) modular monolith, (c) microservices. For each, list the pros, cons, and operational requirements. Then pick one and write a paragraph defending your choice.

---

### 1.2 — Hexagonal Architecture / Clean Architecture / Ports & Adapters

This determines how you structure code within your application.

**Study:**
- "Architecture Patterns with Python" by Percival & Gregory — the entire book. This is your #1 resource. It walks through building a real Python app with repository pattern, service layer, unit of work, and dependency injection. Read it cover to cover.
- "Clean Architecture" by Robert C. Martin — Chapters 15-22 (the architecture chapters; skip the early OOP stuff if you want)
- Alistair Cockburn's original "Hexagonal Architecture" article: https://alistair.cockburn.us/hexagonal-architecture/
- "Dependency Inversion Principle" — understand it deeply. It's the core idea behind all of this.

**Reflection Questions:**
- What is the difference between "Ports & Adapters", "Clean Architecture", and "Hexagonal Architecture"? (Trick question — they're mostly the same idea)
- Why should your domain layer have zero knowledge of your database or framework?
- What is the "Dependency Rule" and which direction should dependencies point?
- How does the repository pattern make your domain testable without a database?
- In your TypeLingo project, what are the "ports" (interfaces) and what are the "adapters" (implementations)?

**Mini-project:**
- Build a tiny task manager app with hexagonal architecture: domain models (`Task`, `TaskList`), a service layer, a repository interface, an in-memory implementation, and a SQLite implementation. Write unit tests that use the in-memory adapter. Then swap to SQLite and watch all tests still pass.

---

### 1.3 — API Design

You'll design the contract between your frontend and backend.

**Study:**
- Read Stripe's API docs end to end (the gold standard): https://stripe.com/docs/api
- Read GitHub's REST API docs for comparison: https://docs.github.com/en/rest
- "RESTful Web API Patterns and Practices Cookbook" by Mike Amundsen — Chapters 1-6
- HTTP status codes: memorize the important ones (200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500, 503)
- Learn about idempotency — why it matters and how to implement it

**Reflection Questions:**
- What makes an API "RESTful"? What are the Richardson Maturity Model levels?
- When would you choose GraphQL over REST? What are the downsides of GraphQL?
- What is idempotency and why does it matter for `POST` requests? How would you implement it?
- How should you handle API versioning? What are the trade-offs of URL-based vs header-based?
- How should you design error responses? What information should they include?
- For TypeLingo: should keystroke streaming be REST, WebSocket, or Server-Sent Events? Why?

**Mini-project:**
- Design the TypeLingo API on paper first. Write out every endpoint, its method, URL, request body, response body, and possible error codes. Don't build it yet — just design it.
- Study 3 APIs you admire (Stripe, Twilio, GitHub). Write down 5 design patterns they all share.

---

### 1.4 — WebSocket & Real-Time Communication

TypeLingo needs real-time keystroke streaming. Understand the options.

**Study:**
- MDN WebSocket API guide: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
- FastAPI WebSocket tutorial: https://fastapi.tiangolo.com/advanced/websockets/
- "WebSocket vs. Server-Sent Events vs. Long Polling" — research all three
- Read about the WebSocket protocol (RFC 6455) at a high level — understand the upgrade handshake

**Reflection Questions:**
- What is the overhead of a WebSocket connection vs. repeated HTTP requests?
- How do you handle authentication on a WebSocket connection?
- What happens when a WebSocket connection drops mid-session? How do you handle reconnection?
- Should you send every individual keystroke over the WebSocket, or batch them? What are the trade-offs?
- How would you handle backpressure if the client sends keystrokes faster than the server can process?

**Mini-project:**
- Build a simple chat app with FastAPI WebSockets. Two browser tabs, real-time messages.
- Add connection drop detection and automatic reconnection on the client side.

---

## Phase 2: Databases & Data Modeling

### 2.1 — Relational Databases Deep Dive

PostgreSQL will be your primary datastore. Understand it deeply.

**Study:**
- "Designing Data-Intensive Applications" by Martin Kleppmann — Chapter 2 (Data Models and Query Languages), Chapter 3 (Storage and Retrieval), Chapter 7 (Transactions)
- "The Art of PostgreSQL" by Dimitri Fontaine — deep PostgreSQL-specific knowledge
- PostgreSQL official docs: JSONB, Indexes (B-tree, GIN, GiST), EXPLAIN ANALYZE
- "Use the Index, Luke" (free online book on SQL indexing): https://use-the-index-luke.com/
- SQLAlchemy 2.0 tutorial (understand the ORM and Core difference): https://docs.sqlalchemy.org/en/20/tutorial/

**Reflection Questions:**
- What is ACID? Explain each letter with a concrete example from TypeLingo.
- What's the difference between a B-tree index and a GIN index? When would you use each for TypeLingo?
- When should you use JSONB vs. a separate relational table? What can't you do efficiently with JSONB?
- What is a database transaction isolation level? What's the default in PostgreSQL? When would you change it?
- How does `EXPLAIN ANALYZE` work? What are you looking for in the output?
- What is connection pooling and why do you need it? What happens without it under load?
- For TypeLingo: should per-key typing stats be a JSONB column or a separate `key_stats` table? What are the trade-offs of each?

**Mini-project:**
- Create a PostgreSQL database with a `users` table and a JSONB column. Insert 100k rows. Write queries against the JSONB data with and without a GIN index. Compare `EXPLAIN ANALYZE` output.
- Deliberately create a slow query (missing index, full table scan). Use `EXPLAIN ANALYZE` to diagnose it, add the right index, and measure the improvement.
- Implement optimistic locking for concurrent updates to a user's skill profile. Test it by simulating two concurrent updates.

---

### 2.2 — Caching

You'll use Redis as a cache layer. Understand caching patterns and pitfalls.

**Study:**
- "Designing Data-Intensive Applications" — Chapter 5 (Replication, relevant to cache consistency)
- Redis University (free courses): https://university.redis.io/
- "Caching Strategies and How to Choose the Right One" — research cache-aside, write-through, write-behind, read-through
- "A Hitchhiker's Guide to Caching Patterns" by Alexy Yunoshev (article)
- Understand the "thundering herd" problem and solutions (locking, probabilistic early expiration)

**Reflection Questions:**
- What is cache-aside vs. write-through vs. write-behind? Which fits TypeLingo's passage cache?
- What is the "thundering herd" problem? How could it happen in TypeLingo when a popular passage expires?
- How do you decide on cache TTL? What happens if it's too short? Too long?
- What data in TypeLingo should be cached? What should never be cached?
- What is cache invalidation and why is it called one of the "two hard problems in CS"?
- If Redis goes down, what happens to your application? How do you design for this?

**Mini-project:**
- Set up Redis locally. Implement cache-aside pattern for a simple key-value lookup in Python.
- Simulate a thundering herd: write a script that fires 100 concurrent requests for the same cache key after expiration. Observe the behavior. Then implement a locking solution and compare.

---

### 2.3 — Database Schema Design & Migrations

**Study:**
- Alembic documentation: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- "Evolutionary Database Design" by Martin Fowler (article): https://martinfowler.com/articles/evodb.html
- Study how to write backwards-compatible migrations (expand-contract pattern)

**Reflection Questions:**
- Why should you never edit a migration file that's already been applied?
- What is the "expand and contract" pattern for schema changes? Why is it important for zero-downtime deployments?
- How do you handle data migrations (not just schema changes)?
- What's your rollback strategy if a migration fails halfway?

**Mini-project:**
- Create a project with Alembic. Write 5 migrations that evolve a schema: create table → add column → add index → rename column (expand-contract) → add JSONB column. Practice `upgrade` and `downgrade`.

---

## Phase 3: Distributed Systems Patterns

### 3.1 — Core Distributed Systems Concepts

**Study:**
- "Designing Data-Intensive Applications" by Martin Kleppmann — this is the bible. Read:
  - Chapter 5: Replication
  - Chapter 6: Partitioning
  - Chapter 7: Transactions
  - Chapter 8: The Trouble with Distributed Systems
  - Chapter 9: Consistency and Consensus
- MIT 6.824 Distributed Systems lectures (free): https://pdos.csail.mit.edu/6.824/
  - At minimum, watch lectures 1-6 and do Lab 1 (MapReduce) and Lab 2 (Raft)
- "The Fallacies of Distributed Computing" — know all 8 and what they mean in practice

**Reflection Questions:**
- What are the 8 fallacies of distributed computing? Give a concrete example of each.
- What is the CAP theorem? What does TypeLingo need — CP or AP? Why?
- What is the difference between consistency models: strong, eventual, causal? Which parts of TypeLingo need which?
- What is a split-brain scenario and how do you prevent it?
- What does "exactly-once delivery" mean and why is it basically impossible? What do you actually get?

**Mini-project:**
- Do MIT 6.824 Lab 1 (MapReduce implementation). It's hard. It's worth it.
- If you're ambitious: do Lab 2 (Raft). Implementing a consensus algorithm will permanently change how you think about distributed systems.

---

### 3.2 — Message Queues & Async Processing

TypeLingo uses background workers for LLM generation. Understand queuing deeply.

**Study:**
- "Designing Data-Intensive Applications" — Chapter 11 (Stream Processing)
- Celery documentation: https://docs.celeryq.dev/
- "RabbitMQ vs. Redis vs. Kafka" — research when to use each
- Understand: at-least-once vs. at-most-once delivery, dead letter queues, retry strategies, idempotent consumers

**Reflection Questions:**
- Why use a task queue instead of just calling the LLM in the request handler?
- What happens if a Celery worker crashes mid-task? How is the task recovered?
- What is a dead letter queue and when would you use one?
- What is backpressure and how does a queue help manage it?
- What is the difference between a task queue (Celery) and a message broker (Kafka)? When would you use each?
- For TypeLingo: what happens if the same passage generation task is accidentally enqueued twice? How do you make it idempotent?

**Mini-project:**
- Set up Celery with Redis as a broker. Create a task that simulates an LLM call (just sleep for 3 seconds). Enqueue 20 tasks and watch workers process them.
- Implement retry with exponential backoff for a task that randomly fails 50% of the time.
- Implement a dead letter queue: after 3 retries, move the failed task somewhere for manual inspection.

---

### 3.3 — Resilience Patterns

Your app depends on external services (LLM API, database, cache). They will fail.

**Study:**
- "Release It!" by Michael Nygard — Chapters on stability patterns. This is the canonical book on building resilient systems. Covers circuit breaker, bulkhead, timeout, retry, and more.
- "Microsoft Azure Architecture: Resilience Patterns" (free, excellent): https://learn.microsoft.com/en-us/azure/architecture/patterns/category/resiliency
- Netflix's Hystrix (now deprecated but the docs explain the patterns beautifully): https://github.com/Netflix/Hystrix/wiki

**Reflection Questions:**
- What is a circuit breaker? Draw the state machine (CLOSED → OPEN → HALF-OPEN). What triggers each transition?
- What is the bulkhead pattern? How does it prevent one failing dependency from taking down everything?
- What is the difference between a timeout and a deadline? Which should you use for LLM API calls?
- What is graceful degradation? For TypeLingo, what's the user experience when the LLM API is down?
- What is the retry amplification problem? How do you prevent retries from making an outage worse?
- Design TypeLingo's complete fallback chain: what happens when the LLM is down, when Redis is down, when PostgreSQL is down?

**Mini-project:**
- Implement a circuit breaker from scratch in Python. No libraries. Include all three states, configurable thresholds, and half-open testing.
- Write a test that simulates an external service failing: verify the circuit opens after N failures, requests fail fast while open, and the circuit recovers after the timeout.

---

## Phase 4: Testing & TDD

### 4.1 — Test-Driven Development

**Study:**
- "Test-Driven Development: By Example" by Kent Beck — the original TDD book. Short, practical, transformative.
- "Architecture Patterns with Python" — Chapters on testing (they show TDD with the repository pattern)
- pytest documentation: fixtures, parametrize, markers, conftest, factories
- "The Practical Test Pyramid" by Ham Vocke (article): https://martinfowler.com/articles/practical-test-pyramid.html

**Reflection Questions:**
- What is the Red-Green-Refactor cycle? Why is the order important?
- What's the difference between a unit test and an integration test? Where do you draw the line?
- What should you mock and what should you not mock? What is "over-mocking"?
- Why does hexagonal architecture make TDD easier?
- What is test coverage? Is 100% coverage a good goal? Why or why not?
- What is a test fixture? What is a test factory? When would you use each?
- For TypeLingo: which parts of the system are most critical to test? Which are hardest to test? How would you approach the hard ones?

**Mini-project:**
- Pick a small feature (e.g., WPM calculation). Write the tests first, then implement. Commit at each step: failing test → passing code → refactor. Look at your git history and see the rhythm.
- Write a test that requires a database. Then refactor using the repository pattern so the test uses an in-memory store instead. Feel the difference in speed and reliability.

---

### 4.2 — Integration & E2E Testing

**Study:**
- pytest-asyncio docs: testing async FastAPI endpoints
- FastAPI testing guide: https://fastapi.tiangolo.com/tutorial/testing/
- "Testing Microservices" by Toby Clemson (article): https://martinfowler.com/articles/microservice-testing/
- Testcontainers (spin up real Postgres/Redis in tests): https://testcontainers-python.readthedocs.io/

**Reflection Questions:**
- When should you test against a real database vs. a mock?
- How do you manage test data? What's the difference between fixtures, factories, and seed data?
- How do you test WebSocket endpoints?
- How do you test the LLM integration without actually calling the API every test run?
- What is a contract test? When would you use one?

**Mini-project:**
- Write an integration test that starts a real PostgreSQL (via Testcontainers or Docker), runs a migration, inserts data, queries it, and verifies the result. Feel the difference from a unit test.
- Write a test for a FastAPI WebSocket endpoint that sends messages and verifies responses.

---

## Phase 5: SRE & Observability

### 5.1 — Observability: Logs, Metrics, Traces

**Study:**
- "The Google SRE Book" (free online): https://sre.google/sre-book/table-of-contents/ — Read chapters: 1-6 (principles), 10-11 (alerting), 29 (dealing with interrupts)
- "The Google SRE Workbook" (free online): https://sre.google/workbook/table-of-contents/ — more practical
- "Observability Engineering" by Charity Majors, Liz Fong-Jones, George Miranda — the modern take on observability
- structlog documentation (Python structured logging): https://www.structlog.org/
- Prometheus documentation (metrics): https://prometheus.io/docs/
- OpenTelemetry documentation (tracing): https://opentelemetry.io/docs/
- "The RED Method" by Tom Wilkie (article) — Rate, Errors, Duration for request-driven systems
- "The USE Method" by Brendan Gregg — Utilization, Saturation, Errors for resource-driven systems

**Reflection Questions:**
- What's the difference between monitoring and observability?
- What are the three pillars of observability? Why do you need all three?
- What is structured logging and why is it better than plain text logs?
- What is a request ID / trace ID? How does it help you debug a problem across multiple components?
- What are the RED method and USE method? Which parts of TypeLingo would you apply each to?
- What makes a good metric vs. a useless metric?
- What's the difference between a counter, gauge, histogram, and summary in Prometheus?

**Mini-project:**
- Add structlog to a FastAPI app. Make every log line include a request ID. Simulate a request flowing through 3 functions and grep the logs by request ID.
- Add 5 Prometheus metrics to a FastAPI app: request count, request duration histogram, active connections gauge, error count, and a custom business metric. View them at `/metrics`.
- Set up Grafana locally (Docker). Connect it to Prometheus. Build a dashboard with 4 panels.

---

### 5.2 — SLOs, Error Budgets, and Incident Response

**Study:**
- "The Google SRE Book" — Chapter 4 (SLOs), Chapter 28 (Accelerating SREs)
- "Implementing Service Level Objectives" by Alex Hidalgo — goes deep on SLO practice
- "The Checklist Manifesto" by Atul Gawande — not about software, but deeply relevant to runbooks and incident response
- PagerDuty's incident response guide (free, excellent): https://response.pagerduty.com/

**Reflection Questions:**
- What's the difference between an SLI, SLO, and SLA?
- What is an error budget? How does it help you make deployment decisions?
- For TypeLingo: what are your 3 most important SLOs? How would you measure them?
- What does a good post-mortem look like? What's the difference between "blameless" and "blameful" post-mortems?
- What is a runbook? When should you write one?

**Mini-project:**
- Define 3 SLOs for TypeLingo. For each, specify: the SLI (what you measure), the target (e.g., 99.9%), and how you'd calculate it from your Prometheus metrics.
- Write a runbook for "LLM API is returning 500 errors." Include: detection, diagnosis steps, mitigation, escalation, and post-recovery verification.

---

### 5.3 — Load Testing & Performance

**Study:**
- Locust documentation: https://locust.io/ (Python-based, great for learning)
- k6 documentation: https://k6.io/docs/ (JavaScript-based, more production-grade)
- Brendan Gregg's "Systems Performance" — Chapter 2 (Methodology) for how to think about performance
- "How to read a flame graph" by Brendan Gregg (article + video)
- Learn about: p50, p95, p99 latency; throughput vs. latency; Amdahl's law; Little's law

**Reflection Questions:**
- Why is p99 latency more important than average latency?
- What is Amdahl's law and what does it tell you about the limits of optimization?
- What is Little's law (L = λW) and how does it help you capacity plan?
- How do you identify whether a bottleneck is CPU-bound, I/O-bound, or memory-bound?
- What is a flame graph and how do you read one?

**Mini-project:**
- Write a Locust load test for a FastAPI app. Ramp from 1 to 100 concurrent users. Find the breaking point. Graph the latency curve.
- Profile a Python function with `cProfile` and `py-spy`. Generate a flame graph. Identify the hotspot and optimize it. Measure the improvement.

---

## Phase 6: LLM Integration & Prompt Engineering

### 6.1 — Working with LLM APIs

**Study:**
- Anthropic Claude API documentation: https://docs.anthropic.com/
- "Prompt Engineering Guide": https://www.promptingguide.ai/
- Understand: tokens, temperature, top_p, max_tokens, system prompts vs. user prompts
- Understand: rate limiting, retry strategies, cost estimation, streaming responses

**Reflection Questions:**
- How do you estimate the cost of generating one passage? How does that scale with users?
- What is prompt injection and how do you defend against it?
- How do you validate that the LLM output matches your constraints? What do you do when it doesn't?
- What is the trade-off between temperature=0 (deterministic) and temperature=1 (creative) for passage generation?
- How would you A/B test two different prompts to see which generates better passages?
- For TypeLingo: how many unique passages do you actually need? Is generating on-the-fly worth the cost vs. pre-generating a large corpus?

**Mini-project:**
- Write 5 different prompts for passage generation. Test each 10 times. Evaluate the outputs against your constraints (word count, grammar targets, key focus). Which prompt is most reliable?
- Implement structured output: make the LLM return JSON with the passage + metadata. Parse and validate it.
- Measure latency and cost for 50 generations. Calculate your per-user cost estimate.

---

## Phase 7: Frontend (When You're Ready)

### 7.1 — React / Next.js Fundamentals

**Study:**
- React official docs (the new ones are excellent): https://react.dev/
- Next.js Learn course: https://nextjs.org/learn
- "Thinking in React" (official guide): https://react.dev/learn/thinking-in-react
- TypeScript handbook: https://www.typescriptlang.org/docs/handbook/

**Reflection Questions:**
- What is the virtual DOM and why does React use it?
- What is server-side rendering (SSR) vs. static site generation (SSG)? Which pages in TypeLingo need which?
- How do you capture individual keystrokes in JavaScript? What events do you listen for?
- How do you measure precise timing between keystrokes? Is `Date.now()` accurate enough? What about `performance.now()`?
- How do you handle WebSocket connections in React? What happens on component unmount?

**Mini-project:**
- Build a minimal typing test UI: display a passage, capture keystrokes, highlight correct/incorrect characters in real-time, calculate WPM at the end. No backend yet — just the frontend.
- Add a per-key heatmap visualization using the keystroke data you collected.

---

## Phase 8: Security

### 8.1 — Authentication & Application Security

**Study:**
- "OWASP Top 10" (memorize it): https://owasp.org/www-project-top-ten/
- "OAuth 2.0 Simplified" by Aaron Parecki: https://www.oauth.com/
- JWT.io — understand the structure of a JWT (header, payload, signature)
- "The Copenhagen Book" (modern auth guide): https://thecopenhagenbook.com/

**Reflection Questions:**
- What is the difference between authentication and authorization?
- How does bcrypt work? Why is a "cost factor" important?
- What is a JWT? What's in it? Should you store sensitive data in the payload?
- What is the difference between storing a JWT in localStorage vs. an httponly cookie? Which is more secure? Why?
- What is CSRF? How does the SameSite cookie attribute help?
- What is SQL injection? How does an ORM prevent it? Can it still happen?
- What is XSS? What's the difference between stored and reflected XSS?

**Mini-project:**
- Implement registration + login in FastAPI with bcrypt + JWT. Include access token (15 min) and refresh token (7 days). Store refresh token in httponly cookie.
- Deliberately write a SQL injection vulnerability, exploit it, then fix it.
- Set up CORS in FastAPI. Test what happens when a different origin tries to access your API.

---

## Ongoing: Engineering Journal

Keep a decision log as you build. Every significant choice gets an entry:

```
## Decision: [Title]
**Date:** YYYY-MM-DD
**Status:** Decided / Revisiting / Superseded

### Context
What is the situation? What problem are we solving?

### Options Considered
1. Option A — pros, cons
2. Option B — pros, cons
3. Option C — pros, cons

### Decision
What did we choose?

### Rationale
Why? What trade-offs are we accepting?

### Consequences
What follows from this decision? What becomes easier? Harder?
```

This journal is one of the most valuable artifacts you'll produce. It forces clear thinking and creates a record of your reasoning that you can revisit and learn from.

---

## Reading Order (Priority-Ranked)

If you only read 5 things, read these:

1. **"Architecture Patterns with Python"** — directly applicable to your project structure, testing, and patterns
2. **"Designing Data-Intensive Applications"** — the distributed systems bible; foundational for everything
3. **"The Google SRE Book"** (free) — production mindset, SLOs, incident response
4. **"Release It!"** — resilience patterns you'll implement (circuit breaker, bulkhead, etc.)
5. **"Test-Driven Development: By Example"** — transforms how you write code

After those, in order:
6. "Fundamentals of Software Architecture"
7. "Fluent Python"
8. "Observability Engineering"
9. MIT 6.824 lectures (distributed systems)
10. "The Art of PostgreSQL"

---

## The Mindset

You're not just building a typing app. You're using a typing app as a vehicle to become the kind of engineer who can build *anything*. Every decision you make — even the "wrong" ones — teaches you something a tutorial never could.

When you get stuck, resist the urge to ask "what should I do?" Instead ask "what are my options and what are the trade-offs of each?" That question is the entire job of a senior engineer.

Build it. Break it. Fix it. Understand why it broke. That's the loop. Now go.
