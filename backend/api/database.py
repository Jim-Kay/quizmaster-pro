from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Get environment variables with default values
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'quizmaster')  # Use main database instead of test

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

logger = logging.getLogger(__name__)

async def get_db():
    async with async_session_maker() as session:
        yield session

async def init_db():
    """Initialize the database and create tables."""
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized.")

async def add_generation_started_at_column():
    """Add generation_started_at column to blueprints table."""
    from sqlalchemy import Column, DateTime, text
    from sqlalchemy.dialects.postgresql import TIMESTAMP
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='blueprints' AND column_name='generation_started_at'"
        ))
        if not result.scalar():
            # Add column if it doesn't exist
            await conn.execute(text(
                "ALTER TABLE blueprints "
                "ADD COLUMN generation_started_at TIMESTAMP WITH TIME ZONE"
            ))
            logger.info("Added generation_started_at column to blueprints table")
