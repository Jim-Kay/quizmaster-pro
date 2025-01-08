"""
Test Database Initialization
Ensures the test database is properly initialized with required mock data.

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
"""

import os
import logging
import asyncio
from uuid import UUID
from sqlalchemy import select
from datetime import datetime

from api.models import User, LLMProvider
from api.core.database import get_test_db

# Mock user constants - these should be used across all tests
MOCK_USER_ID = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
MOCK_USER_EMAIL = 'test_mock_user@quizmasterpro.test'
MOCK_USER_NAME = 'Mock Test User'

async def ensure_mock_user_exists():
    """Ensure our mock test user exists in the database"""
    logging.info("Checking for mock test user...")
    
    async for db in get_test_db():
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
                llm_provider=LLMProvider.OPENAI.value,
                encrypted_openai_key=None,
                encrypted_anthropic_key=None
            )
            db.add(user)
            await db.commit()
            logging.info("Mock test user created successfully")
        else:
            logging.info("Mock test user already exists")
            
        # Verify mock user
        result = await db.execute(query)
        mock_user = result.scalar_one()
        assert mock_user.user_id == MOCK_USER_ID
        assert mock_user.email == MOCK_USER_EMAIL
        logging.info("Mock test user verified")
        
async def test_main():
    """Main test function"""
    logging.info("Testing database connection...")
    logging.info(f"Database URL: {os.getenv('DATABASE_URL')}")
    logging.info(f"Database User: {os.getenv('POSTGRES_USER')}")
    logging.info(f"Database Name: {os.getenv('POSTGRES_DB')}")
    
    await ensure_mock_user_exists()
    
if __name__ == "__main__":
    asyncio.run(test_main())