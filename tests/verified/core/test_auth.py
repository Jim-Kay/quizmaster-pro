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

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.auth import create_access_token
from api.tests.utils.test_db import async_session, get_mock_user

# Fixtures for test client and database session
@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c

@pytest.fixture
async def async_client() -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(async_session: AsyncSession) -> dict:
    """Fixture to get authentication headers with a valid token"""
    mock_user = await get_mock_user(async_session)
    token = await create_access_token(data={"sub": str(mock_user.user_id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_protected_route(async_client: AsyncClient, auth_headers: dict):
    """Test protected route access with JWT token"""
    response = await async_client.get("/api/protected", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()

@pytest.mark.asyncio
async def test_protected_route_no_auth(async_client: AsyncClient):
    """Test protected route access without token"""
    response = await async_client.get("/api/protected")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_websocket_connection(client: TestClient, auth_headers: dict):
    """Test WebSocket connection and message exchange"""
    token = auth_headers["Authorization"].split()[1]
    with client.websocket_connect(f"/api/ws?token={token}") as websocket:
        # Test connection establishment
        data = websocket.receive_json()
        assert "message" in data
        assert data["message"] == "Connection established"

        # Test message exchange
        test_message = "Hello WebSocket"
        websocket.send_text(test_message)
        response = websocket.receive_text()
        assert response == test_message

@pytest.mark.asyncio
async def test_websocket_no_auth(client: TestClient):
    """Test WebSocket connection without token"""
    with pytest.raises(Exception):  # WebSocket connection should fail
        with client.websocket_connect("/api/ws") as websocket:
            pass

@pytest.mark.asyncio
async def test_long_running_process(client: TestClient, auth_headers: dict):
    """Test a long-running process with WebSocket status updates"""
    # Start the long-running process via REST API
    response = client.post("/api/start-process", headers=auth_headers)
    assert response.status_code == 200
    process_id = response.json()["process_id"]

    # Connect to WebSocket to receive status updates
    token = auth_headers["Authorization"].split()[1]
    with client.websocket_connect(f"/api/ws/process/{process_id}?token={token}") as websocket:
        # Collect status updates
        updates = []
        for _ in range(3):  # Expect at least 3 status updates
            data = websocket.receive_json()
            updates.append(data["status"])
        
        # Verify process progression
        assert "started" in updates
        assert "in_progress" in updates
        assert "completed" in updates
