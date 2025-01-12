#!/usr/bin/env python
"""Initialize development database schema."""
import os
import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
MOCK_USER_ID = UUID("f9b5645d-898b-4d58-b10a-a6b50a9d234b")
MOCK_USER_EMAIL = "mock.user@example.com"
MOCK_USER_NAME = "Mock User"

async def init_dev_db():
    """Initialize development database schema."""
    # Set environment
    os.environ["QUIZMASTER_ENVIRONMENT"] = "development"
    
    # Add backend directory to Python path
    backend_dir = str(Path(__file__).parent.parent / "backend")
    os.environ["PYTHONPATH"] = backend_dir
    sys.path.insert(0, backend_dir)

    # Load environment variables from .env file
    env_file = Path(__file__).parent.parent / "backend" / ".env.development"
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    
    # Import these after setting environment variables
    from api.core.models import Base, User
    from api.schemas.pydantic_schemas import LLMProvider
    
    # Create database URL
    DB_USER = os.getenv("POSTGRES_USER", "test_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "test_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "quizmaster_dev")
    
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info(f"Connecting to database: {DB_NAME}")
    
    # Create engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10
    )
    
    try:
        async with engine.begin() as conn:
            # Drop all tables except users
            logger.info("Dropping existing tables...")
            await conn.execute(text("DROP TABLE IF EXISTS flow_logs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS idempotency_keys CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS flow_executions CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS enabling_objectives CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS terminal_objectives CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS blueprints CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS topics CASCADE"))
            
            # Create all tables
            logger.info("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Create mock user if not exists
            logger.info("Creating mock user...")
            result = await conn.execute(
                text("SELECT user_id FROM users WHERE user_id = :user_id"),
                {"user_id": MOCK_USER_ID}
            )
            if not result.scalar():
                await conn.execute(
                    text("""
                        INSERT INTO users (user_id, email, name, llm_provider)
                        VALUES (:user_id, :email, :name, :llm_provider)
                    """),
                    {
                        "user_id": MOCK_USER_ID,
                        "email": MOCK_USER_EMAIL,
                        "name": MOCK_USER_NAME,
                        "llm_provider": LLMProvider.openai.value
                    }
                )
            
            # Commit all changes
            await conn.commit()
            logger.info("Database initialization complete")
    
    finally:
        await engine.dispose()
        logger.info("Database connection closed")

if __name__ == "__main__":
    asyncio.run(init_dev_db())
