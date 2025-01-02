import pytest
from httpx import AsyncClient
import uuid
import logging
from api.main import app
from api.auth import MOCK_USER_ID
import jwt
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio(loop_scope="session")

# Create a proper JWT token for testing
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")
mock_token = jwt.encode({"sub": str(MOCK_USER_ID)}, JWT_SECRET, algorithm="HS256")
headers = {
    "Authorization": f"Bearer {mock_token}",
    "Content-Type": "application/json"
}

async def test_blueprint_counts(test_session, test_user, client):
    """Test getting blueprint counts for topics."""
    # First create a test topic
    topic_data = {
        "title": "Test Topic",
        "description": "Test Description"
    }
    create_response = await client.post("/api/topics", json=topic_data, headers=headers)
    assert create_response.status_code == 201
    topic = create_response.json()
    
    # Get the blueprint count for this topic
    count_response = await client.get(f"/api/topics/{topic['id']}/blueprints/count", headers=headers)
    assert count_response.status_code == 200
    count_data = count_response.json()
    assert "count" in count_data
    assert isinstance(count_data["count"], int)
    assert count_data["count"] == 0  # Should be 0 as we haven't created any blueprints

    # Get all topics and their blueprint counts
    topics_response = await client.get("/api/topics", headers=headers)
    assert topics_response.status_code == 200
    topics = topics_response.json()
    
    # Verify we can get counts for all topics
    for topic in topics:
        count_response = await client.get(
            f"/api/topics/{topic['id']}/blueprints/count",
            headers=headers
        )
        assert count_response.status_code == 200
        count_data = count_response.json()
        assert "count" in count_data
        assert isinstance(count_data["count"], int)
        logger.info(f"Topic '{topic['title']}' has {count_data['count']} blueprints")
