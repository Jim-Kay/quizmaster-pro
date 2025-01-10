"""
Test Database Initialization
Ensures the test database is properly initialized with required mock data.

IMPORTANT: This module manages the persistent mock test user that is used across all tests.
The mock user (MOCK_USER_ID) should NEVER be deleted as other tests depend on its existence
for authentication and authorization testing.

Test Metadata:
    Level: 0
    Dependencies: []
    Blocking: True
    Parallel_Safe: False
    Estimated_Duration: 5
    Working_Directory: backend
    Required_Paths:
        - api/core/database.py
        - api/models.py

Environment:
    - Conda Environment: crewai-quizmaster-pro
    - Required Services:
        - PostgreSQL database

Setup:
    1. Ensure PostgreSQL is running
    2. Set required environment variables:
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_DB
        - POSTGRES_HOST
        - POSTGRES_PORT

Execution:
    Run with test runner:
    python tests/test_runner.py

Expected Results:
    - Test database should be initialized with mock user
    - Mock user should have specific UUID and email for consistent testing

Mock User vs Test User:
    This codebase uses two types of test users:
    1. Mock User (defined here):
       - Has fixed UUID: f9b5645d-898b-4d58-b10a-a6b50a9d234b
       - Should NEVER be deleted
       - Used by other tests for authentication
       - Provides consistent test environment
    
    2. Test User (defined in test_auth.py):
       - Has different UUID: a1b2c3d4-e5f6-4321-8765-9abcdef01234
       - Can be safely created/deleted
       - Used for testing CRUD operations
       - Temporary, cleaned up after tests
"""

import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, text
import logging
import sys
import traceback
from typing import AsyncGenerator
from uuid import UUID

from api.core.models import Base, User, LLMProvider

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a console handler if not already present
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Mock user constants - these should be used across all tests
# WARNING: This mock user should NEVER be deleted as other tests depend on it
MOCK_USER_ID = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
MOCK_USER_EMAIL = 'test_mock_user@quizmasterpro.test'
MOCK_USER_NAME = 'Mock Test User'

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    DB_USER = os.getenv("POSTGRES_USER", "test_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "test_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = "quizmaster_test"
    
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest.fixture(scope="session")
async def init_db(test_engine):
    """Initialize database schema"""
    engine = await anext(test_engine)
    async with engine.begin() as conn:
        # Drop all tables except users
        await conn.execute(text("DROP TABLE IF EXISTS flow_logs CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS idempotency_keys CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS flow_executions CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS enabling_objectives CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS terminal_objectives CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS blueprints CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS topics CASCADE"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine

@pytest.fixture(scope="function")
async def test_session(init_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh session for each test."""
    logger.debug("Creating test session")
    
    engine = await anext(init_db)
    session = AsyncSession(engine)
    logger.debug("Created AsyncSession object")
    
    await session.begin()
    logger.debug("Session transaction begun")
    
    try:
        logger.debug("Yielding session to test")
        yield session
        logger.debug("Test completed, cleaning up session")
    except Exception as e:
        logger.error(f"Error in test_session fixture: {str(e)}")
        raise
    finally:
        try:
            logger.debug("Rolling back session")
            await session.rollback()
            logger.debug("Closing session")
            await session.close()
            logger.debug("Session cleanup completed")
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")

@pytest.mark.asyncio
async def test_ensure_mock_user_exists(test_session):
    """Test creating/finding mock user"""
    logger.debug("Starting test_ensure_mock_user_exists")
    try:
        session = await anext(test_session)
        
        logger.debug("Creating query to find mock user")
        query = select(User).where(User.user_id == MOCK_USER_ID)
        logger.debug(f"Executing query: {query}")
    
        logger.debug("About to execute query")
        result = await session.execute(query)
        logger.debug("Query executed")
        
        user = result.scalar_one_or_none()
        logger.debug(f"Query result: {user}")
        
        if user is None:
            logger.debug("Mock user not found, creating new one")
            user = User(
                user_id=MOCK_USER_ID,
                email=MOCK_USER_EMAIL,
                name=MOCK_USER_NAME,
                llm_provider=LLMProvider.OPENAI
            )
            session.add(user)
            await session.commit()
            logger.debug("Created new mock user")
        else:
            logger.debug("Mock user already exists")
        
        assert user is not None
        assert user.user_id == MOCK_USER_ID
        assert user.email == MOCK_USER_EMAIL
        assert user.name == MOCK_USER_NAME
        logger.debug("Mock user assertions passed")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise
    finally:
        logger.debug("Test cleanup completed")
