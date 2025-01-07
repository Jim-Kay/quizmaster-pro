"""
Test Name: test_book_flow
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

#!/usr/bin/env python
"""
Test for the book flow with caching.

To run this test:
1. Make sure the backend server is running
2. Run the test using conda:
   conda run -n crewai-quizmaster-pro python backend/api/tests/test_book_flow.py

Note: This test will attempt to use cached results if available to speed up testing.
If no cache is available, you may need to run the flow without cache first and save
the results for future test runs.
"""

import os
import sys
import asyncio
from uuid import uuid4

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from api.tests.utils.flow_tester import FlowTester

async def test_book_flow():
    """Test the book flow using cache if available."""
    tester = FlowTester()
    
    # Try to use cached result
    print("\nTesting book flow with cache...")
    result = await tester.execute_flow(
        flow_name="book",
        initial_state={
            "topic": "A day in the life of a pet hamster",
            "goal": """
                Write a short children's book about a pet hamster's daily activities,
                focusing on their routines, habits, and fun adventures.
                The book should be educational and entertaining for young readers.
            """,
            "book": [],  # Empty list of chapters initially
            "book_outline": []  # Empty list of chapter outlines initially
        },
        max_attempts=3,  # Reduce for testing
        delay_seconds=1.0,  # Reduce for testing
        expected_status="completed",
        use_cache=True  # Always try to use cache
    )
    
    # Verify result
    assert result is not None, "Flow execution failed"
    assert "book" in result, "No book in result"
    assert len(result["book"]) > 0, "No chapters in book"
    
    # Test unauthorized access
    print("\nTesting unauthorized access...")
    wrong_user_result = await tester.execute_flow_with_wrong_user(
        flow_name="book",
        initial_state={
            "topic": "Test topic",
            "goal": "Test goal"
        }
    )
    assert wrong_user_result is None, "Expected unauthorized access to fail"
    
    print("\nAll tests passed!")

async def main():
    await test_book_flow()

if __name__ == "__main__":
    asyncio.run(main())
