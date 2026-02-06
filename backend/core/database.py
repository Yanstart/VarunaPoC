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

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_size=5,
    max_overflow=10,
)

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
