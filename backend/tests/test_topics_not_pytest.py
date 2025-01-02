"""
Non-pytest version of the topics API tests.
This script tests the HTTP API endpoints for topics by:
1. Getting topics (empty list initially)
2. Creating a topic
3. Getting topics (should include created topic)
4. Updating a topic
5. Deleting a topic
"""

import os
import sys
import logging
import jwt
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.auth import MOCK_USER_ID  # Import the mock user ID
import os

# Use the same secret as the auth module
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")

# Import database models and session
from api.database import get_db, Base, engine, async_session_maker, sync_engine
from api.models import Topic, Blueprint, EnablingObjective, TerminalObjective
from sqlalchemy.future import select
from sqlalchemy import delete

# Configure logging
logs_dir = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs')
os.makedirs(logs_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_dir, f'topics_test_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(filename)s-%(module)s:%(lineno)d - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# API URL for testing
API_URL = os.getenv("API_URL", "http://localhost:8000")

def create_test_token():
    """Create a test JWT token."""
    payload = {
        "sub": str(MOCK_USER_ID),  # Use the same mock user ID as the auth module
        "exp": datetime.utcnow() + timedelta(days=1),
        "role": "admin"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def cleanup_database():
    """Clean up test topics from the database before running tests."""
    try:
        async with async_session_maker() as session:
            # Find test topics
            stmt = select(Topic.topic_id).where(Topic.title.like('Test Topic%'))
            result = await session.execute(stmt)
            topic_ids = result.scalars().all()
            
            if topic_ids:
                # Find blueprints for these topics
                stmt = select(Blueprint.blueprint_id).where(Blueprint.topic_id.in_(topic_ids))
                result = await session.execute(stmt)
                blueprint_ids = result.scalars().all()
                
                if blueprint_ids:
                    # Delete enabling objectives
                    stmt = delete(EnablingObjective).where(EnablingObjective.terminal_objective_id.in_(
                        select(TerminalObjective.terminal_objective_id).where(TerminalObjective.blueprint_id.in_(blueprint_ids))
                    ))
                    await session.execute(stmt)
                    
                    # Delete terminal objectives
                    stmt = delete(TerminalObjective).where(TerminalObjective.blueprint_id.in_(blueprint_ids))
                    await session.execute(stmt)
                    
                    # Delete blueprints
                    stmt = delete(Blueprint).where(Blueprint.blueprint_id.in_(blueprint_ids))
                    await session.execute(stmt)
                
                # Delete topics
                stmt = delete(Topic).where(Topic.topic_id.in_(topic_ids))
                await session.execute(stmt)
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error cleaning up test topics: {str(e)}")
        raise

async def run_test():
    """Run the topics API tests."""
    try:
        # Clean up any existing test data
        await cleanup_database()
        
        # Create test client with the correct user ID
        async with AsyncClient(transport=ASGITransport(app=app), base_url=API_URL) as client:
            # Set up authentication token with the correct user ID
            token = create_test_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test 1: Get topics (should be empty)
            response = await client.get("/api/topics", headers=headers)
            assert response.status_code == 200
            topics = response.json()
            assert isinstance(topics, list)
            initial_count = len(topics)
            
            # Test 2: Create a topic
            topic_data = {
                "title": "Test Topic",
                "description": "Test Description"
            }
            response = await client.post("/api/topics", json=topic_data, headers=headers)
            assert response.status_code == 201
            created_topic = response.json()
            topic_id = created_topic["topic_id"]
            
            # Test 3: Get topics (should include new topic)
            response = await client.get("/api/topics", headers=headers)
            assert response.status_code == 200
            topics = response.json()
            assert len(topics) == initial_count + 1
            
            # Test 4: Get specific topic
            response = await client.get(f"/api/topics/{topic_id}", headers=headers)
            assert response.status_code == 200
            topic = response.json()
            assert topic["title"] == "Test Topic"
            
            # Test 5: Update topic
            update_data = {
                "title": "Updated Test Topic",
                "description": "Updated Test Description"
            }
            response = await client.put(f"/api/topics/{topic_id}", json=update_data, headers=headers)
            assert response.status_code == 200
            updated_topic = response.json()
            assert updated_topic["title"] == "Updated Test Topic"
            
            # Test 6: Delete topic
            response = await client.delete(f"/api/topics/{topic_id}", headers=headers)
            assert response.status_code == 204
            
            # Test 7: Verify topic is deleted
            response = await client.get(f"/api/topics/{topic_id}", headers=headers)
            assert response.status_code == 404
            
            return True
            
    except AssertionError as e:
        logger.error(f"Test assertion failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        return False

async def main():
    """Main entry point."""
    # Set up UTF-8 encoding for Windows console
    if sys.platform.startswith('win'):
        import locale
        if locale.getpreferredencoding().upper() != 'UTF-8':
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            
    success = await run_test()
    if success:
        logger.info("Test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
