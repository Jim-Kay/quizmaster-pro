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
import logging
import asyncio
from uuid import UUID
from sqlalchemy import select, text
from datetime import datetime
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.core.base import Base
from api.core.database import get_db
from api.core.models import (
    User, LLMProvider, Topic, Blueprint, TerminalObjective,
    EnablingObjective, FlowExecution, IdempotencyKey, FlowLog,
    FlowExecutionStatus, CognitiveLevelEnum, LogLevel
)

# Mock user constants - these should be used across all tests
# WARNING: This mock user should NEVER be deleted as other tests depend on it
MOCK_USER_ID = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
MOCK_USER_EMAIL = 'test_mock_user@quizmasterpro.test'
MOCK_USER_NAME = 'Mock Test User'

async def init_test_database():
    """Initialize test database with tables if they don't exist"""
    # Note: We only create tables if they don't exist
    # We do NOT drop tables to preserve the mock user
    # Get database URL from environment variables
    DB_USER = os.getenv("POSTGRES_USER", "test_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "test_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = "quizmaster_test"
    
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Bind engine to Base
    Base.metadata.bind = engine
    
    async with engine.begin() as conn:
        # Drop all tables except users
        await conn.execute(text("DROP TABLE IF EXISTS flow_logs CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS idempotency_keys CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS flow_executions CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS enabling_objectives CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS terminal_objectives CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS blueprints CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS topics CASCADE"))
        
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()

async def ensure_mock_user_exists():
    """
    Ensure our mock test user exists in the database.
    This user should NEVER be deleted as it's used by other tests for authentication.
    """
    logging.info("Checking for mock test user...")
    
    async for db in get_db():
        # Check if mock user exists
        query = select(User).where(User.user_id == MOCK_USER_ID)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user is None:
            logging.info("Creating mock test user...")
            user = User(
                user_id=MOCK_USER_ID,
                email=MOCK_USER_EMAIL,
                name=MOCK_USER_NAME,
                llm_provider=LLMProvider.openai,
                encrypted_openai_key=None,
                encrypted_anthropic_key=None
            )
            db.add(user)
            await db.commit()
            logging.info("Mock test user created successfully")
        else:
            logging.info("Mock test user already exists")
            # Verify mock user has correct data
            if (existing_user.email != MOCK_USER_EMAIL or 
                existing_user.name != MOCK_USER_NAME or
                existing_user.llm_provider != LLMProvider.openai):
                logging.info("Updating mock test user data...")
                existing_user.email = MOCK_USER_EMAIL
                existing_user.name = MOCK_USER_NAME
                existing_user.llm_provider = LLMProvider.openai
                await db.commit()
                logging.info("Mock test user data updated")

async def test_mock_user_exists():
    """Test that we can find the mock test user"""
    logging.info("Testing database connection...")
    logging.info(f"Database URL: {None}")  # Don't log the full URL
    logging.info(f"Database User: {os.getenv('POSTGRES_USER', 'test_user')}")
    logging.info(f"Database Name: quizmaster_test")
    
    # Initialize database and ensure mock user exists
    await init_test_database()
    await ensure_mock_user_exists()
    
    async for db in get_db():
        # Verify mock user exists and has correct data
        query = select(User).where(User.user_id == MOCK_USER_ID)
        result = await db.execute(query)
        user = result.scalar_one()
        
        assert user is not None, "Mock test user not found"
        assert user.email == MOCK_USER_EMAIL, f"Mock user email mismatch: {user.email} != {MOCK_USER_EMAIL}"
        assert user.name == MOCK_USER_NAME, f"Mock user name mismatch: {user.name} != {MOCK_USER_NAME}"
        
        logging.info("Mock test user verified")

async def test_main():
    """Main test function"""
    await test_mock_user_exists()

if __name__ == "__main__":
    asyncio.run(test_main())
