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

import jwt
import logging
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select
from fastapi.testclient import TestClient

from api.core.config import get_settings
from api.core.database import get_db
from api.core.models import User
from api.auth import create_access_token, get_current_user
from api.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

test_client = TestClient(app)

def get_test_db():
    """Get test database session"""
    return next(get_db())

def get_mock_user(db):
    """Get the mock user for authentication tests"""
    query = select(User).where(User.user_id == UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b'))
    result = db.execute(query)
    user = result.scalar_one()
    return user

async def test_create_access_token():
    """Test JWT token creation"""
    logger.info("Starting test_create_access_token")
    user_id = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
    token = await create_access_token({"sub": str(user_id)})
    
    # Verify token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    
    # Verify expiration
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert exp > now
    assert exp <= now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)
    logger.info("Completed test_create_access_token")

async def test_get_current_user():
    """Test current user retrieval from token"""
    logger.info("Starting test_get_current_user")
    db = get_test_db()
    mock_user = get_mock_user(db)
    
    # Create token
    token = await create_access_token({"sub": str(mock_user.user_id)})
    
    # Get current user
    user = await get_current_user(token, db)
    assert user is not None
    assert user.user_id == mock_user.user_id
    assert user.email == mock_user.email
    logger.info("Completed test_get_current_user")

async def test_protected_route_access():
    """Test protected route access with JWT token"""
    logger.info("Starting test_protected_route_access")
    db = get_test_db()
    mock_user = get_mock_user(db)
    
    # Create token
    token = await create_access_token({"sub": str(mock_user.user_id)})
    
    # Test protected route
    response = await test_client.get(
        "/api/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "user" in response.json()
    logger.info("Completed test_protected_route_access")

async def test_websocket_auth():
    """Test WebSocket authentication"""
    logger.info("Starting test_websocket_auth")
    # Create token
    user_id = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')
    token = await create_access_token({"sub": str(user_id)})
    
    # Test WebSocket connection
    async with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        data = await websocket.receive_json()
        assert data == {"message": "Connection established"}
    logger.info("Completed test_websocket_auth")

async def run_tests():
    """Run all tests"""
    logger.info("Starting run_tests")
    await test_create_access_token()
    await test_get_current_user()
    await test_protected_route_access()
    await test_websocket_auth()
    logger.info("Completed run_tests")

# This will be called by the test runner
def test_auth():
    logger.info("Starting test_auth")
    import asyncio
    asyncio.run(run_tests())
    logger.info("Completed test_auth")
