"""
Test Name: Authentication Core Service Tests
Description: Tests the authentication infrastructure including JWT tokens, user authentication, and WebSocket auth.

Test Metadata:
    Level: 1
    Dependencies: [
        "c:/ParseThat/QuizMasterPro/tests/verified/infrastructure/test_db_init.py"
    ]
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
        - PostgreSQL Database
        - Backend API Server

Setup:
    1. Ensure PostgreSQL is running
    2. Set environment variables:
        - TEST_MODE=true
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_HOST
        - POSTGRES_PORT
    3. Add backend directory to PYTHONPATH

Execution:
    pytest tests/verified/core/test_auth.py -v

Expected Results:
    1. JWT token creation succeeds with correct payload
    2. User retrieval from token works correctly
    3. Protected route access with valid token succeeds
    4. WebSocket connection with valid token succeeds
    5. Token refresh generates new valid token

Notes:
    This test is part of Level 1 core tests and depends on
    the mock user being properly initialized in the database.
"""

import jwt
import pytest
import logging
import asyncio
from uuid import UUID
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from typing import Dict, AsyncGenerator

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from api.core.models import User
from api.core.config import get_settings
from api.core.database import test_engine
from api.auth import create_access_token, get_current_user
from api.main import app

from starlette.testclient import TestClient

# Set up logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Test database engine
@pytest.fixture(scope="session")
async def async_engine() -> AsyncEngine:
    """Get async database engine"""
    engine = await test_engine()
    yield engine
    await engine.dispose()

# Test database session
@pytest.fixture(scope="function")
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    logger.info("Creating test database session...")
    
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Mock user for testing
@pytest.fixture(scope="function")
async def mock_user(db_session: AsyncSession) -> Dict:
    """Create a mock user for testing"""
    logger.info("Creating mock user...")
    
    # Get session from generator
    session = await db_session.__anext__()
    
    # Check if mock user exists
    result = await session.execute(
        select(User).where(User.email == "test_mock_user@quizmasterpro.test")
    )
    user = result.scalar_one_or_none()
    
    if user is not None:
        return {
            "id": str(user.user_id),
            "email": user.email,
            "is_active": True
        }
    
    # Create mock user
    user = User(
        email="test_mock_user@quizmasterpro.test",
        name="Test Mock User"
    )
    session.add(user)
    await session.commit()
    
    return {
        "id": str(user.user_id),
        "email": user.email,
        "is_active": True
    }

@pytest.fixture(scope="module")
def test_client() -> TestClient:
    """Create a test client"""
    return TestClient(app)

@pytest.mark.asyncio
async def test_create_access_token(mock_user: Dict):
    """Test JWT token creation"""
    logger.info("Testing JWT token creation...")
    
    # Get mock user data
    user_data = await mock_user
    
    # Create token
    token = await create_access_token(data={"sub": user_data["id"]})
    
    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    assert payload["sub"] == user_data["id"]
    assert "exp" in payload
    assert isinstance(payload["exp"], int)

@pytest.mark.asyncio
async def test_get_current_user(
    db_session: AsyncSession,
    mock_user: Dict,
    test_client: TestClient
):
    """Test current user retrieval from token"""
    logger.info("Testing user retrieval from token...")
    
    # Get mock user data and session
    user_data = await mock_user
    session = await db_session.__anext__()
    
    # Create token
    token = await create_access_token(data={"sub": user_data["id"]})
    
    # Get user from token
    user = await get_current_user(token, session)
    
    # Verify user data
    assert user is not None
    assert str(user.user_id) == user_data["id"]
    assert user.email == user_data["email"]

@pytest.mark.asyncio
async def test_protected_route_access(
    test_client: TestClient,
    mock_user: Dict
):
    """Test access to protected route with token"""
    logger.info("Testing protected route access...")
    
    # Get mock user data
    user_data = await mock_user
    
    # Create token
    token = await create_access_token(data={"sub": user_data["id"]})
    
    # Test access to protected route
    response = test_client.get(
        "/api/topics",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_websocket_auth(
    test_client: TestClient,
    mock_user: Dict
):
    """Test WebSocket authentication"""
    logger.info("Testing WebSocket authentication...")
    
    # Get mock user data
    user_data = await mock_user
    
    # Create token
    token = await create_access_token(data={"sub": user_data["id"]})
    
    # Test WebSocket connection
    with test_client.websocket_connect(
        f"/api/ws?token={token}"
    ) as websocket:
        # Test initial connection message
        data = websocket.receive_json()
        assert data["type"] == "websocket.connect"
        assert data["message"] == "Connection established"
        
        # Test echo functionality
        test_message = "Hello WebSocket!"
        websocket.send_json({"message": test_message})
        response = websocket.receive_json()
        assert response["message"] == test_message
