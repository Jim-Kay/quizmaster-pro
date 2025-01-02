import asyncio
import logging
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient
import pytest
from api.main import app
from api.config import JWT_SECRET

logger = logging.getLogger(__name__)

# Configuration
POLL_INTERVAL = 1  # seconds
MAX_POLL_TIME = 30  # seconds

def create_test_token():
    """Create a test JWT token."""
    payload = {
        "sub": "550e8400-e29b-41d4-a716-446655440000",  # Test user ID
        "exp": datetime.utcnow() + timedelta(days=1),
        "role": "admin"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@pytest.mark.asyncio
async def test_blueprint_generation():
    """Test blueprint generation endpoint and background task."""
    topic_title = "Next.JS for Beginners"
    topic_description = "A comprehensive guide to learning Next.JS"
    
    auth_token = create_test_token()
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a test topic
        topic_response = await client.post(
            "/api/topics/",
            json={"title": topic_title, "description": topic_description},
            headers=headers
        )
        assert topic_response.status_code == 201
        topic_id = topic_response.json()["id"]
        
        # Start blueprint generation
        response = await client.post(
            f"/api/topics/{topic_id}/blueprints/generate",
            headers=headers
        )
        assert response.status_code == 200
        blueprint_id = response.json()["blueprint_id"]
        
        logger.info(f"Starting blueprint generation for topic {topic_id}")
        
        # Check initial status
        status_response = await client.get(
            f"/api/blueprints/{blueprint_id}/status",
            headers=headers
        )
        assert status_response.status_code == 200
        initial_status = status_response.json()
        assert initial_status["status"] == "generating"
        
        # Poll status until completion or error
        max_retries = 30  # 30 seconds max wait time
        retry_count = 0
        while retry_count < max_retries:
            status_response = await client.get(
                f"/api/blueprints/{blueprint_id}/status",
                headers=headers
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                logger.info("Blueprint generation completed successfully")
                break
            elif status_data["status"] == "error":
                logger.error(f"Blueprint generation failed: {status_data.get('description')}")
                logger.error(f"Error details: {status_data.get('error_details')}")
                assert False, f"Blueprint generation failed: {status_data.get('description')}"
            
            await asyncio.sleep(POLL_INTERVAL)
            retry_count += 1
        
        if retry_count >= max_retries:
            logger.error("Blueprint generation timed out")
            assert False, "Blueprint generation did not complete within expected time"
        
        # Verify the generated blueprint
        final_status = status_response.json()
        assert final_status["status"] == "completed"
        assert final_status["title"] == topic_title
        assert final_status["terminal_objectives_count"] > 0
        assert final_status["enabling_objectives_count"] > 0
