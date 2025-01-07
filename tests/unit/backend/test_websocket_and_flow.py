"""
Test Name: test_websocket_and_flow
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

import asyncio
import websockets
import jwt
import json
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import uuid4, UUID
from urllib.parse import quote

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock user configuration
MOCK_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
NEXTAUTH_SECRET = "development-secret"

# HTTP client configuration
HTTP_TIMEOUT = httpx.Timeout(
    timeout=30.0,  # Default timeout for all operations
    connect=10.0,  # Timeout for connecting to the server
    read=30.0,     # Timeout for reading the response
    write=10.0     # Timeout for writing the request
)

def generate_auth_token() -> str:
    """Generate a mock authentication token."""
    payload = {
        "sub": str(MOCK_USER_ID),  # User ID must be a string
        "iat": int(datetime(2025, 1, 6, 20, 26, 24).timestamp()),  # Use the provided time
        "jti": str(uuid4()),  # Unique token ID
        "exp": int((datetime(2025, 1, 6, 20, 26, 24) + timedelta(days=30)).timestamp()),  # Add expiry
        "name": "Test User",  # Optional user info
        "email": "test@example.com"  # Optional user info
    }
    return jwt.encode(payload, NEXTAUTH_SECRET, algorithm="HS256")

async def test_websocket_connection(token_format: str, execution_id: str) -> None:
    """Test WebSocket connection with different token formats."""
    base_token = generate_auth_token()
    
    if token_format == "basic":
        token = base_token
    elif token_format == "bearer":
        token = f"Bearer%20{base_token}"  # URL encode the space
    elif token_format == "encoded":
        token = quote(base_token)
    elif token_format == "encoded_bearer":
        token = quote(f"Bearer {base_token}")
    else:
        raise ValueError(f"Invalid token format: {token_format}")
    
    logger.info(f"\nTesting {token_format} token:")
    url = f"ws://localhost:8000/api/flows/executions/{execution_id}/logs/ws?token={token}"
    logger.info(f"Connecting to: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            logger.info(f"WebSocket connected successfully with {token_format} token!")
            message = await websocket.recv()
            logger.info(f"Received message: {message}")
            await websocket.close()
    except Exception as e:
        logger.error(f"Error testing {token_format} token: {str(e)}")
        raise

async def create_flow_execution(flow_name: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new flow execution."""
    auth_token = generate_auth_token()
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    create_payload = {
        "flow_name": flow_name,
        "initial_state": initial_state
    }
    
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            "http://localhost:8000/api/flows/executions",
            json=create_payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def main():
    """Run the combined WebSocket and flow execution test."""
    try:
        # First create a flow execution
        logger.info("Creating test flow execution...")
        flow_execution = await create_flow_execution(
            "test",
            {
                "topic_title": "Test Topic",
                "topic_description": "A test topic about testing flows",
                "sentence_count": 3
            }
        )
        execution_id = flow_execution["id"]
        logger.info(f"Flow execution created with ID: {execution_id}")
        
        # Then test WebSocket connections with different token formats
        token_formats = ["basic", "bearer", "encoded", "encoded_bearer"]
        for token_format in token_formats:
            await test_websocket_connection(token_format, execution_id)
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
