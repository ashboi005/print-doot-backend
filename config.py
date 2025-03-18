from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models import Base

load_dotenv()

# Load the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Synchronous engine for Alembic migrations (convert asyncpg to psycopg2)
sync_engine = create_engine(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))

# Asynchronous engine for application use (keep asyncpg for async usage)
async_engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)

# Async session maker for application usage
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Function to get DB session for application (async)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Function to initialize the database (sync version for Alembic)
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Synchronous engine setup for Alembic migrations
def get_sync_engine():
    return sync_engine
