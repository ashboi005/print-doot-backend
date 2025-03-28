import os
import boto3
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# AWS Region (Automatically set in Lambda)
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")  # Default to ap-south-1 if not set

# AWS SSM Client (Fetching secrets from AWS)
ssm = boto3.client("ssm", region_name=AWS_REGION)

# Function to get a secure parameter from AWS SSM
def get_ssm_secure_parameter(name):
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]

# Load sensitive parameters from AWS SSM
DATABASE_URL = get_ssm_secure_parameter("/printdoot/DATABASE_URL")

# Fix asyncpg issue in SQLAlchemy for Alembic migrations (convert asyncpg to psycopg2)
sync_engine = create_engine(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))

# Asynchronous engine for FastAPI app usage
async_engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)

# Async session maker for FastAPI application
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Function to get an async DB session for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Function to initialize the database (for startup scripts)
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Function to get synchronous engine for Alembic migrations
def get_sync_engine():
    return sync_engine
