"""
Test Name: Topics API Test Suite
Description: Tests the core functionality of the Topics API endpoints including CRUD operations

Test Metadata:
    Level: 1
    Dependencies: None
    Blocking: True
    Parallel_Safe: False
    Estimated_Duration: 10
    Working_Directory: tests/verified/core
    Required_Paths: 
        - api/core/models.py
        - api/database.py
        - api/auth.py

Environment:
    - Conda Environment: quiz_master_backend
    - Required Services: 
        - PostgreSQL
        - Backend API Server

Setup:
    1. Ensure PostgreSQL is running
    2. Ensure test database exists
    3. Set QUIZMASTER_ENVIRONMENT=test
    4. Set NEXTAUTH_SECRET for JWT signing

Execution:
    pytest test_topics_api.py -v

Expected Results:
    All tests should pass with proper cleanup of test data
"""

import os
import pytest
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator, Dict

# Import application components
from api.main import app
from api.auth import MOCK_USER_ID
from api.database import async_session_maker
from api.core.models import Topic, Blueprint, TerminalObjective, EnablingObjective
from sqlalchemy import select, delete

# Test configuration
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")
API_URL = os.getenv("API_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_token() -> str:
    """Create a test JWT token for authentication."""
    payload = {
        "sub": str(MOCK_USER_ID),
        "exp": datetime.utcnow() + timedelta(days=1),
        "role": "admin"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@pytest.fixture(scope="module")
async def auth_headers(test_token: str) -> Dict[str, str]:
    """Create authorization headers with test token."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
async def test_client():
    """Create a test client for making API requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=API_URL) as client:
        yield client

@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Clean up test data before and after each test."""
    await _cleanup_database()
    yield
    await _cleanup_database()

async def _cleanup_database():
    """Remove all test topics and related data."""
    async with async_session_maker() as session:
        try:
            # Find test topics
            stmt = select(Topic.topic_id).where(Topic.title.like('Test Topic%'))
            result = await session.execute(stmt)
            topic_ids = result.scalars().all()
            
            if topic_ids:
                # Find and delete related data
                stmt = select(Blueprint.blueprint_id).where(Blueprint.topic_id.in_(topic_ids))
                result = await session.execute(stmt)
                blueprint_ids = result.scalars().all()
                
                if blueprint_ids:
                    # Delete enabling objectives
                    stmt = delete(EnablingObjective).where(EnablingObjective.terminal_objective_id.in_(
                        select(TerminalObjective.terminal_objective_id).where(
                            TerminalObjective.blueprint_id.in_(blueprint_ids)
                        )
                    ))
                    await session.execute(stmt)
                    
                    # Delete terminal objectives
                    stmt = delete(TerminalObjective).where(
                        TerminalObjective.blueprint_id.in_(blueprint_ids)
                    )
                    await session.execute(stmt)
                    
                    # Delete blueprints
                    stmt = delete(Blueprint).where(Blueprint.blueprint_id.in_(blueprint_ids))
                    await session.execute(stmt)
                
                # Delete topics
                stmt = delete(Topic).where(Topic.topic_id.in_(topic_ids))
                await session.execute(stmt)
            
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise

@pytest.mark.asyncio
async def test_get_topics_empty(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test getting topics when none exist."""
    response = await test_client.get("/api/topics", headers=auth_headers)
    assert response.status_code == 200
    topics = response.json()
    assert isinstance(topics, list)
    assert len(topics) == 0

@pytest.mark.asyncio
async def test_create_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test creating a new topic."""
    topic_data = {
        "title": "Test Topic",
        "description": "Test Description"
    }
    response = await test_client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 201
    created_topic = response.json()
    assert created_topic["title"] == topic_data["title"]
    assert created_topic["description"] == topic_data["description"]
    assert "topic_id" in created_topic

@pytest.mark.asyncio
async def test_get_specific_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test getting a specific topic by ID."""
    # First create a topic
    topic_data = {
        "title": "Test Topic",
        "description": "Test Description"
    }
    create_response = await test_client.post("/api/topics", json=topic_data, headers=auth_headers)
    created_topic = create_response.json()
    topic_id = created_topic["topic_id"]

    # Then get the specific topic
    response = await test_client.get(f"/api/topics/{topic_id}", headers=auth_headers)
    assert response.status_code == 200
    topic = response.json()
    assert topic["topic_id"] == topic_id
    assert topic["title"] == topic_data["title"]
    assert topic["description"] == topic_data["description"]

@pytest.mark.asyncio
async def test_update_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test updating an existing topic."""
    # First create a topic
    initial_data = {
        "title": "Test Topic",
        "description": "Test Description"
    }
    create_response = await test_client.post("/api/topics", json=initial_data, headers=auth_headers)
    created_topic = create_response.json()
    topic_id = created_topic["topic_id"]

    # Update the topic
    update_data = {
        "title": "Updated Test Topic",
        "description": "Updated Test Description"
    }
    response = await test_client.put(
        f"/api/topics/{topic_id}", 
        json=update_data, 
        headers=auth_headers
    )
    assert response.status_code == 200
    updated_topic = response.json()
    assert updated_topic["title"] == update_data["title"]
    assert updated_topic["description"] == update_data["description"]

@pytest.mark.asyncio
async def test_delete_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test deleting a topic."""
    # First create a topic
    topic_data = {
        "title": "Test Topic",
        "description": "Test Description"
    }
    create_response = await test_client.post("/api/topics", json=topic_data, headers=auth_headers)
    created_topic = create_response.json()
    topic_id = created_topic["topic_id"]

    # Delete the topic
    response = await test_client.delete(f"/api/topics/{topic_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify topic is deleted
    get_response = await test_client.get(f"/api/topics/{topic_id}", headers=auth_headers)
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_get_nonexistent_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test getting a topic that doesn't exist."""
    response = await test_client.get("/api/topics/999999", headers=auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_nonexistent_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test updating a topic that doesn't exist."""
    update_data = {
        "title": "Updated Test Topic",
        "description": "Updated Test Description"
    }
    response = await test_client.put(
        "/api/topics/999999", 
        json=update_data, 
        headers=auth_headers
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_nonexistent_topic(test_client: AsyncClient, auth_headers: Dict[str, str]):
    """Test deleting a topic that doesn't exist."""
    response = await test_client.delete("/api/topics/999999", headers=auth_headers)
    assert response.status_code == 404
