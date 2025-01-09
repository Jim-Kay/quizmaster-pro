"""
Test Name: Authentication Core Service Tests
Description: Tests the authentication infrastructure including JWT tokens, user authentication, and WebSocket auth.

Environment:
    - Conda Environment: crewai-quizmaster-pro
    - Working Directory: backend
    - Required Services:
        - PostgreSQL Database
        - Backend API Server

Setup:
    1. Ensure PostgreSQL is running
    2. Set TEST_MODE=true environment variable
    3. Set database connection environment variables:
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_HOST
        - POSTGRES_PORT
    4. Add backend directory to PYTHONPATH

Execution:
    python tests/test_runner.py

Expected Results:
    1. JWT token creation succeeds with correct payload and expiration
    2. User retrieval from token works correctly
    3. Protected route access with valid token succeeds
    4. WebSocket connection with valid token succeeds
    5. Token refresh generates new token with extended expiration

Test Metadata:
    Level: 1  # Core Service Test
    Dependencies: [c:/ParseThat/QuizMasterPro/tests/verified/infrastructure/test_db_init.py]
    Blocking: True
    Parallel_Safe: False
    Estimated_Duration: 10
    Working_Directory: backend
    Required_Paths:
        - api/core/database.py
        - api/core/models.py
        - api/auth.py
        - api/main.py
"""

import os
import jwt
import pytest
import logging
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from api.core.config import get_settings
from api.core.database import get_db
from api.core.models import User, LLMProvider
from api.auth import create_access_token, get_current_user
from api.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

test_client = TestClient(app)

@pytest.fixture
async def test_db():
    """Get test database session"""
    async for db in get_db():
        yield db

@pytest.fixture
async def mock_user(test_db):
    """Get the mock user for authentication tests"""
    query = select(User).where(User.user_id == UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b'))
    result = await test_db.execute(query)
    user = result.scalar_one()
    return user

@pytest.fixture
async def test_user(test_db):
    """Create a temporary test user for CRUD testing"""
    # Create test user
    test_user = User(
        user_id=uuid4(),
        email='test_auth_user@quizmasterpro.test',
        name='Test Auth User',
        llm_provider=LLMProvider.openai.value,
        encrypted_openai_key=None,
        encrypted_anthropic_key=None
    )
    test_db.add(test_user)
    await test_db.commit()
    
    yield test_user
    
    # Cleanup
    await test_db.delete(test_user)
    await test_db.commit()

async def test_create_access_token():
    """Test JWT token creation"""
    user_id = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
    token = await create_access_token({"sub": str(user_id)})
    
    # Verify token
    payload = jwt.decode(token.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    
    # Verify expiration
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert exp > now
    assert exp <= now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)

async def test_get_current_user(test_db, mock_user):
    """Test current user retrieval from token"""
    # Create token
    token = await create_access_token({"sub": str(mock_user.user_id)})
    
    # Get current user
    user = await get_current_user(token, test_db)
    assert user is not None
    assert user.user_id == mock_user.user_id
    assert user.email == mock_user.email

async def test_protected_route_access(mock_user):
    """Test protected route access with JWT token"""
    # Create token
    token = await create_access_token({"sub": str(mock_user.user_id)})
    
    # Test protected route
    response = test_client.get(
        "/api/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == str(mock_user.user_id)

async def test_websocket_auth():
    """Test WebSocket authentication"""
    # Create token
    user_id = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
    token = await create_access_token({"sub": str(user_id)})
    
    # Test WebSocket connection
    with test_client.websocket_connect(
        f"/ws/test?token={token}"
    ) as websocket:
        # Send test message
        websocket.send_text("test")
        
        # Receive response
        data = websocket.receive_text()
        assert data == "test"
        
        # Close connection
        websocket.close()

async def test_token_refresh():
    """Test token refresh functionality"""
    # Create initial token
    user_id = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
    token = await create_access_token({"sub": str(user_id)})
    
    # Verify token
    payload = jwt.decode(token.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    
    # Create refresh token
    refresh_token = await create_access_token(
        {"sub": str(user_id)},
        expires_delta=timedelta(days=7)
    )
    
    # Verify refresh token
    refresh_payload = jwt.decode(refresh_token.encode(), settings.SECRET_KEY, algorithms=["HS256"])
    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["exp"] > payload["exp"]

async def test_main():
    """Main test function"""
    async for db in get_db():
        await test_create_access_token()
        await test_get_current_user(db, mock_user)
        await test_protected_route_access(mock_user)
        await test_websocket_auth()
        await test_token_refresh()

if __name__ == "__main__":
    asyncio.run(test_main())
