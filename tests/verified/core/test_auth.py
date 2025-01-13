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

import pytest
import pytest_asyncio
import logging
import os
from typing import Dict, AsyncGenerator
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.sql import text
from fastapi.testclient import TestClient
from httpx import AsyncClient
from starlette import status
from starlette.websockets import WebSocketDisconnect

from api.core.models import User, Base
from api.core.config import get_settings
from api.main import app
from api.core.database import get_db
from api.auth import create_access_token, verify_token

# Configure pytest-asyncio
pytestmark = [
    pytest.mark.asyncio(scope="function"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning")
]

# Set up logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Override host for local testing if not in Docker
if not os.path.exists('/.dockerenv'):
    settings.postgres_host = 'localhost'

# Database configuration
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/quizmaster_test"

@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    
    await engine.dispose()

@pytest_asyncio.fixture
async def mock_user(session: AsyncSession) -> Dict:
    """Create a mock user for testing"""
    logger.info("Creating mock user...")
    
    # Delete any existing test users first
    test_email = "test_mock_user@quizmasterpro.test"
    await session.execute(
        text("DELETE FROM users WHERE email = :email"),
        {"email": test_email}
    )
    await session.commit()
    
    # Create mock user
    user = User(
        email=test_email,
        name="Test Mock User"
    )
    session.add(user)
    await session.commit()
    
    return {
        "id": str(user.user_id),
        "email": user.email,
        "is_active": True
    }

@pytest.mark.asyncio
async def test_create_access_token(mock_user: Dict):
    """Test access token creation"""
    logger.info("Testing access token creation...")
    token = await create_access_token(data={"sub": mock_user["id"]})
    assert isinstance(token, str)
    assert len(token) > 0

@pytest.mark.asyncio
async def test_get_current_user(session: AsyncSession, mock_user: Dict):
    """Test getting current user from token"""
    logger.info("Testing get current user...")
    
    # Create token
    token = await create_access_token(data={"sub": mock_user["id"]})
    
    # Get user from token
    user = await verify_token(token, session)
    assert user is not None
    assert str(user.user_id) == mock_user["id"]
    assert user.email == mock_user["email"]

@pytest.mark.asyncio
async def test_protected_route_access(session: AsyncSession, mock_user: Dict):
    """Test access to protected route with token"""
    logger.info("Testing protected route access...")
    
    # Create token
    token = await create_access_token(data={"sub": mock_user["id"]})
    
    # Override get_db dependency
    async def override_get_db():
        yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == mock_user["email"]
        assert data["id"] == mock_user["id"]

@pytest.mark.asyncio
async def test_websocket_auth(session: AsyncSession, mock_user: Dict):
    """Test WebSocket authentication"""
    logger.info("Testing WebSocket authentication...")
    
    # Create token
    token = await create_access_token(data={"sub": mock_user["id"]})
    
    # Override get_db dependency
    async def override_get_db():
        try:
            yield session
        finally:
            await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with valid token
        async with client.websocket_connect(f"/api/ws?token={token}") as websocket:
            data = await websocket.receive_json()
            assert data["type"] == "connection_established"
            assert data["user_id"] == str(mock_user["id"])
        
        # Test with invalid token
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with client.websocket_connect("/api/ws?token=invalid_token"):
                pass
        assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
    
    # Clean up dependency override
    app.dependency_overrides.clear()
