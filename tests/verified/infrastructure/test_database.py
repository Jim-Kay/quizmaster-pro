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
import pytest
import pytest_asyncio
import logging
from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
from urllib.parse import urlparse

# Import from backend package
from api.core.database import get_db
from api.core.config import get_settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Override host for local testing if not in Docker
if not os.path.exists('/.dockerenv'):
    settings.postgres_host = 'localhost'

# Database configuration
DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.test_db_name}"

@pytest.fixture
def database_url():
    return DATABASE_URL

@pytest.mark.asyncio
async def test_database_connection(database_url):
    """Test database connection"""
    logging.info("Testing database connection...")
    
    # Get database URL components
    parsed = urlparse(database_url)
    logging.info(f"Database User: {parsed.username}")
    logging.info(f"Database Name: {parsed.path[1:]}")  # Remove leading '/'
    
    try:
        engine = create_async_engine(database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("Database connection successful")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        pytest.fail(f"Database connection failed: {str(e)}")

@pytest.mark.asyncio
async def test_database_operations(database_url):
    """Test basic database operations"""
    logger.info("Testing database operations...")
    
    engine = create_async_engine(
        database_url,
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
            await session.commit()
            
            # Query the test record
            result = await session.execute(text(
                "SELECT * FROM test_table WHERE name = 'test'"
            ))
            row = result.fetchone()
            assert row is not None, "Test record not found"
            assert row[1] == 'test', "Test record has incorrect value"
            
            # Clean up
            await session.execute(text("DROP TABLE test_table"))
            await session.commit()
            
            logger.info("Database operations successful")
    except Exception as e:
        logger.error(f"Database operations failed: {str(e)}")
        pytest.fail(f"Database operations failed: {str(e)}")
    finally:
        await engine.dispose()
