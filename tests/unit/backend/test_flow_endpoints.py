"""
Test Name: test_flow_endpoints
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
Test for the flow execution endpoints.

This test will verify that the flow execution API endpoints are working correctly:
1. Create a flow execution
2. Start the flow execution
3. Get the flow execution status
4. Get the flow execution logs
"""

import os
import sys
import jwt
import httpx
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuration
API_BASE_URL = "http://localhost:8000"
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")

# Mock user ID for testing - using a proper UUID v4
MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

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

async def test_flow_endpoints():
    """Test the flow execution endpoints."""
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create flow execution
        print("\nTesting flow endpoints...")
        print("Creating flow execution...")
        create_response = await client.post(
            f"{API_BASE_URL}/api/flows/executions",
            json={
                "flow_name": "test",
                "initial_state": {
                    "message": "Initial message"
                }
            },
            headers=headers
        )
        
        if create_response.status_code != 201:
            print(f"Error creating flow execution: {create_response.status_code}")
            print(create_response.text)
            return
            
        execution = create_response.json()
        execution_id = execution["id"]
        print(f"Created execution {execution_id}")

        # 2. Start flow execution
        print("Starting flow execution...")
        start_response = await client.post(
            f"{API_BASE_URL}/api/flows/executions/{execution_id}/start",
            headers=headers
        )
        
        if start_response.status_code != 200:
            print(f"Error starting flow execution: {start_response.status_code}")
            print(start_response.text)
            return
            
        print("Flow started")

        # Wait a moment for the flow to start
        await asyncio.sleep(2)

        # 3. Get flow execution status
        print("Getting flow execution status...")
        status_response = await client.get(
            f"{API_BASE_URL}/api/flows/executions/{execution_id}",
            headers=headers
        )
        
        if status_response.status_code != 200:
            print(f"Error getting flow execution status: {status_response.status_code}")
            print(status_response.text)
            return
            
        status = status_response.json()
        print(f"Flow status: {status['status']}")

        # 4. Get flow execution logs
        print("Getting flow execution logs...")
        logs_response = await client.get(
            f"{API_BASE_URL}/api/flows/executions/{execution_id}/logs",
            headers=headers
        )
        
        if logs_response.status_code == 200:
            print("Flow logs:")
            print(logs_response.text)
        else:
            print(f"Error getting flow execution logs: {logs_response.status_code}")
            print(logs_response.text)

async def main():
    """Run the tests."""
    await test_flow_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
