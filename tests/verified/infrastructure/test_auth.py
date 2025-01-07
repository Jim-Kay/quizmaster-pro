"""
Authentication Infrastructure Tests
Tests the authentication infrastructure including JWT tokens, user authentication, and WebSocket auth.

Test Metadata:
    Level: 0
    Dependencies: []
    Blocking: True
    Parallel_Safe: False
    Estimated_Duration: 10
    Working_Directory: backend
    Required_Paths:
        - api/core/database.py
        - api/core/models.py
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
"""

import os
import jwt
import pytest
import logging
import asyncio
import websockets
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from api.auth import create_access_token, get_current_user
from api.core.database import get_db
from api.core.models import User
from api.main import app
from api.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Test configuration
MOCK_USER_ID = 12345  # Using integer ID instead of UUID
MOCK_USER_EMAIL = "test@example.com"
MOCK_USER_PASSWORD = "test_password"
WS_URL = "ws://localhost:8000"

@pytest.fixture
async def test_client():
    """Create a test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_db():
    """Get test database session"""
    async for session in get_db():
        yield session

@pytest.fixture
async def test_user(test_db):
    """Create a test user"""
    user = User(
        id=MOCK_USER_ID,
        email=MOCK_USER_EMAIL,
        hashed_password="hashed_password",  # In real tests, use proper hashing
        llm_provider="OPENAI"  # Required field
    )
    test_db.add(user)
    await test_db.commit()
    yield user
    await test_db.delete(user)
    await test_db.commit()

async def test_create_access_token():
    """Test JWT token creation"""
    # Test with default expiration
    token1 = await create_access_token({"sub": str(MOCK_USER_ID)})
    assert token1
    payload1 = jwt.decode(token1.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload1["sub"] == str(MOCK_USER_ID)

    # Test with custom expiration
    expires = timedelta(minutes=30)
    token2 = await create_access_token({"sub": str(MOCK_USER_ID)}, expires)
    assert token2
    payload2 = jwt.decode(token2.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload2["sub"] == str(MOCK_USER_ID)
    # Verify expiration is set correctly
    exp_time = datetime.fromtimestamp(payload2["exp"])
    assert (exp_time - datetime.utcnow()).total_seconds() <= expires.total_seconds()

async def test_get_current_user(test_db, test_user):
    """Test current user retrieval from token"""
    token = await create_access_token({"sub": str(test_user.id)})
    user = await get_current_user(token, test_db)
    assert user
    assert user.id == test_user.id
    assert user.email == test_user.email

async def test_protected_route_access(test_client, test_user):
    """Test access to protected routes"""
    # Try accessing protected route without token
    response = await test_client.get("/api/topics")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try accessing with valid token
    token = await create_access_token({"sub": str(test_user.id)})
    response = await test_client.get(
        "/api/topics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK

    # Try accessing with invalid token
    response = await test_client.get(
        "/api/topics",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_websocket_auth():
    """Test WebSocket authentication"""
    # Generate test tokens
    valid_token = await create_access_token({"sub": str(MOCK_USER_ID)})
    invalid_token = "invalid_token"
    expired_token = await create_access_token(
        {"sub": str(MOCK_USER_ID)},
        expires_delta=timedelta(seconds=-1)
    )

    # Test valid token
    try:
        async with websockets.connect(
            f"{WS_URL}/ws/flow?token={valid_token}"
        ) as websocket:
            assert websocket.open
    except websockets.exceptions.InvalidStatusCode as e:
        pytest.fail(f"WebSocket connection failed with valid token: {e}")

    # Test invalid token
    with pytest.raises(websockets.exceptions.InvalidStatusCode):
        async with websockets.connect(
            f"{WS_URL}/ws/flow?token={invalid_token}"
        ):
            pytest.fail("Should not connect with invalid token")

    # Test expired token
    with pytest.raises(websockets.exceptions.InvalidStatusCode):
        async with websockets.connect(
            f"{WS_URL}/ws/flow?token={expired_token}"
        ):
            pytest.fail("Should not connect with expired token")

async def test_token_refresh():
    """Test token refresh functionality"""
    # Create initial token
    token = await create_access_token(
        {"sub": str(MOCK_USER_ID)},
        expires_delta=timedelta(minutes=30)
    )

    # Verify token is valid
    payload = jwt.decode(token.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(MOCK_USER_ID)

    # TODO: Implement token refresh endpoint test when available
    pass

async def test_main():
    """Main test function"""
    # Set up test database session
    engine = create_async_engine(
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}",
        poolclass=NullPool
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create test user
        user = User(
            id=MOCK_USER_ID,
            email=MOCK_USER_EMAIL,
            hashed_password="hashed_password",  # In real tests, use proper hashing
            llm_provider="OPENAI"  # Required field
        )
        
        try:
            session.add(user)
            await session.commit()
            
            # Create test client
            async with AsyncClient(app=app, base_url="http://test") as client:
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
