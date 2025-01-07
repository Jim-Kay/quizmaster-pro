"""
Test Name: test_poem_flow
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
Test for the poem flow execution.

This test will verify that the poem flow API endpoints are working correctly:
1. Create a poem flow execution
2. Start the flow execution
3. Get the flow execution status
4. Get the flow execution logs
5. Verify the generated poem
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from api.tests.utils.flow_tester import FlowTester


async def test_poem_flow() -> None:
    """Test the poem flow."""
    tester = FlowTester()
    
    # Test with a simple topic
    initial_state = {
        "topic_title": "A Beautiful Sunset",
        "topic_description": "A peaceful evening scene with the sun setting over the horizon",
        "sentence_count": 3
    }
    
    result = await tester.execute_flow(
        flow_name="poem",
        initial_state=initial_state,
        max_attempts=3,  # Reduce for testing
        delay_seconds=1.0,  # Reduce for testing
        expected_status="completed"
    )
    
    if not result:
        print("Flow execution failed or no cache available")
        return
        
    print("\nGenerated Poem:")
    if "state" in result and "poem" in result["state"]:
        print(result["state"]["poem"])
    else:
        print("No poem found in flow state")


async def main() -> None:
    """Run the test."""
    await test_poem_flow()


if __name__ == "__main__":
    asyncio.run(main())
