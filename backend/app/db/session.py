import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Async engine for FastAPI route handlers
# Handle sqlite vs postgresql async drivers gracefully
async_db_url = settings.database_url
if async_db_url.startswith("postgresql://"):
    async_db_url = async_db_url.replace("postgresql://", "postgresql+asyncpg://")
elif async_db_url.startswith("sqlite://") and not async_db_url.startswith("sqlite+aiosqlite://"):
    async_db_url = async_db_url.replace("sqlite://", "sqlite+aiosqlite://")

# Pass appropriate engine arguments based on driver
engine_args = {"echo": False}
if "sqlite" not in async_db_url:
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
    })

async_engine = create_async_engine(async_db_url, **engine_args)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic and CLI scripts
sync_db_url = settings.sync_database_url
if sync_db_url.startswith("postgresql+asyncpg://"):
    sync_db_url = sync_db_url.replace("postgresql+asyncpg://", "postgresql://")

sync_engine_args = {"echo": False}
if "sqlite" not in sync_db_url:
    sync_engine_args.update({
        "pool_pre_ping": True,
    })

sync_engine = create_engine(sync_db_url, **sync_engine_args)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
