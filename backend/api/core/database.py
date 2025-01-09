"""Database connection and session management"""

import logging
from typing import AsyncGenerator
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Import all models
from .models import (
    User, LLMProvider, Topic, Blueprint, TerminalObjective,
    EnablingObjective, FlowExecution, IdempotencyKey, FlowLog,
    FlowExecutionStatus, CognitiveLevelEnum, LogLevel
)

# Import Base from base.py
from .base import Base

def get_database_url(test_mode=False):
    """Get database URL from environment variables"""
    DB_USER = os.getenv("POSTGRES_USER", "test_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "test_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = "quizmaster_test" if test_mode else "quizmaster"
    
    return f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine based on test mode
DATABASE_URL = get_database_url(test_mode=os.getenv("TEST_MODE") == "true")
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Configure logging
logger = logging.getLogger(__name__)

# Dependency to get DB sessions
async def get_db():
    async with async_session() as session:
        yield session

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for async operations"""
    async for session in get_db():
        yield session

async def init_db():
    """Initialize the database and create tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Export functions and classes
__all__ = ["get_async_session", "get_db", "init_db", "Base"]
