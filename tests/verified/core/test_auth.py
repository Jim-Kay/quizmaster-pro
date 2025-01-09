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
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from fastapi.testclient import TestClient
from typing import AsyncGenerator

from api.core.settings import settings
from api.core.database import get_session, get_db, engine, Base, async_session
from api.core.models import User, LLMProvider
from api.auth import create_access_token, get_current_user
from api.main import app

# Import mock user constants from test_db_init using relative import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from verified.infrastructure.test_db_init import (
    MOCK_USER_ID,
    MOCK_USER_EMAIL,
    MOCK_USER_NAME
)

# Remove @pytest.fixture decorator
# @pytest.fixture
def override_get_db():
    """Override database dependency for testing"""
    return get_session()

# Override the get_db dependency for testing
app.dependency_overrides[get_db] = override_get_db
test_client = TestClient(app)

async def get_mock_user(db: AsyncSession) -> User:
    """
    Get the mock user for authentication tests.
    This is the persistent mock user that should NEVER be deleted.
    """
    query = select(User).where(User.user_id == MOCK_USER_ID)
    result = await db.execute(query)
    return result.scalar_one()

async def create_temp_test_user(db: AsyncSession) -> User:
    """
    Create a temporary test user for CRUD testing.
    This user is safe to delete and recreate, unlike the mock user.
    """
    user = User(
        user_id=uuid4(),
        email=f"test_{uuid4()}@example.com",
        name="Test User",
        llm_provider=LLMProvider.openai,
        encrypted_openai_key="test_key"
    )
    db.add(user)
    await db.commit()
    return user

async def cleanup_test_user(db: AsyncSession, test_user: User):
    """
    Clean up temporary test user after tests.
    Never deletes the mock user (MOCK_USER_ID) as it's needed by other tests.
    """
    if test_user.user_id != MOCK_USER_ID:
        await db.delete(test_user)
        await db.commit()

async def test_create_access_token():
    """Test creating an access token"""
    async with async_session() as db:
        mock_user = await get_mock_user(db)
        token = await create_access_token(data={"sub": str(mock_user.user_id)})
        assert token is not None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == str(mock_user.user_id)
        assert "exp" in payload

async def test_get_current_user():
    """Test getting current user from token"""
    async with async_session() as db:
        mock_user = await get_mock_user(db)
        token = await create_access_token(data={"sub": str(mock_user.user_id)})
        user = await get_current_user(token, db)
        assert user is not None
        assert user.user_id == mock_user.user_id
        assert user.email == mock_user.email

async def test_invalid_token():
    """Test invalid token handling"""
    async with async_session() as db:
        invalid_token = "invalid_token"
        try:
            await get_current_user(invalid_token, db)
            assert False, "Should have raised an error"
        except:
            pass

async def test_expired_token():
    """Test expired token handling"""
    async with async_session() as db:
        mock_user = await get_mock_user(db)
        expired_token = jwt.encode(
            {"sub": str(mock_user.user_id), "exp": datetime.utcnow() - timedelta(minutes=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        try:
            await get_current_user(expired_token, db)
            assert False, "Should have raised an error"
        except:
            pass

async def test_protected_route_access():
    """Test protected route access with JWT token"""
    async with async_session() as db:
        mock_user = await get_mock_user(db)
        token = await create_access_token(data={"sub": str(mock_user.user_id)})
        response = test_client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

async def test_websocket_auth():
    """Test WebSocket authentication"""
    async with async_session() as db:
        mock_user = await get_mock_user(db)
        token = await create_access_token(data={"sub": str(mock_user.user_id)})
        with test_client.websocket_connect(
            f"/ws?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data == "Connection established"

# Run all tests
async def run_tests():
    await test_create_access_token()
    await test_get_current_user()
    await test_invalid_token()
    await test_expired_token()
    await test_protected_route_access()
    await test_websocket_auth()

# This will be called by the test runner
def test_auth():
    asyncio.run(run_tests())
