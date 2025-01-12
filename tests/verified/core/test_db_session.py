"""
Test database session handling in async context.

This module tests the async database session management using SQLAlchemy and PostgreSQL.
Tests are designed to run in isolation using function-scoped fixtures and nested transactions.

Key components:
1. Database Configuration:
   - Uses a dedicated test database (quizmaster_test) to avoid conflicts with production
   - Requires appropriate permissions for the test user in the test database
   - Test user must have privileges to create tables, types, and perform DML operations

2. Fixtures:
   - schema_engine: Session-scoped engine for database schema management
   - create_tables: Creates all required tables before tests run
   - engine: Function-scoped engine for isolated test execution
   - session: Function-scoped session with nested transaction support

3. Transaction Management:
   - Each test runs in its own nested transaction
   - Changes are rolled back after each test
   - Warning about deassociated nested transactions is expected

Note: Previous issues with insufficient privileges were resolved by:
1. Using a dedicated test database instead of the default postgres database
2. Ensuring the test user has proper permissions in the test database
3. Separating schema management (session-scoped) from test execution (function-scoped)
"""

import pytest
import pytest_asyncio
import logging
import asyncio
import os
from uuid import UUID
from typing import AsyncGenerator, Any
from datetime import datetime
from functools import wraps

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    AsyncConnection,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker
)

from api.core.models import User, Base
from api.core.config import get_settings
import asyncpg

# Configure pytest-asyncio
pytestmark = [
    pytest.mark.asyncio(scope="function"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning")
]

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Add file handler with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f'tests/logs/test_db_session_{timestamp}.log'
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Get settings
settings = get_settings()

# Override host for local testing if not in Docker
if not os.path.exists('/.dockerenv'):
    settings.postgres_host = 'localhost'

# Database configuration
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/quizmaster_test"

@pytest_asyncio.fixture(scope="session")
async def schema_engine():
    """Create a session-scoped engine for schema management"""
    logger.debug("Creating schema engine...")
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        future=True,
        isolation_level="REPEATABLE READ"
    )
    yield engine
    logger.debug("Disposing schema engine...")
    await engine.dispose()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables(schema_engine):
    """Create all database tables before running tests"""
    logger.info("Creating database tables...")
    async with schema_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created!")

@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create async engine instance for each test function."""
    logger.debug("Creating async engine...")
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        future=True,
        isolation_level="REPEATABLE READ"
    )
    yield engine
    logger.debug("Disposing async engine...")
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped session with nested transaction rollback."""
    logger.debug("Creating database session...")
    async with engine.connect() as conn:
        # Begin transaction
        trans = await conn.begin()
        logger.debug("Started outer transaction")
        
        # Begin nested transaction (savepoint)
        nested = await conn.begin_nested()
        logger.debug("Created savepoint")

        # Create async session using the same connection
        session_maker = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            class_=AsyncSession
        )
        async with session_maker() as session:
            try:
                yield session
            finally:
                logger.debug("Rolling back to savepoint...")
                await nested.rollback()
                logger.debug("Rolling back outer transaction...")
                await trans.rollback()
                logger.debug("Closing session...")
                await session.close()

async def test_create_user(session: AsyncSession):
    """Test creating a user with async session"""
    logger.info("Testing user creation...")
    
    # Create test user
    logger.debug("Creating test user...")
    user = User(
        email="test_session_user@quizmasterpro.test",
        name="Test Session User"
    )
    session.add(user)
    await session.flush()  # Flush changes to get the ID
    logger.debug(f"Created user with ID: {user.user_id}")
    
    # Query user
    logger.debug("Querying user...")
    result = await session.execute(
        select(User).where(User.email == "test_session_user@quizmasterpro.test")
    )
    queried_user = result.scalar_one_or_none()
    
    # Verify user
    assert queried_user is not None
    assert queried_user.email == "test_session_user@quizmasterpro.test"
    assert queried_user.name == "Test Session User"
    logger.info("User creation test passed!")

async def test_multiple_operations(session: AsyncSession):
    """Test multiple database operations in sequence"""
    logger.info("Testing multiple operations...")
    
    # Create first user
    logger.debug("Creating first user...")
    user1 = User(
        email="test_multi_user1@quizmasterpro.test",
        name="Test Multi User 1"
    )
    session.add(user1)
    await session.flush()  # Flush changes to get the ID
    logger.debug(f"Created first user with ID: {user1.user_id}")
    
    # Create second user
    logger.debug("Creating second user...")
    user2 = User(
        email="test_multi_user2@quizmasterpro.test",
        name="Test Multi User 2"
    )
    session.add(user2)
    await session.flush()  # Flush changes to get the ID
    logger.debug(f"Created second user with ID: {user2.user_id}")
    
    # Query both users
    logger.debug("Querying users...")
    result = await session.execute(
        select(User).where(
            User.email.in_([
                "test_multi_user1@quizmasterpro.test",
                "test_multi_user2@quizmasterpro.test"
            ])
        )
    )
    users = result.scalars().all()
    
    # Verify users
    assert len(users) == 2
    emails = {user.email for user in users}
    assert "test_multi_user1@quizmasterpro.test" in emails
    assert "test_multi_user2@quizmasterpro.test" in emails
    logger.info("Multiple operations test passed!")
