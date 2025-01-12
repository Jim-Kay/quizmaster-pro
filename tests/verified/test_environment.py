"""Tests for the environment endpoint."""
import os
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from api.main import create_app
from api.core.config import get_settings

@pytest.mark.asyncio
async def test_environment_endpoint():
    """Test that the environment endpoint returns correct database name."""
    # Ensure we're in test environment
    os.environ["QUIZMASTER_ENVIRONMENT"] = "test"
    # Clear settings cache to pick up environment change
    get_settings.cache_clear()
    
    # Create a fresh app instance
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/environment")
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Check environment info
        assert data["environment"] == "test"
        assert data["color"] is not None
        assert data["description"] is not None
        
        # Check database name
        assert data["database_name"] == "quizmaster_test"

@pytest.mark.asyncio
async def test_environment_endpoint_development():
    """Test that the environment endpoint returns correct database name in development."""
    # Switch to development environment
    os.environ["QUIZMASTER_ENVIRONMENT"] = "development"
    # Clear settings cache to pick up environment change
    get_settings.cache_clear()
    
    # Create a fresh app instance
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/environment")
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Check environment info
        assert data["environment"] == "development"
        assert data["color"] is not None
        assert data["description"] is not None
        
        # Check database name
        assert data["database_name"] == "quizmaster_dev"
