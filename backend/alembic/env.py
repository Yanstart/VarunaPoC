"""
Alembic Environment Configuration

Supports async SQLAlchemy engine for PostgreSQL+asyncpg.
Imports all models so autogenerate can detect schema changes.
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load .env for DATABASE_URL

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add backend to path for model imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models so they register with Base.metadata
import models  # noqa: F401
from core.database import DATABASE_URL, Base

config = context.config

# Override sqlalchemy.url from environment if set
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode (generates SQL without DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
