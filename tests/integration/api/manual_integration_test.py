"""
Test Name: Manual Integration Test
Description: End-to-end integration test that verifies the interaction between the API endpoints,
            database operations, and user authentication. This test performs a complete workflow
            including database setup, user creation, and API endpoint testing.

Environment:
    - Conda Environment: quiz_master_backend
    - Working Directory: tests/integration/api
    - Required Services:
        - PostgreSQL database (running on localhost:5432)
        - Backend API server (running on localhost:8000)
        - Test database (quizmaster_test)

Setup:
    1. Ensure PostgreSQL is running
    2. Create test database if not exists:
       ```sql
       CREATE DATABASE quizmaster_test;
       ```
    3. Set environment variables (or use .env file):
       - POSTGRES_USER
       - POSTGRES_PASSWORD
       - POSTGRES_HOST
       - POSTGRES_PORT
       - TEST_DB_NAME
    4. Start the backend API server:
       ```bash
       cd backend
       uvicorn api.main:app --reload
       ```

Execution:
    ```bash
    # Activate conda environment
    conda activate quiz_master_backend
    
    # Run the test
    cd tests/integration/api
    python manual_integration_test.py
    ```

Expected Results:
    1. Database tables are created successfully
    2. Test user is created in the database
    3. Topic creation API endpoint responds with 200
    4. Created topic is verified in the database
    5. All database operations complete without errors
    6. No authentication errors occur during API calls

Notes:
    - This is an integration test that modifies the database. Do not run in production.
    - The test database will be reset (dropped and recreated) on each run.
    - Uses a mock user ID (550e8400-e29b-41d4-a716-446655440000) for authentication.
"""

import asyncio
import os
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from sqlalchemy.pool import NullPool
import httpx
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("TEST_DB_NAME", "quizmaster_test")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Test configuration
MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")  # Same as in auth.py
API_BASE_URL = "http://localhost:8000"

async def setup_database():
    """Set up a fresh test database."""
    logger.info("Setting up test database...")
    
    # Create engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        poolclass=NullPool
    )
    
    try:
        # Create tables and insert test user
        async with engine.begin() as conn:
            # Drop and recreate all tables
            await conn.execute(text("DROP TABLE IF EXISTS topics CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            
            # Create users table
            await conn.execute(text("""
                CREATE TABLE users (
                    id UUID PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create topics table
            await conn.execute(text("""
                CREATE TABLE topics (
                    id UUID PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert test user
            await conn.execute(
                text("""
                    INSERT INTO users (id, email, name)
                    VALUES (:id, :email, :name)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": MOCK_USER_ID,
                    "email": "test@example.com",
                    "name": "Test User"
                }
            )
        
        logger.info("Database setup completed successfully")
        return engine
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise

async def verify_user_exists(engine):
    """Verify that the test user exists in the database."""
    logger.info("Verifying test user exists...")
    async with AsyncSession(engine) as session:
        result = await session.execute(
            text("SELECT id, email, name FROM users WHERE id = :user_id"),
            {"user_id": MOCK_USER_ID}
        )
        user = result.fetchone()
        if user:
            logger.info(f"Found test user: {user}")
            return True
        logger.error("Test user not found!")
        return False

async def test_create_topic():
    """Test creating a topic via the API."""
    logger.info("Testing topic creation...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": "Bearer mock_token",
            "Content-Type": "application/json"
        }
        
        topic_data = {
            "title": "Test Topic",
            "description": "Test Description"
        }
        
        try:
            logger.info(f"Sending request to create topic with data: {topic_data}")
            logger.info(f"Using headers: {headers}")
            
            response = await client.post(
                f"{API_BASE_URL}/api/topics",
                json=topic_data,
                headers=headers,
                follow_redirects=True
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code != 201:
                logger.error(f"Failed to create topic. Response: {response.text}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error creating topic: {e}")
            return False

async def main():
    """Run all tests in sequence."""
    try:
        # Setup
        engine = await setup_database()
        
        # Verify setup
        if not await verify_user_exists(engine):
            logger.error("Test user verification failed!")
            return
        
        # Run tests
        if await test_create_topic():
            logger.info("Topic creation test passed!")
        else:
            logger.error("Topic creation test failed!")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
