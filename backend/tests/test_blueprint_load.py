import os
import sys
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
    log_file = os.path.join(logs_dir, f'test_blueprint_load_{timestamp}.log')
    
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
        logger.info("Starting blueprint load test")

        # Load the sample blueprint
        sample_path = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs', 'sample_blueprint.json')
        logger.info(f"Loading blueprint from: {sample_path}")

        # Load the blueprint using the new class method
        blueprint = Blueprint.from_json_file(sample_path)
        logger.info(f"Successfully loaded blueprint with title: {blueprint.title}")

        # Log some details about the loaded blueprint
        logger.info(f"Blueprint details:")
        logger.info(f"  - Blueprint ID: {blueprint.blueprint_id}")
        logger.info(f"  - Description: {blueprint.description}")
        logger.info(f"  - Terminal Objectives: {len(blueprint.terminal_objectives)}")
        logger.info(f"  - Status: {blueprint.status}")

        # Test saving to a new location
        test_output = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs', 'test_output')
        logger.info(f"Saving loaded blueprint to new location: {test_output}")
        
        output_file = blueprint.save_to_file(test_output)
        logger.info(f"Successfully saved blueprint to: {output_file}")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

if __name__ == "__main__":
    main()
