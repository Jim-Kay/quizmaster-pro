"""Database connection and session management"""

import logging
from typing import AsyncGenerator, Dict
import os
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
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
from .config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from settings"""
    settings = get_settings()
    return f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"

# Cache engines per database URL
_engines: Dict[str, AsyncEngine] = {}
_sessions: Dict[str, sessionmaker] = {}

def get_engine() -> AsyncEngine:
    """Get or create database engine for current settings"""
    database_url = get_database_url()
    if database_url not in _engines:
        _engines[database_url] = create_async_engine(database_url, echo=True)
    return _engines[database_url]

def get_session_maker() -> sessionmaker:
    """Get or create session maker for current settings"""
    database_url = get_database_url()
    if database_url not in _sessions:
        engine = get_engine()
        _sessions[database_url] = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _sessions[database_url]

# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# For testing and internal use where we need a session directly
def get_session() -> AsyncSession:
    """Get a new database session"""
    session_maker = get_session_maker()
    return session_maker()

async def init_db():
    """Initialize the database and create tables"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Export functions and classes
__all__ = ["get_db", "init_db", "get_session", "Base"]
