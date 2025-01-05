import asyncio
import httpx
import json
from typing import Dict, Any

async def test_flow(
    flow_name: str,
    initial_state: Dict[str, Any],
    base_url: str = "http://localhost:8000"
) -> None:
    """Test a flow execution end-to-end."""
    async with httpx.AsyncClient() as client:
        # 1. Create flow execution
        print(f"\nTesting {flow_name} flow...")
        print("Creating flow execution...")
        create_response = await client.post(
            f"{base_url}/api/flows/executions",
            json={
                "flow_name": flow_name,
                "initial_state": initial_state
            }
        )
        create_response.raise_for_status()
        execution = create_response.json()
        execution_id = execution["id"]
        print(f"Created execution {execution_id}")

        # 2. Start flow execution
        print("Starting flow execution...")
        start_response = await client.post(
            f"{base_url}/api/flows/executions/{execution_id}/start"
        )
        start_response.raise_for_status()
        print("Flow started")

        # 3. Poll for completion
        print("Polling for completion...")
        while True:
            status_response = await client.get(
                f"{base_url}/api/flows/executions/{execution_id}"
            )
            status_response.raise_for_status()
            status = status_response.json()
            
            if status["status"] == "completed":
                print("Flow completed successfully!")
                break
            elif status["status"] == "failed":
                error = status.get("error", "Unknown error")
                raise Exception(f"Flow failed: {error}")
            
            await asyncio.sleep(2)

        # 4. Get final state
        print("Getting final state...")
        state_response = await client.get(
            f"{base_url}/api/flows/executions/{execution_id}/state"
        )
        state_response.raise_for_status()
        final_state = state_response.json()
        print("\nFinal state:")
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
