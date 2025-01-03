# Note: This script is not intended to be run as a pytest test
# To run this script, use the following command:
#       conda run -n crewai-quizmaster-pro python -u c:/ParseThat/QuizMasterPro/backend/tests/test_question_crew_not_pytest.py

import os
import sys
import uuid
import logging
from pathlib import Path
from datetime import datetime
from crewai import Agent, Task, Crew
import logging
from api.utils.file_utils import sanitize_filename

# Get the backend directory path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
crews_dir = os.path.join(backend_dir, 'api', 'crews')

# Add both possible paths to sys.path
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)
sys.path.insert(0, crews_dir)

# Configure logging
def setup_logging():
    logs_dir = os.path.join(backend_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f'output_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(process)d - %(filename)s-%(module)s:%(lineno)d - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Create logger for this module
logger = logging.getLogger(__name__)

from api.crews.question_crew.question_crew import QuestionCrew
from api.schemas.pydantic_schemas import Assessment, Question  # Update import path
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    # Set up UTF-8 encoding for Windows console
    if sys.platform.startswith('win'):
        import locale
        if locale.getpreferredencoding().upper() != 'UTF-8':
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')

    setup_logging()
    
    logger.info(f"Loading Sample Blueprint...")

    # Load sample blueprint
    blueprint_path = os.path.join(backend_dir, "tests", "sample_blueprint_partial.json")
    if not os.path.exists(blueprint_path):
        logger.error(f"Blueprint file not found: {blueprint_path}")
        sys.exit(1)

    try:
        # Create logs directory and topic-specific output folder with timestamp
        timestamp = "2025-01-02_17-26-34"  # Current time in format YYYY-MM-DD_HH-MM-SS
        logs_dir = os.path.join(backend_dir, "logs")
        log_file = os.path.join(logs_dir, f'output_{timestamp}.log')
        topic_dir = os.path.join(logs_dir, f"question_crew_test_{timestamp}")
        os.makedirs(topic_dir, exist_ok=True)
        logger.info(f"Created output directory: {topic_dir}")
        logger.debug(f"Full output directory path: {os.path.abspath(topic_dir)}")

        # Define the input parameters based on question crew config
        style_guide = os.path.join(backend_dir, "api", "crews", "reference_documents", "Style Guide for Assessments.md")
        inputs = {
            "blueprint": blueprint_path,
            "number_of_questions": 3,  # Default number of questions
            "topic": "Playwright Testing",  # Topic from sample blueprint
            "style_guide_path": style_guide,
            "style_guide_pdf_path": style_guide,  # For backward compatibility
            "output_folder": topic_dir
        }

        # Create an instance of QuestionCrew with inputs
        logger.info("Initializing QuestionCrew...")
        logger.debug(f"Input parameters: {inputs}")
        question_crew = QuestionCrew()
        logger.info("QuestionCrew initialized successfully")
        
        logger.info("Getting crew instance...")
        crew = question_crew.crew()
        logger.info("Crew instance created successfully")
        
        logger.info(f"Starting question generation with inputs: {inputs}")
        logger.debug("Starting crew.kickoff()")
        result = crew.kickoff(inputs)
        logger.debug("crew.kickoff() completed")
        
        # Print the result
        if isinstance(result, Assessment):
            logger.info("\nGenerated Questions:")
            logger.info(result.model_dump_json(indent=2))
        else:
            logger.info("\nRaw Result:")
            logger.info(result)
            
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {dir(e)}")
        logger.error("Full traceback:", exc_info=True)
        raise

if __name__ == "__main__":
    main()
