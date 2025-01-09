"""
Test Name: test_topics
Description: [TODO: Add test description]

Environment:
    - Conda Environment: quiz_master_backend
    - Working Directory: tests/unit/backend
    - Required Services: [TODO: List required services]

Setup:
    1. [TODO: Add setup steps]

Execution:
    [TODO: Add execution command]

Expected Results:
    [TODO: Add expected results]
"""

import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from api.main import app
from api.auth import MOCK_USER_ID  # Import the mock user ID

pytestmark = pytest.mark.asyncio(loop_scope="session")  # Set session scope for all async tests

# Mock authorization token
mock_token = "mock_token"
headers = {
    "Authorization": f"Bearer {mock_token}",
    "Content-Type": "application/json"
}

@pytest.fixture
async def client(test_session):
    """Create a test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as client:
        yield client

async def test_get_topics_empty(test_session, test_user, client):
    """Test getting topics when there are none."""
    response = await client.get("/api/topics", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

async def test_get_topics(test_session, test_user, client):
    """Test getting topics."""
    # Create a test topic
    topic_id = uuid.uuid4()
    create_response = await client.post(
        "/api/topics",
        json={
            "title": "Test Topic",
            "description": "Test Description"
        },
        headers=headers
    )
    assert create_response.status_code == 201

    # Get all topics
    response = await client.get("/api/topics", headers=headers)
    assert response.status_code == 200
    topics = response.json()
    assert len(topics) == 1
    assert topics[0]["title"] == "Test Topic"
    assert topics[0]["description"] == "Test Description"

async def test_create_topic(test_session, test_user, client):
    """Test creating a topic."""
    response = await client.post(
        "/api/topics",
        json={
            "title": "New Topic",
            "description": "New Description"
        },
        headers=headers
    )
    assert response.status_code == 201
    topic = response.json()
    assert topic["title"] == "New Topic"
    assert topic["description"] == "New Description"
    assert "id" in topic  # ID should be auto-generated
    assert "user_id" in topic  # Should match our mock user ID
    assert topic["user_id"] == str(MOCK_USER_ID)

async def test_update_topic(test_session, test_user, client):
    """Test updating a topic."""
    # Create a topic first
    create_response = await client.post(
        "/api/topics",
        json={
            "title": "Topic to Update",
            "description": "Will be updated"
        },
        headers=headers
    )
    assert create_response.status_code == 201
    topic = create_response.json()
    topic_id = topic["id"]

    # Update the topic
    update_response = await client.put(
        f"/api/topics/{topic_id}",
        json={
            "title": "Updated Topic",
            "description": "Updated Description"
        },
        headers=headers
    )
    assert update_response.status_code == 200
    updated_topic = update_response.json()
    assert updated_topic["id"] == topic_id
    assert updated_topic["title"] == "Updated Topic"
    assert updated_topic["description"] == "Updated Description"
    assert updated_topic["user_id"] == str(MOCK_USER_ID)

async def test_delete_topic(test_session, test_user, client):
    """Test deleting a topic."""
    # Create a topic first
    create_response = await client.post(
        "/api/topics",
        json={
            "title": "Topic to Delete",
            "description": "Will be deleted"
        },
        headers=headers
    )
    assert create_response.status_code == 201
    topic = create_response.json()
    topic_id = topic["id"]

    # Delete the topic
    delete_response = await client.delete(f"/api/topics/{topic_id}", headers=headers)
    assert delete_response.status_code == 204  # 204 No Content is the correct status code for successful DELETE

    # Verify it's deleted
    get_response = await client.get("/api/topics", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json() == []

async def test_unauthorized_access(test_session, client):
    """Test access without user ID."""
    response = await client.get("/api/topics")
    assert response.status_code == 403

async def test_unauthorized_access_with_invalid_token(test_session, client):
    """Test access with invalid token."""
    response = await client.get("/api/topics", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
