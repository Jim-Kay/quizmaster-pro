"""
Database Infrastructure Test
Verifies basic database connectivity and operations.

Test Metadata:
    Level: 0
    Dependencies: []
    Blocking: True
    Parallel_Safe: True
    Estimated_Duration: 10
    Working_Directory: backend
    Required_Paths:
        - api/models
        - api/core/database.py
        - api/core/config.py
"""

import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
from urllib.parse import urlparse

# Import from backend package
from api.core.database import get_async_session
from api.core.config import get_settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Database configuration
DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.TEST_DB_NAME}"

def get_database_url():
    return DATABASE_URL

async def test_database_connection():
    """Test database connection"""
    logging.info("Testing database connection...")
    
    # Get database URL components
    db_url = get_database_url()
    logging.info(f"Database URL: {db_url}")
    
    # Extract user and database name from URL
    parsed = urlparse(db_url)
    logging.info(f"Database User: {parsed.username}")
    logging.info(f"Database Name: {parsed.path[1:]}")  # Remove leading '/'
    
    try:
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("Database connection successful")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        return False

async def test_database_operations():
    """Test basic database operations"""
    logger.info("Testing database operations...")
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Create a test table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            
            # Insert a test record
            await session.execute(text(
                "INSERT INTO test_table (name) VALUES ('test')"
            ))
            
            # Query the test record
            result = await session.execute(text(
                "SELECT name FROM test_table WHERE name = 'test'"
            ))
            row = result.scalar()
            assert row == 'test'
            
            # Clean up
            await session.execute(text("DROP TABLE test_table"))
            await session.commit()
            
            logger.info("Database operations successful")
            return True
    except Exception as e:
        logger.error(f"Database operations failed: {e}")
        return False

async def test_main():
    """Main test function"""
    success = await test_database_connection()
    assert success, "Database connection test failed"
    
    success = await test_database_operations()
    assert success, "Database operations test failed"

if __name__ == "__main__":
    asyncio.run(test_main())
