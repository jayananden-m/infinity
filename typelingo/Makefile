.PHONY: install install-hooks lint format typecheck security test test-unit test-integration test-e2e seed run dev up down

install:
	pip install -e ".[dev]"

install-hooks:
	pre-commit install --hook-type pre-commit
	pre-commit install --hook-type commit-msg

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/ --strict

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v --cov=src --cov-fail-under=90

security:
	pip-audit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

seed:
	python scripts/seed_passages.py

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev:
	docker compose up -d postgres redis

up:
	docker compose up -d

down:
	docker compose down
