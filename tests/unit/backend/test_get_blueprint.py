"""
Test Name: test_get_blueprint
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

async def test_get_blueprint(test_session, test_user, client):
    """Test getting a single blueprint with objective counts."""
    # First create a test topic
    topic_data = {
        "title": "Test Topic",
        "description": "Test Description"
    }
    create_topic_response = await client.post("/api/topics", json=topic_data, headers=headers)
    assert create_topic_response.status_code == 201
    topic = create_topic_response.json()
    
    # Create a test blueprint with objectives
    blueprint_data = {
        "title": "Test Blueprint",
        "description": "Test Blueprint Description",
        "objectives": [
            {
                "title": "Terminal Objective 1",
                "description": "First terminal objective",
                "type": "terminal"
            },
            {
                "title": "Enabling Objective 1",
                "description": "First enabling objective",
                "type": "enabling"
            },
            {
                "title": "Enabling Objective 2",
                "description": "Second enabling objective",
                "type": "enabling"
            }
        ]
    }
    
    create_blueprint_response = await client.post(
        f"/api/topics/{topic['id']}/blueprints",
        json=blueprint_data,
        headers=headers
    )
    assert create_blueprint_response.status_code == 201
    created_blueprint = create_blueprint_response.json()
    
    # Get the single blueprint
    get_blueprint_response = await client.get(
        f"/api/topics/{topic['id']}/blueprints/{created_blueprint['id']}",
        headers=headers
    )
    assert get_blueprint_response.status_code == 200
    blueprint = get_blueprint_response.json()
    
    # Verify the blueprint data
    assert blueprint["id"] == created_blueprint["id"]
    assert blueprint["title"] == blueprint_data["title"]
    assert blueprint["description"] == blueprint_data["description"]
    assert blueprint["topic_id"] == topic["id"]
    assert blueprint["created_by"] == str(MOCK_USER_ID)
    assert "created_at" in blueprint
    assert "updated_at" in blueprint
    
    # Verify objective counts
    assert blueprint["terminal_objectives_count"] == 1
    assert blueprint["enabling_objectives_count"] == 2
    
    # Test getting a non-existent blueprint
    non_existent_id = str(uuid.uuid4())
    error_response = await client.get(
        f"/api/topics/{topic['id']}/blueprints/{non_existent_id}",
        headers=headers
    )
    assert error_response.status_code == 404
    
    # Test getting a blueprint with a non-existent topic
    non_existent_topic_id = str(uuid.uuid4())
    error_response = await client.get(
        f"/api/topics/{non_existent_topic_id}/blueprints/{created_blueprint['id']}",
        headers=headers
    )
    assert error_response.status_code == 404
