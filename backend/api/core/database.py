"""Database connection and session management"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from .config import get_settings
from .base import Base

# Get settings
settings = get_settings()

# Construct database URLs
DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
SYNC_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Create engines
engine = create_async_engine(DATABASE_URL, echo=True)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)

# Create session factories
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Configure logging
logger = logging.getLogger(__name__)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for async operations"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (alias for get_async_session for compatibility)"""
    async for session in get_async_session():
        yield session

async def init_db():
    """Initialize the database and create tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Export functions and classes
__all__ = ["get_async_session", "get_db", "init_db", "Base"]
