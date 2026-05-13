# CI/CD Pipeline

```mermaid
graph LR
    push[Push / PR]

    push --> quality[quality\nruff lint\nruff format\nmypy strict]
    push --> unit[test-unit\npytest tests/unit\n90% coverage gate]
    push --> security[security\npip-audit]
    push --> frontend[frontend\ntsc --noEmit\neslint\nvitest run]

    quality --> integration[test-integration\nreal PostgreSQL 16\nreal Redis 7]
    unit --> integration
    security --> integration
    frontend --> integration

    integration --> e2e[test-e2e\nfull HTTP flow\nPostgreSQL 16]

    style quality fill:#1d3557,color:#fff
    style unit fill:#1d3557,color:#fff
    style security fill:#1d3557,color:#fff
    style frontend fill:#1d3557,color:#fff
    style integration fill:#2d6a4f,color:#fff
    style e2e fill:#2d6a4f,color:#fff
```

## Pre-commit hooks (local, before push)

```mermaid
graph LR
    commit[git commit] --> ruff[ruff lint + format\nauto-fix]
    ruff --> mypy[mypy strict]
    mypy --> fe_tsc[frontend tsc --noEmit]
    fe_tsc --> fe_lint[frontend eslint]
    fe_lint --> cz[commitizen\nmessage format check]
    cz -->|all pass| done[commit created]
    cz -->|any fail| blocked[commit blocked]
```

## Conventional commit format

```
<type>(<scope>): <description>

Types: feat · fix · refactor · test · docs · chore · perf
```

Examples:
- `feat(domain): add TypingSession state machine`
- `fix(scoring): exclude backspaced chars from WPM`
- `test(adaptation): add balanced advance scenario`
- `chore(ci): add frontend quality gate`

## Job rationale

| Job | Runs | Why |
|---|---|---|
| quality | Always | Cheap — fail fast on lint before spending on tests |
| test-unit | Always | No infra needed — runs in <3s |
| security | Always | Independent of code correctness |
| frontend | Always | TypeScript type check + ESLint + Vitest component tests |
| test-integration | After all four pass | Spins up Postgres + Redis — expensive |
| test-e2e | After integration | Full HTTP user flow — requires clean DB state |
