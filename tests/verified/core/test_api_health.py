"""
Test Name: API Health and Core Functionality Test
Description: Tests the core API functionality including health checks, rate limiting, and error handling.

Test Metadata:
    Level: 1
    Dependencies: [
        "c:/ParseThat/QuizMasterPro/tests/verified/infrastructure/test_backend_health.py",
        "c:/ParseThat/QuizMasterPro/tests/verified/infrastructure/test_db_init.py"
    ]
    Blocking: True
    Parallel_Safe: True
    Estimated_Duration: 10
    Working_Directory: backend
    Required_Paths:
        - api/main.py
        - api/routers/
        - api/core/config.py
        - api/core/database.py

Environment:
    - Conda Environment: crewai-quizmaster-pro
    - Required Services:
        - PostgreSQL Database
        - Backend API Server

Setup:
    1. Ensure PostgreSQL is running
    2. Ensure backend server is running
    3. Set environment variables:
        - TEST_MODE=true
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_HOST
        - POSTGRES_PORT

Execution:
    pytest tests/verified/core/test_api_health.py -v

Expected Results:
    - All API endpoints respond with correct status codes
    - Rate limiting functions as expected
    - Error responses follow standard format
    - API version information is correct

Notes:
    This test ensures core API functionality is working correctly.
    It must pass before running any higher-level feature tests.
"""

import os
import pytest
import logging
import httpx
from typing import AsyncGenerator
from fastapi import status
from dotenv import load_dotenv
import asyncio

# Import from backend package
from api.core.config import get_settings
from api.core.database import get_db, engine
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables and settings
load_dotenv()
settings = get_settings()

# Server configuration
API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

MOCK_USER_EMAIL = "test@example.com"
MOCK_USER_PASSWORD = "testpassword123"

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests"""
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.mark.asyncio
async def test_api_root():
    """Test API root endpoint"""
    logger.info("Testing API root endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to QuizMaster Pro API"

@pytest.mark.asyncio
async def test_api_health():
    """Test API health endpoint"""
    logger.info("Testing API health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_api_error_handling():
    """Test API error handling"""
    logger.info("Testing API error handling...")
    async with httpx.AsyncClient() as client:
        # Test 404 Not Found
        response = await client.get(f"{API_BASE_URL}/api/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

        # Test 405 Method Not Allowed
        response = await client.post(f"{API_BASE_URL}/api/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

@pytest.mark.asyncio
async def test_api_rate_limiting():
    """Test API rate limiting"""
    logger.info("Testing API rate limiting...")
    async with httpx.AsyncClient() as client:
        # Make multiple rapid requests to auth endpoint
        responses = []
        for _ in range(100):  # Increased to trigger rate limit
            response = await client.post(
                f"{API_BASE_URL}/api/token",
                data={
                    "username": MOCK_USER_EMAIL,
                    "password": MOCK_USER_PASSWORD
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            responses.append(response)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
            await asyncio.sleep(0.01)  # Small delay between requests
        
        # Check if rate limiting is working
        assert any(r.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                  for r in responses), "Rate limiting not detected"

        # Get a non-rate-limited response to check headers
        response = await client.get(f"{API_BASE_URL}/api/health")
        headers = response.headers
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers
