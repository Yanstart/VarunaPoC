"""
Database Configuration - Async SQLAlchemy + PostgreSQL/PostGIS

Provides async database engine, session factory, and base model
for the VarunaPoC annotation system.

Uses:
    - asyncpg as async PostgreSQL driver
    - GeoAlchemy2 for PostGIS spatial types
    - Alembic for schema migrations

Configuration via DATABASE_URL environment variable:
    postgresql+asyncpg://varuna:varuna_dev@localhost:5432/varuna  # pragma: allowlist secret
"""

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://varuna:varuna_dev@localhost:5433/varuna",  # pragma: allowlist secret
)

_engine_kwargs = {
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
}

if "sqlite" in DATABASE_URL:
    from sqlalchemy.pool import StaticPool

    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["poolclass"] = StaticPool
else:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context():
    """Context manager variant for use outside FastAPI routes."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create engine connection pool (call on startup)."""
    # Verify connectivity
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)


async def close_db():
    """Dispose engine connection pool (call on shutdown)."""
    await engine.dispose()
