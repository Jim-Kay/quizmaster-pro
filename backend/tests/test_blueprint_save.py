import os
import sys
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Add the backend directory to sys.path to allow importing from backend
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from api.routers.schemas import Blueprint

# Configure logging
def setup_logging():
    logs_dir = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f'test_blueprint_save_{timestamp}.log')
    
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

def main():
    try:
        setup_logging()
        logger.info("Starting blueprint save test")

        # Create UUIDs for our test data
        blueprint_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        user_id = uuid.uuid4()
        terminal_obj_id = uuid.uuid4()
        enabling_obj_id = uuid.uuid4()

        # Create sample blueprint data
        blueprint_data = {
            "id": blueprint_id,
            "title": "Python Programming",
            "description": "Introduction to Python programming language basics",
            "topic_id": topic_id,
            "created_by": user_id,
            "terminal_objectives": [
                {
                    "id": terminal_obj_id,
                    "number": 1,
                    "description": "Identify and describe the components of a basic Python program.",
                    "cognitive_level": "remember",
                    "topic_id": topic_id,
                    "enabling_objectives": [
                        {
                            "id": enabling_obj_id,
                            "number": "1.1",
                            "description": "Identify basic Python data types (integers, floats, strings, lists).",
                            "cognitive_level": "remember",
                            "terminal_objective_id": terminal_obj_id
                        }
                    ]
                }
            ],
            "terminal_objectives_count": 1,
            "enabling_objectives_count": 1,
            "status": "completed"
        }

        # Create Blueprint object from the data
        blueprint = Blueprint(**blueprint_data)
        logger.info(f"Created Blueprint object with title: {blueprint.title}")

        # Create a test output folder
        test_output = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs', 'test_output')
        logger.info(f"Will save blueprint to: {test_output}")

        # Save the blueprint to a new file
        output_file = blueprint.save_to_file(test_output)
        logger.info(f"Successfully saved blueprint to: {output_file}")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

if __name__ == "__main__":
    main()
