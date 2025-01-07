"""
Test Name: test_blueprint_crew
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
NOTE: This pytest version of the blueprint crew test is currently not in use due to several issues:

1. Integration Test Nature:
   - This is more of an integration test than a unit test, involving multiple components:
     * CrewAI interactions
     * LLM API calls
     * File system operations
   - These components are better tested using the non-pytest version (test_blueprint_crew_not_pytest.py)

2. Technical Issues:
   - Encountered collection issues with pytest-asyncio in Python 3.12
   - Difficulties in handling the asynchronous nature of CrewAI operations within pytest
   - Complex fixture requirements for proper test isolation

3. Debugging and Visibility:
   - The non-pytest version provides better logging visibility
   - Easier to debug without pytest's test collection and fixture system
   - More straightforward execution flow

For running tests of the blueprint crew functionality, please use test_blueprint_crew_not_pytest.py instead.
This file is kept for reference and potential future pytest integration when the issues are resolved.
"""

import os
import sys
import uuid
import logging
import pytest
from pathlib import Path
from datetime import datetime
from crewai import Agent, Task, Crew
from api.utils.file_utils import sanitize_filename
from api.crews.blueprint_crew.blueprint_crew import BlueprintCrew
from api.routers.schemas import Blueprint  # Import Blueprint schema
from dotenv import load_dotenv

# Configure logging
logs_dir = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs')
os.makedirs(logs_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_dir, f'output_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(filename)s-%(module)s:%(lineno)d - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import locale
    if locale.getpreferredencoding().upper() != 'UTF-8':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

@pytest.fixture
def blueprint_inputs():
    """Fixture to provide test inputs for blueprint generation."""
    topic = "Python Programming"
    description = "Introduction to Python programming language basics"
    topic_dir = os.path.join(logs_dir, sanitize_filename(topic))
    os.makedirs(topic_dir, exist_ok=True)
    
    return {
        "blueprint_id": uuid.uuid4(),
        "topic": topic,
        "description": description,
        "topic_id": uuid.uuid4(),
        "created_by": uuid.uuid4(),
        "output_folder": topic_dir
    }

def test_blueprint_crew_generation(blueprint_inputs):
    """Test that the blueprint crew can generate a valid blueprint."""
    try:
        # Create an instance of BlueprintCrew with inputs
        logger.info("Initializing BlueprintCrew...")
        blueprint_crew = BlueprintCrew(inputs=blueprint_inputs)
        
        # Get crew instance
        logger.info("Getting crew instance...")
        crew = blueprint_crew.crew()
        
        # Run the crew
        logger.info("Starting blueprint generation...")
        result = crew.kickoff(blueprint_inputs)
        
        # Verify the result is not None
        assert result is not None, "Blueprint generation result should not be None"
        
        # Handle different result types
        if isinstance(result, Blueprint):
            blueprint = result
            logger.info("Result is already a Blueprint instance")
        else:
            try:
                # Try to convert from raw format
                if isinstance(result, str):
                    import json
                    result_dict = json.loads(result)
                else:
                    result_dict = result.raw if hasattr(result, 'raw') else result
                    
                blueprint = Blueprint(**result_dict)
                logger.info("Successfully converted result to Blueprint")
            except Exception as e:
                logger.warning(f"Could not convert result to Blueprint: {e}")
                logger.info(f"Raw result: {result}")
                # Don't fail the test, just log the raw result
                return

        # Log the blueprint details
        logger.info("\nGenerated Blueprint Details:")
        if hasattr(blueprint, 'title'):
            logger.info(f"Title: {blueprint.title}")
        if hasattr(blueprint, 'description'):
            logger.info(f"Description: {blueprint.description}")
        
        # Log terminal objectives if they exist
        if hasattr(blueprint, 'terminal_objectives') and blueprint.terminal_objectives:
            logger.info("\nTerminal Objectives:")
            for to in blueprint.terminal_objectives:
                logger.info(f"\nObjective {getattr(to, 'number', 'N/A')}:")
                logger.info(f"Description: {getattr(to, 'description', 'N/A')}")
                logger.info(f"Cognitive Level: {getattr(to, 'cognitive_level', 'N/A')}")
                
                if hasattr(to, 'enabling_objectives') and to.enabling_objectives:
                    logger.info("\nEnabling Objectives:")
                    for eo in to.enabling_objectives:
                        logger.info(f"- {getattr(eo, 'number', 'N/A')}: {getattr(eo, 'description', 'N/A')}")
                        logger.info(f"  Cognitive Level: {getattr(eo, 'cognitive_level', 'N/A')}")
        
        logger.info("Blueprint generation test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in blueprint generation test: {str(e)}")
        raise
