import os
import sys
import pytest
import asyncio
from urllib.parse import quote
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text, select
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import uuid
from httpx import AsyncClient, ASGITransport
import asyncpg

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from api.models import Base, User

# Load environment variables from .env file
load_dotenv()

# Set mock auth for testing
os.environ["MOCK_AUTH"] = "true"

# Database URL for testing
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "quizmaster")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{quote(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Note: We removed the event_loop fixture as we'll use pytest.mark.asyncio with scope instead

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create a test engine for the test session."""
    # First connect to default 'postgres' database to create test database
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database="postgres"
        )
        
        # Drop any existing connections to the test database
        await conn.execute(f'''
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
            AND pid <> pg_backend_pid()
        ''')
        
        # Create test database if it doesn't exist
        await conn.execute(f'DROP DATABASE IF EXISTS {DB_NAME}')
        await conn.execute(f'CREATE DATABASE {DB_NAME}')
        await conn.close()
    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise
    
    # Now connect to the test database
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        poolclass=NullPool  # Disable connection pooling
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
        # Create test user directly in the database
        await conn.execute(
            text("""
                INSERT INTO users (user_id, email, name)
                VALUES (:user_id, :email, :name)
                ON CONFLICT (user_id) DO NOTHING
            """),
            {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "test@example.com",
                "name": "Test User"
            }
        )
    
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

@pytest.fixture(autouse=True)
async def clean_tables(test_session):
    """Clean all tables before each test."""
    async with test_session.begin():
        for table in reversed(Base.metadata.sorted_tables):
            if table.name != 'users':  # Don't delete the test user
                await test_session.execute(text(f'TRUNCATE TABLE {table.name} CASCADE'))
    await test_session.commit()

@pytest.fixture(scope="function")
async def test_session(test_engine):
    """Create a test session for each test."""
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    session = async_session()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()

@pytest.fixture(scope="function")
async def test_user(test_session):
    """Get the test user for each test."""
    user_query = await test_session.execute(
        select(User).where(User.user_id == uuid.UUID("550e8400-e29b-41d4-a716-446655440000"))
    )
    user = user_query.scalar_one()
    return user

@pytest.fixture
async def client(test_session):
    """Create a test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as client:
        yield client
