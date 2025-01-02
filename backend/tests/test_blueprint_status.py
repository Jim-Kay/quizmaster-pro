"""
Test for the blueprint status endpoint.

This test will:
1. Verify that the topic and blueprint exist in the database
2. Try to access the blueprint status endpoint
3. Verify the response
"""

import os
import sys
import logging
import jwt
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from api.auth import MOCK_USER_ID
from uuid import UUID
from ..config import get_db_password

# Configuration
API_BASE_URL = "http://localhost:8000"
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")

# Database configuration
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = get_db_password()
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "quizmaster")

QUIZ_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configure logging
logs_dir = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs')
os.makedirs(logs_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_dir, f'blueprint_status_test_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(filename)s-%(module)s:%(lineno)d - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_test_token():
    """Create a test JWT token."""
    now = datetime.now(timezone.utc)
    token_data = {
        "sub": str(MOCK_USER_ID),  # Convert UUID to string
        "email": "test@example.com",
        "name": "Test User",
        "iat": now,
        "exp": now + timedelta(hours=1)
    }
    return jwt.encode(token_data, JWT_SECRET, algorithm="HS256")

async def verify_records_exist(topic_id: str, blueprint_id: str) -> bool:
    """Verify that the topic and blueprint exist in the database."""
    engine = create_async_engine(QUIZ_DB_URL)
    async with AsyncSession(engine) as session:
        try:
            # Convert string IDs to UUIDs for database query
            topic_uuid = UUID(topic_id)
            blueprint_uuid = UUID(blueprint_id)
            
            # List all topics first
            logger.info("\nChecking topics in quizmaster database:")
            topics_result = await session.execute(text("SELECT topic_id, title FROM topics"))
            topics = topics_result.fetchall()
            for t in topics:
                logger.info(f"Found topic: {t[0]} - {t[1]}")
            
            # List all blueprints
            logger.info("\nChecking blueprints in quizmaster database:")
            blueprints_result = await session.execute(
                text("SELECT blueprint_id, topic_id, status FROM blueprints")
            )
            blueprints = blueprints_result.fetchall()
            for b in blueprints:
                logger.info(f"Found blueprint: {b[0]} for topic {b[1]} (status: {b[2]})")
            
            # Check if our specific topic exists
            topic_result = await session.execute(
                text("SELECT COUNT(*) FROM topics WHERE topic_id = :topic_id"),
                {"topic_id": topic_uuid}
            )
            topic_count = topic_result.scalar()
            
            if topic_count == 0:
                logger.error(f"Topic {topic_id} not found in database")
                return False
                
            # Check if blueprint exists
            blueprint_result = await session.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM blueprints 
                    WHERE blueprint_id = :blueprint_id 
                    AND topic_id = :topic_id
                """),
                {"blueprint_id": blueprint_uuid, "topic_id": topic_uuid}
            )
            blueprint_count = blueprint_result.scalar()
            
            if blueprint_count == 0:
                logger.error(f"Blueprint {blueprint_id} not found in database")
                return False
            
            logger.info(f"Found topic {topic_id} and blueprint {blueprint_id} in database")
            return True
            
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return False
        finally:
            await engine.dispose()

async def test_blueprint_status():
    """Test the blueprint status endpoint."""
    # Test data - using existing IDs from the database
    topic_id = "d9909b07-b0f1-4c01-ae7d-8e0c6b7c2f89"  # Next.js for someone who only knows HTML
    blueprint_id = "af091360-df1e-45a7-aa46-fc52ce887f46"  # Completed blueprint
    
    try:
        # Step 1: Verify records exist
        logger.info("Step 1: Verifying records exist in database")
        records_exist = await verify_records_exist(topic_id, blueprint_id)
        if not records_exist:
            logger.error("Required records not found in database")
            return False
        
        # Step 2: Test the status endpoint
        logger.info("Step 2: Testing blueprint status endpoint")
        auth_token = create_test_token()
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
            url = f"/api/topics/{topic_id}/blueprints/{blueprint_id}/status"  
            logger.info(f"Making request to: {url}")
            logger.info(f"Headers: {headers}")
            
            response = await client.get(
                url,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ Blueprint status endpoint test passed")
                return True
            else:
                logger.error(f"❌ Blueprint status endpoint test failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return False

async def main():
    """Main entry point."""
    try:
        success = await test_blueprint_status()
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
