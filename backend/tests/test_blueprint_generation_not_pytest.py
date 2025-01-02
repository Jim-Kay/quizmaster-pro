"""
Non-pytest version of the blueprint generation test.

NOTE: This test requires:
1. A running PostgreSQL database with the following configuration:
   - Database name: test_db (or as specified in TEST_DB_NAME env var)
   - Database user: postgres (or as specified in POSTGRES_USER env var)
   - Database password: postgres (or as specified in POSTGRES_PASSWORD env var)
   - Database host: localhost (or as specified in POSTGRES_HOST env var)
   - Database port: 5432 (or as specified in POSTGRES_PORT env var)
2. The backend API server running at http://localhost:8000

The test will:
1. Create a test topic
2. Initiate blueprint generation
3. Poll the status until completion
4. Verify the generated blueprint

Before running this test:
1. Ensure PostgreSQL is running
2. Create a test database: createdb test_db
3. Set up environment variables in .env file if using non-default values
4. Make sure the backend API server is running at http://localhost:8000
"""

import os
import sys
import logging
import jwt
import httpx
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from api.database import async_session_maker
import asyncio
from api.auth import MOCK_USER_ID  # Import the mock user ID

# Use the same secret as the auth module
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")

# Configure logging
logs_dir = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs')
os.makedirs(logs_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_dir, f'blueprint_generation_test_{timestamp}.log')

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

# Configuration
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 300  # seconds (5 minutes)
API_BASE_URL = "http://localhost:8000"

def create_test_token():
    """Create a test JWT token."""
    payload = {
        "sub": str(MOCK_USER_ID),  # Use the same mock user ID as the auth module
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "role": "admin"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

async def cleanup_database():
    """Clean up test data from the database."""
    logger.info("Starting database cleanup")
    async with async_session_maker() as session:
        try:
            # Delete test topics and their associated blueprints
            await session.execute(
                text("""DELETE FROM enabling_objectives 
                    WHERE terminal_objective_id IN (
                        SELECT terminal_objective_id FROM terminal_objectives 
                        WHERE blueprint_id IN (
                            SELECT blueprint_id FROM blueprints 
                            WHERE topic_id IN (
                                SELECT topic_id FROM topics 
                                WHERE title LIKE 'Test Topic%'
                            )
                        )
                    )""")
            )
            await session.execute(
                text("""DELETE FROM terminal_objectives 
                    WHERE blueprint_id IN (
                        SELECT blueprint_id FROM blueprints 
                        WHERE topic_id IN (
                            SELECT topic_id FROM topics 
                            WHERE title LIKE 'Test Topic%'
                        )
                    )""")
            )
            await session.execute(
                text("""DELETE FROM blueprints 
                    WHERE topic_id IN (
                        SELECT topic_id FROM topics 
                        WHERE title LIKE 'Test Topic%'
                    )""")
            )
            await session.execute(
                text("DELETE FROM topics WHERE title LIKE 'Test Topic%'")
            )
            await session.commit()
            logger.info("Database cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during database cleanup: {str(e)}")
            await session.rollback()
            raise

async def run_test():
    """Run the blueprint generation test."""
    topic_title = "Test Topic - Next.JS for Beginners"
    topic_description = "A comprehensive guide to learning Next.JS"
    
    auth_token = create_test_token()
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    
    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
            # Test 1: Clean up any existing test data
            logger.info("Test 1: Cleaning up test data")
            await cleanup_database()
            
            # Test 2: Create a test topic
            logger.info(f"Test 2: Creating test topic: {topic_title}")
            try:
                topic_response = await client.post(
                    "/api/topics",
                    json={"title": topic_title, "description": topic_description},
                    headers=headers,
                    timeout=30.0
                )
                
                if topic_response.status_code != 201:
                    logger.error(f"Failed to create topic. Status: {topic_response.status_code}")
                    logger.error(f"Response: {topic_response.text}")
                    return False
                    
                topic_id = topic_response.json()["topic_id"]
                logger.info(f"Created topic with ID: {topic_id}")
            except httpx.TimeoutException:
                logger.error("Timeout while creating topic")
                return False
            except Exception as e:
                logger.error(f"Error creating topic: {str(e)}")
                return False
            
            # Test 3: Start blueprint generation
            logger.info("Test 3: Starting blueprint generation")
            try:
                response = await client.post(
                    f"/api/topics/{topic_id}/blueprints/generate",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to start blueprint generation. Status: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False
                    
                blueprint_id = response.json()["blueprint_id"]
                logger.info(f"Blueprint generation started with ID: {blueprint_id}")
            except httpx.TimeoutException:
                logger.error("Timeout while starting blueprint generation")
                return False
            except Exception as e:
                logger.error(f"Error starting blueprint generation: {str(e)}")
                return False
            
            # Test 4: Check initial status
            logger.info("Test 4: Checking initial blueprint status")
            try:
                status_response = await client.get(
                    f"/api/blueprints/{blueprint_id}/status",
                    headers=headers,
                    timeout=30.0
                )
                
                if status_response.status_code != 200:
                    logger.error(f"Failed to get initial status. Status: {status_response.status_code}")
                    logger.error(f"Response: {status_response.text}")
                    return False
                    
                initial_status = status_response.json()
                if initial_status["status"] not in ["generating", "completed"]:
                    logger.error(f"Unexpected initial status: {initial_status['status']}")
                    return False
                    
                logger.info("Initial status check passed")
            except httpx.TimeoutException:
                logger.error("Timeout while checking initial status")
                return False
            except Exception as e:
                logger.error(f"Error checking initial status: {str(e)}")
                return False
            
            # Test 5: Poll status until completion
            logger.info("Test 5: Polling blueprint status until completion")
            max_retries = MAX_POLL_TIME // POLL_INTERVAL
            retry_count = 0
            final_status = None
            
            while retry_count < max_retries:
                try:
                    status_response = await client.get(
                        f"/api/blueprints/{blueprint_id}/status",
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if status_response.status_code != 200:
                        logger.error(f"Failed to get status update. Status: {status_response.status_code}")
                        logger.error(f"Response: {status_response.text}")
                        return False
                        
                    status_data = status_response.json()
                    logger.info(f"Current status: {status_data['status']}")
                    
                    if status_data["status"] == "completed":
                        logger.info("Blueprint generation completed successfully")
                        final_status = status_data
                        break
                    elif status_data["status"] == "error":
                        logger.error(f"Blueprint generation failed: {status_data.get('description')}")
                        logger.error(f"Error details: {status_data.get('error_details')}")
                        return False
                    
                    await asyncio.sleep(POLL_INTERVAL)
                    retry_count += 1
                except httpx.TimeoutException:
                    logger.error("Timeout while polling status")
                    return False
                except Exception as e:
                    logger.error(f"Error polling status: {str(e)}")
                    return False
            
            if retry_count >= max_retries:
                logger.error("Blueprint generation timed out")
                return False
            
            # Test 6: Verify the generated blueprint
            logger.info("Test 6: Verifying generated blueprint")
            if not final_status:
                logger.error("No final status available for verification")
                return False
                
            # Verify status
            if final_status["status"] != "completed":
                logger.error(f"Final status is not 'completed': {final_status['status']}")
                return False
                
            # Verify title
            if final_status["title"] != topic_title:
                logger.error(f"Title mismatch. Expected: {topic_title}, Got: {final_status['title']}")
                return False
                
            # Verify objectives
            if final_status["terminal_objectives_count"] <= 0:
                logger.error("No terminal objectives generated")
                return False
                
            if final_status["enabling_objectives_count"] <= 0:
                logger.error("No enabling objectives generated")
                return False
            
            logger.info("All verifications passed successfully")
            logger.info(f"Terminal objectives count: {final_status['terminal_objectives_count']}")
            logger.info(f"Enabling objectives count: {final_status['enabling_objectives_count']}")
            
            # Test 7: Clean up test data
            logger.info("Test 7: Final cleanup")
            await cleanup_database()
            
            return True
            
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
