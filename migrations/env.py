import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from config import DATABASE_URL  

from models import Base as RootBase
from routers.products.models import Base as ProductsBase
from routers.orders.models import Base as OrdersBase

# Load Alembic configuration and logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata to the root metadata
target_metadata = RootBase.metadata

# Manually merge tables from ProductsBase into target_metadata
for table_name, table in ProductsBase.metadata.tables.items():
    if table_name not in target_metadata.tables:
        target_metadata._add_table(table_name, table.schema, table)

for table_name, table in OrdersBase.metadata.tables.items():
    if table_name not in target_metadata.tables:
        target_metadata._add_table(table_name, table.schema, table)

def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
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
