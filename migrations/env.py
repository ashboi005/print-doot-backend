import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import context
from config import DATABASE_URL  # Import database URL from config
from models import Base  # Import models

# Load Alembic configuration and logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata so Alembic knows about our models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode with an async engine."""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.begin() as conn:
        await conn.run_sync(lambda sync_conn: context.configure(
            connection=sync_conn,
            target_metadata=target_metadata
        ))

        await conn.run_sync(lambda sync_conn: context.run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
