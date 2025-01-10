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

Environment:
    - Conda Environment: crewai-quizmaster-pro
    - Required Services: None

Setup:
    1. Ensure backend server is running
    2. Environment variables are set

Execution:
    pytest tests/verified/infrastructure/test_backend_health.py -v

Expected Results:
    - Server responds with 200 status code
    - Health check returns {"status": "healthy"}

Notes:
    This test is part of Level 0 infrastructure tests and must pass
    before proceeding with higher-level tests.
"""

import os
import pytest
import logging
import httpx
from dotenv import load_dotenv

# Import from backend package
from api.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables and settings
load_dotenv()
settings = get_settings()

# Server configuration
API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

@pytest.mark.asyncio
async def test_server_health():
    """Test if the server is running and responding"""
    logger.info("Testing backend server health...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        logger.info("Backend server health check passed")
