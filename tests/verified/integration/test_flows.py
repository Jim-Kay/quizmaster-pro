"""
Integration tests for flow execution
"""
import pytest
import asyncio
from uuid import UUID
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient
from fastapi.testclient import TestClient
from api.main import app
from api.tests.utils.flow_tester import FlowTester

@pytest.fixture
def flow_tester() -> FlowTester:
    return FlowTester()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers(flow_tester: FlowTester) -> Dict[str, str]:
    token = flow_tester.create_test_token()
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_flow_execution(async_client: AsyncClient, flow_tester: FlowTester, auth_headers: Dict[str, str]):
    """Test executing a flow and monitoring its progress"""
    # Start the flow
    flow_name = "test_flow"
    initial_state = {"param1": "value1"}
    
    response = await async_client.post(
        f"/api/flows/{flow_name}/execute",
        json=initial_state,
        headers=auth_headers
    )
    assert response.status_code == 200
    execution_id = response.json()["execution_id"]

    # Connect to WebSocket to monitor progress
    with TestClient(app).websocket_connect(
        f"/api/ws/flows/{execution_id}?token={auth_headers['Authorization'].split()[1]}"
    ) as websocket:
        # Collect status updates
        updates = []
        for _ in range(3):  # Expect at least 3 status updates
            try:
                data = websocket.receive_json()
                updates.append(data["status"])
            except Exception as e:
                pytest.fail(f"Failed to receive WebSocket update: {str(e)}")

        # Verify flow progression
        assert "started" in updates
        assert "in_progress" in updates
        assert "completed" in updates

@pytest.mark.asyncio
async def test_flow_unauthorized_access(async_client: AsyncClient, flow_tester: FlowTester):
    """Test flow execution with unauthorized access"""
    flow_name = "test_flow"
    initial_state = {"param1": "value1"}
    
    # Try to execute flow without auth headers
    response = await async_client.post(
        f"/api/flows/{flow_name}/execute",
        json=initial_state
    )
    assert response.status_code == 401

    # Try to execute flow with wrong user
    result = await flow_tester.execute_flow_with_wrong_user(
        flow_name=flow_name,
        initial_state=initial_state,
        max_attempts=1
    )
    assert result is None  # Should fail due to unauthorized access

@pytest.mark.asyncio
async def test_flow_with_retries(async_client: AsyncClient, flow_tester: FlowTester, auth_headers: Dict[str, str]):
    """Test flow execution with retries on failure"""
    flow_name = "test_flow_with_retries"
    initial_state = {"should_fail": True, "fail_count": 2}  # Will fail twice then succeed
    
    result = await flow_tester.execute_flow(
        flow_name=flow_name,
        initial_state=initial_state,
        max_attempts=5,
        delay_seconds=1.0,
        expected_status="completed"
    )
    
    assert result is not None
    assert result.get("status") == "completed"
    assert result.get("retry_count") == 2
