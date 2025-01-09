"""
Test Name: Authentication Core Service Tests
Description: Tests the authentication infrastructure including JWT tokens, user authentication, and WebSocket auth.

IMPORTANT: This module uses both the persistent mock user (from test_db_init.py) and temporary test users.
- For authentication tests, we use the mock user which should NEVER be deleted
- For CRUD testing, we create temporary test users that are cleaned up after each test

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

Test User Types:
    This module works with two types of test users:
    1. Mock User (imported from test_db_init):
       - Used for authentication testing
       - Should NEVER be deleted
       - Has fixed UUID: f9b5645d-898b-4d58-b10a-a6b50a9d234b
    
    2. Temporary Test User (created here):
       - Used for CRUD testing
       - Created and deleted during tests
       - Has UUID: a1b2c3d4-e5f6-4321-8765-9abcdef01234
       - Safe to delete and recreate

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

import jwt
import asyncio
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.database import get_db
from api.core.models import User, LLMProvider
from api.auth import create_access_token, get_current_user
from api.main import app
from fastapi.testclient import TestClient

test_client = TestClient(app)
settings = get_settings()

# Import mock user constants from test_db_init using relative import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from verified.infrastructure.test_db_init import (
    MOCK_USER_ID,
    MOCK_USER_EMAIL,
    MOCK_USER_NAME
)

async def get_test_db():
    """Get test database session"""
    async for db in get_db():
        return db

async def get_mock_user(db):
    """
    Get the mock user for authentication tests.
    This is the persistent mock user that should NEVER be deleted.
    """
    query = select(User).where(User.user_id == MOCK_USER_ID)
    result = await db.execute(query)
    user = result.scalar_one()
    return user

async def create_temp_test_user():
    """
    Create a temporary test user for CRUD testing.
    This user is safe to delete and recreate, unlike the mock user.
    """
    temp_user_id = UUID('a1b2c3d4-e5f6-4321-8765-9abcdef01234')
    test_user = User(
        user_id=temp_user_id,  # Different UUID from mock user
        email='test_auth_user@quizmasterpro.test',
        name='Test Auth User',
        llm_provider=LLMProvider.openai
    )
    
    async for session in get_db():
        # First delete any existing test user
        stmt = select(User).where(User.user_id == temp_user_id)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            await session.delete(existing_user)
            await session.commit()
        
        # Now create the new test user
        session.add(test_user)
        await session.commit()
        
    return test_user

async def cleanup_test_user(db, test_user):
    """
    Clean up temporary test user after tests.
    Never deletes the mock user (MOCK_USER_ID) as it's needed by other tests.
    """
    if test_user.user_id != MOCK_USER_ID:  # Never delete the mock user
        await db.delete(test_user)
        await db.commit()

async def test_create_access_token():
    """Test creating an access token"""
    db = await get_test_db()
    mock_user = await get_mock_user(db)
    
    token = create_access_token(
        data={"sub": mock_user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    assert token is not None
    decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert decoded["sub"] == mock_user.email

async def test_get_current_user():
    """Test getting current user from token"""
    db = await get_test_db()
    mock_user = await get_mock_user(db)
    
    token = create_access_token(
        data={"sub": mock_user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    current_user = await get_current_user(token)
    assert current_user is not None
    assert current_user.email == mock_user.email

async def test_invalid_token():
    """Test invalid token handling"""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid_token")
    assert exc_info.value.status_code == 401

async def test_expired_token():
    """Test expired token handling"""
    db = await get_test_db()
    mock_user = await get_mock_user(db)
    
    token = create_access_token(
        data={"sub": mock_user.email},
        expires_delta=timedelta(minutes=-1)  # Expired token
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token)
    assert exc_info.value.status_code == 401

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
    db = await get_test_db()
    mock_user = await get_mock_user(db)
    test_user = await create_temp_test_user()
    
    try:
        await test_create_access_token()
        await test_get_current_user()
        await test_invalid_token()
        await test_expired_token()
        await test_protected_route_access(mock_user)
        await test_websocket_auth()
        await test_token_refresh()
    finally:
        await cleanup_test_user(db, test_user)

if __name__ == "__main__":
    asyncio.run(test_main())
