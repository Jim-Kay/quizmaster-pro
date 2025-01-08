"""
Authentication Infrastructure Tests
Tests the authentication infrastructure including JWT tokens, user authentication, and WebSocket auth.

Test Metadata:
    Level: 0
    Dependencies: ["test_db_init.py"]
    Blocking: True
    Parallel_Safe: False
    Estimated_Duration: 10
    Working_Directory: backend
    Required_Paths:
        - api/core/database.py
        - api/models.py
        - api/auth.py
        - api/main.py

Environment:
    - Conda Environment: crewai-quizmaster-pro
    - Required Services:
        - PostgreSQL database
        - Backend API server

Setup:
    1. Ensure PostgreSQL is running
    2. Ensure backend API server is running
    3. Set required environment variables:
        - NEXTAUTH_SECRET
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_DB
        - POSTGRES_HOST
        - POSTGRES_PORT

Execution:
    Run with test runner:
    python tests/test_runner.py

Expected Results:
    - All authentication mechanisms should work correctly
    - JWT tokens should be properly generated and validated
    - Protected routes should enforce authentication
    - WebSocket connections should require valid authentication
    - User CRUD operations should work correctly
"""

import os
import jwt
import pytest
import logging
import asyncio
import websockets
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select

from api.auth import create_access_token, get_current_user
from api.core.database import get_db
from api.models import User, LLMProvider  # Using the correct User model with UUID
from api.main import app
from api.core.config import get_settings
from .test_db_init import MOCK_USER_ID, MOCK_USER_EMAIL, MOCK_USER_NAME

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Print database connection details
logging.info(f"Database User: {settings.POSTGRES_USER}")
logging.info(f"Database Name: {settings.TEST_DB_NAME}")
logging.info(f"Database Host: {settings.POSTGRES_HOST}")

# Test configuration
WS_URL = "ws://localhost:8000"

@pytest.fixture
async def test_client():
    """Create a test client"""
    async with AsyncClient(app=app, base_url="http://localhost:8000", follow_redirects=True) as client:
        yield client

@pytest.fixture
async def test_db():
    """Get test database session"""
    async for session in get_db():
        yield session

@pytest.fixture
async def mock_user(test_db):
    """Get the mock user for authentication tests"""
    query = select(User).where(User.user_id == MOCK_USER_ID)
    result = await test_db.execute(query)
    user = result.scalar_one()
    assert user.email == MOCK_USER_EMAIL
    return user

@pytest.fixture
async def test_user(test_db):
    """Create a temporary test user for CRUD testing"""
    # Generate unique user for CRUD tests
    user_id = uuid4()
    email = f"test_crud_{datetime.now().timestamp()}@quizmasterpro.test"
    
    user = User(
        user_id=user_id,
        email=email,
        name="CRUD Test User",
        llm_provider=LLMProvider.OPENAI.value,
        encrypted_openai_key=None,
        encrypted_anthropic_key=None
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    yield user
    
    # Cleanup
    await test_db.delete(user)
    await test_db.commit()

async def test_create_access_token():
    """Test JWT token creation"""
    # Test with default expiration
    token1 = await create_access_token({"sub": MOCK_USER_ID})  
    assert token1
    payload1 = jwt.decode(token1.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload1["sub"] == str(MOCK_USER_ID)  

    # Test with custom expiration
    expires = timedelta(minutes=30)
    token2 = await create_access_token({"sub": MOCK_USER_ID}, expires)  
    assert token2
    payload2 = jwt.decode(token2.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload2["sub"] == str(MOCK_USER_ID)  
    # Verify expiration is set correctly
    exp_time = datetime.fromtimestamp(payload2["exp"])
    assert (exp_time - datetime.utcnow()).total_seconds() <= expires.total_seconds()

async def test_get_current_user(test_db, mock_user):
    """Test current user retrieval from token"""
    token = await create_access_token({"sub": mock_user.user_id})  
    user = await get_current_user(token, test_db)
    assert user
    assert user.user_id == mock_user.user_id  

async def test_protected_route_access(test_client, mock_user):
    """Test protected route access with JWT token"""
    # Try accessing without token
    response = await test_client.get("/api/topics")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try accessing with valid token
    token = await create_access_token({"sub": mock_user.user_id})  
    response = await test_client.get(
        "/api/topics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK

async def test_websocket_auth():
    """Test WebSocket authentication"""
    # Generate test tokens
    valid_token = await create_access_token({"sub": MOCK_USER_ID})  
    invalid_token = "invalid_token"
    expired_token = await create_access_token(
        {"sub": MOCK_USER_ID},  
        expires_delta=timedelta(seconds=-1)
    )

    # Test valid token
    async with websockets.connect(
        f"{WS_URL}/ws?token={valid_token}"
    ) as websocket:
        # Send a test message
        await websocket.send("test")
        # Should receive the message back
        response = await websocket.recv()
        assert response == "test"

    # Test invalid token
    with pytest.raises(websockets.exceptions.InvalidStatusCode):
        async with websockets.connect(
            f"{WS_URL}/ws?token={invalid_token}"
        ):
            pass

    # Test expired token
    with pytest.raises(websockets.exceptions.InvalidStatusCode):
        async with websockets.connect(
            f"{WS_URL}/ws?token={expired_token}"
        ):
            pass

async def test_token_refresh():
    """Test token refresh functionality"""
    # Create initial token
    token = await create_access_token(
        {"sub": MOCK_USER_ID},  
        expires_delta=timedelta(minutes=30)
    )

    # Verify token
    payload = jwt.decode(token.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(MOCK_USER_ID)  

    # TODO: Implement token refresh endpoint test when available
    pass

async def test_main():
    """Main test function"""
    # Set up test database session
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.TEST_DB_NAME}",
        poolclass=NullPool
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create test user
        user = User(
            user_id=uuid4(),
            email=f"test_main_{datetime.now().timestamp()}@quizmasterpro.test",
            name="Test User",
            llm_provider=LLMProvider.OPENAI.value,
            encrypted_openai_key=None,
            encrypted_anthropic_key=None
        )
        
        try:
            session.add(user)
            await session.commit()
            
            # Create test client
            async with AsyncClient(app=app, base_url="http://localhost:8000", follow_redirects=True) as client:
                # Run all tests
                await test_create_access_token()
                await test_get_current_user(session, user)
                await test_protected_route_access(client, user)
                await test_websocket_auth()
                await test_token_refresh()
            
        except Exception as e:
            await session.rollback()
            raise e
            
        finally:
            # Clean up test user
            try:
                await session.delete(user)
                await session.commit()
            except Exception:
                await session.rollback()
            finally:
                await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_main())
