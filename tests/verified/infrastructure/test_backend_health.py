"""
Backend Server Health Test
Verifies that the backend server is running and responding to health checks.

Test Metadata:
    Level: 0
    Dependencies: []
    Blocking: True
    Parallel_Safe: True
    Estimated_Duration: 5
    Working_Directory: backend
    Required_Paths:
        - api/main.py
        - api/routers
        - api/core/config.py
"""

import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

# Import from backend package
from api.core.config import get_settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Server configuration
API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

async def test_server_running():
    """Test if the server is running and responding"""
    logger.info("Testing backend server health...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            
            logger.info("Backend server health check successful")
            return True
            
    except Exception as e:
        logger.error(f"Backend server health check failed: {e}")
        return False

async def test_main():
    """Main test function"""
    success = await test_server_running()
    assert success, "Backend server health check failed"

if __name__ == "__main__":
    asyncio.run(test_main())
