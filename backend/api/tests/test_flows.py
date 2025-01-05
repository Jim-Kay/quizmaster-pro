import asyncio
import httpx
import json
import os
import jwt
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import MOCK_USER_ID

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")

def create_test_token() -> str:
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

async def test_flow(
    flow_name: str,
    initial_state: Dict[str, Any],
    base_url: str = "http://localhost:8000"
) -> None:
    """Test a flow execution end-to-end."""
    # Get test token
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Create flow execution
        print(f"\nTesting {flow_name} flow...")
        print("Creating flow execution...")
        create_response = await client.post(
            f"{base_url}/api/flows/executions",
            json={
                "flow_name": flow_name,
                "initial_state": initial_state
            },
            headers=headers
        )
        create_response.raise_for_status()
        execution = create_response.json()
        execution_id = execution["id"]
        print(f"Created execution {execution_id}")

        # 2. Start flow execution
        print("Starting flow execution...")
        start_response = await client.post(
            f"{base_url}/api/flows/executions/{execution_id}/start",
            headers=headers
        )
        start_response.raise_for_status()
        print("Flow started")

        # 3. Poll for completion and stream logs
        print("\nFlow progress:")
        while True:
            # Get status
            status_response = await client.get(
                f"{base_url}/api/flows/executions/{execution_id}",
                headers=headers
            )
            status_response.raise_for_status()
            status = status_response.json()
            
            # Get latest logs
            logs_response = await client.get(
                f"{base_url}/api/flows/executions/{execution_id}/logs",
                headers=headers
            )
            if logs_response.status_code == 200:
                print(logs_response.text, end="", flush=True)
            
            if status["status"] == "completed":
                print("\nFlow completed successfully!")
                break
            elif status["status"] == "failed":
                error = status.get("error", "Unknown error")
                raise Exception(f"Flow failed: {error}")
            
            await asyncio.sleep(2)

        # 4. Get final state
        print("\nFinal state:")
        state_response = await client.get(
            f"{base_url}/api/flows/executions/{execution_id}/state",
            headers=headers
        )
        state_response.raise_for_status()
        final_state = state_response.json()
        print(json.dumps(final_state, indent=2))

async def main():
    """Run tests for all flows."""
    # Test poem flow
    await test_flow(
        "poem",
        initial_state={
            "topic_title": "Test Topic",
            "topic_description": "A test topic about testing flows",
            "sentence_count": 3
        }
    )

    # Test book flow
    await test_flow(
        "book",
        initial_state={
            "topic_title": "Test Topic",
            "topic_description": "A test topic about testing flows",
            "chapter_count": 2
        }
    )

if __name__ == "__main__":
    asyncio.run(main())
