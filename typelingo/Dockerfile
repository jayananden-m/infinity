FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e ".[dev]"

COPY src/ src/
COPY tests/ tests/
COPY alembic/ alembic/
COPY alembic.ini .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
