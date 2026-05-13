"""Shared fixtures for integration tests.

Requires live Postgres (DATABASE_URL) and Redis (REDIS_URL) — provided by CI
services or a local `docker-compose up -d postgres redis`.
Run: pytest tests/integration/ -v -m integration
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config
from src.config import settings


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    """Run alembic upgrade head once per test session."""
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


@pytest.fixture()
async def db_session() -> AsyncSession:
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session, session.begin():
        yield session
        await session.rollback()
    await engine.dispose()
