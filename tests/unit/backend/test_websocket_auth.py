"""
Test Name: test_websocket_auth
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

"""
WebSocket Authentication Test

To run this test:
conda run -n crewai-quizmaster-pro python tests/test_websocket_auth.py

This ensures the test runs in the correct conda environment with all dependencies.
"""

import asyncio
import websockets
import jwt
import logging
import os
from uuid import UUID
from urllib.parse import quote

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
MOCK_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")  # Same as mock auth
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")
WS_URL = "ws://localhost:8000"

def generate_test_tokens():
    """Generate different variations of tokens for testing"""
    payload = {
        "sub": str(MOCK_USER_ID),
        "iat": 1736096644,  # Fixed timestamp for testing
    }
    
    # Basic token
    basic_token = jwt.encode(payload, NEXTAUTH_SECRET, algorithm="HS256")
    logger.debug(f"Basic token: {basic_token}")
    
    # Token with Bearer prefix
    bearer_token = f"Bearer {basic_token}"
    logger.debug(f"Bearer token: {bearer_token}")
    
    # URL encoded token
    encoded_token = quote(basic_token)
    logger.debug(f"URL encoded token: {encoded_token}")
    
    # URL encoded Bearer token
    encoded_bearer = quote(bearer_token)
    logger.debug(f"URL encoded Bearer token: {encoded_bearer}")
    
    return {
        "basic": basic_token,
        "bearer": bearer_token,
        "encoded": encoded_token,
        "encoded_bearer": encoded_bearer
    }

async def test_websocket_connection(token, token_type):
    """Test WebSocket connection with different token formats"""
    execution_id = "8d917f7c-d200-4fbd-a8b0-50cf2cab8405"
    
    logger.info(f"\nTesting {token_type}:")
    ws_url = f"{WS_URL}/api/flows/executions/{execution_id}/logs/ws?token={token}"
    logger.info(f"Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info(f"WebSocket connected successfully with {token_type}!")
            
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received message: {message}")
            except asyncio.TimeoutError:
                logger.info("No messages received after 5 seconds")
                
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"Failed to connect with {token_type}")
        logger.error(f"Status code: {e.status_code}")
        logger.error(f"Response headers: {e.headers}")
    except Exception as e:
        logger.error(f"Error with {token_type}: {str(e)}", exc_info=True)
        
    # Wait a bit between attempts
    await asyncio.sleep(1)

async def main():
    tokens = generate_test_tokens()
    # Test each token format
    await test_websocket_connection(tokens["basic"], "basic token")
    await test_websocket_connection(quote(f"Bearer {tokens['basic']}"), "bearer token")  # URL encode the Bearer token
    await test_websocket_connection(tokens["encoded"], "encoded token")
    await test_websocket_connection(f"Bearer%20{tokens['basic']}", "encoded_bearer token")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
