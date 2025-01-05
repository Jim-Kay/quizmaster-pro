"""
Utility class for testing flows.
"""

import os
import jwt
import httpx
import json
import backoff
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from pydantic import UUID4

from api.auth import MOCK_USER_ID, JWT_SECRET


class FlowTester:
    """Utility class for testing flows."""
    
    def __init__(self):
        """Initialize the flow tester."""
        self.api_base_url = "http://localhost:8000"
        self.mock_user_id = MOCK_USER_ID  # Use the same mock user ID as auth.py
        
    def create_test_token(self, user_id: Optional[UUID4] = None) -> str:
        """Create a test JWT token using the same format as auth.py."""
        now = datetime.now(timezone.utc)
        token_data = {
            "sub": str(user_id or self.mock_user_id),  # Convert UUID to string
            "email": "test@example.com",
            "name": "Test User",
            "iat": now,
            "exp": now + timedelta(hours=1)
        }
        token = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")
        print(f"Created JWT token with user ID: {user_id or self.mock_user_id}")
        return token
        
    @backoff.on_exception(backoff.expo, httpx.ReadError, max_tries=3)
    async def get_flow_status(self, client: httpx.AsyncClient, execution_id: str, headers: Dict[str, str]) -> httpx.Response:
        """Get flow execution status with retries."""
        try:
            response = await client.get(
                f"{self.api_base_url}/api/flows/executions/{execution_id}",
                headers=headers
            )
            return response
        except httpx.ReadError as e:
            print(f"Error getting flow status: {str(e)}")
            raise
        
    async def execute_flow_with_wrong_user(
        self,
        flow_name: str,
        initial_state: Dict[str, Any],
        max_attempts: int = 3,
        delay_seconds: float = 1.0,
        expected_status: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Execute a flow with a different user ID to test unauthorized access."""
        wrong_user_id = uuid.uuid4()  # Generate a different user ID
        return await self.execute_flow(
            flow_name=flow_name,
            initial_state=initial_state,
            max_attempts=max_attempts,
            delay_seconds=delay_seconds,
            expected_status=expected_status,
            use_cache=use_cache,
            user_id=wrong_user_id
        )
        
    async def execute_flow(
        self,
        flow_name: str,
        initial_state: Dict[str, Any],
        max_attempts: int = 360,  # 360 attempts × 10 seconds = 1 hour
        delay_seconds: float = 10.0,  # Check every 10 seconds
        expected_status: Optional[str] = None,
        use_cache: bool = True,  # Control whether to use cache for this execution
        user_id: Optional[UUID4] = None  # Optional user ID for testing unauthorized access
    ) -> Optional[Dict[str, Any]]:
        """Execute a flow and wait for completion.
        
        Args:
            flow_name: Name of the flow to execute.
            initial_state: Initial state for the flow.
            max_attempts: Maximum number of attempts to check flow status.
            delay_seconds: Delay between status checks in seconds.
            expected_status: Expected final status of the flow. If None, any non-running status is accepted.
            use_cache: Whether to use cache for this execution.
            user_id: Optional user ID for testing unauthorized access.
            
        Returns:
            Dict containing the final flow state and logs.
        """
        # Don't add user_id to initial state - it will be added by the router
        initial_state = initial_state or {}
            
        token = self.create_test_token(user_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Create client with no timeout
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(timeout=None, limits=limits) as client:
            # 1. Create flow execution
            print(f"Creating flow execution for user {user_id or self.mock_user_id}...")
            create_response = await client.post(
                f"{self.api_base_url}/api/flows/executions",
                json={
                    "flow_name": flow_name,
                    "initial_state": initial_state,
                    "use_cache": use_cache
                },
                headers=headers
            )
            
            if create_response.status_code == 403:
                print("Unauthorized access as expected")
                return None
            elif create_response.status_code != 201:
                print(f"Error creating flow execution: {create_response.text}")
                return None
                
            execution_id = create_response.json()["id"]
            print(f"Created execution {execution_id}")
            
            # 2. Start flow execution
            print("Starting flow execution...")
            start_response = await client.post(
                f"{self.api_base_url}/api/flows/executions/{execution_id}/start",
                headers=headers
            )
            
            if start_response.status_code == 403:
                print("Unauthorized access as expected")
                return None
            elif start_response.status_code != 200:
                print(f"Error starting flow execution: {start_response.text}")
                return None
                
            print("Flow started")
            
            # 3. Poll for completion
            for attempt in range(max_attempts):
                print(f"Getting flow execution status (attempt {attempt + 1})...")
                try:
                    response = await self.get_flow_status(client, execution_id, headers)
                    if response.status_code == 403:
                        print("Unauthorized access as expected")
                        return None
                    elif response.status_code != 200:
                        print(f"Error getting flow status: {response.status_code}")
                        print(response.text)
                        return None
                        
                    execution = response.json()
                    status = execution["status"]
                    print(f"Flow status: {status}")
                    
                    if status == "failed":
                        print(f"Flow failed: {execution.get('error', 'Unknown error')}")
                        return None
                    elif status == "completed":
                        print("Flow completed successfully!")
                        
                        # Get logs
                        logs_response = await client.get(
                            f"{self.api_base_url}/api/flows/executions/{execution_id}/logs",
                            headers=headers
                        )
                        if logs_response.status_code == 403:
                            print("Unauthorized access as expected")
                            return None
                        elif logs_response.status_code != 200:
                            print(f"Error getting logs: {logs_response.status_code}")
                            print(logs_response.text)
                        else:
                            print("Flow logs:")
                            print(logs_response.text)
                            
                        return execution["state"]
                    elif status == "running":
                        await asyncio.sleep(delay_seconds)
                    else:
                        print(f"Unexpected status: {status}")
                        return None
                except Exception as e:
                    print(f"Error checking flow status: {str(e)}")
                    await asyncio.sleep(delay_seconds)
                    continue
                    
            print(f"Flow did not complete after {max_attempts} attempts")
            return None
