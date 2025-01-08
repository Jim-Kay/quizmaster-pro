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
        - api/models.py
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

async def get_test_db():
    """Get test database session"""
    async for db in get_db():
        return db

async def get_mock_user(db):
    """Get the mock user for authentication tests"""
    query = select(User).where(User.user_id == UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b'))
    result = await db.execute(query)
    user = result.scalar_one()
    return user

async def create_test_user():
    """Create a test user for authentication tests"""
    test_user = User(
        user_id=UUID('a1b2c3d4-e5f6-4321-8765-9abcdef01234'),
        email='test_auth_user@quizmasterpro.test',
        name='Test Auth User',
        llm_provider='openai'
    )
    
    async for session in get_db():
        session.add(test_user)
        await session.commit()
        
    return test_user

async def cleanup_test_user(db, test_user):
    """Clean up test user after tests"""
    await db.delete(test_user)
    await db.commit()

async def test_create_access_token():
    """Test creating an access token"""
    test_user = await create_test_user()
    
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token can be decoded
    decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert decoded["sub"] == test_user.email

async def test_get_current_user():
    """Test getting current user from token"""
    test_user = await create_test_user()
    
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    current_user = await get_current_user(token)
    assert current_user is not None
    assert current_user.email == test_user.email

async def test_invalid_token():
    """Test invalid token handling"""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid_token")
    assert exc_info.value.status_code == 401

async def test_expired_token():
    """Test expired token handling"""
    test_user = await create_test_user()
    
    token = create_access_token(
        data={"sub": test_user.email},
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
    test_user = await create_test_user()
    
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
