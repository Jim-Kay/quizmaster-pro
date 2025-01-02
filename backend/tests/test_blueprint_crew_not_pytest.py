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
sys.path.append(backend_dir)

# Configure logging
def setup_logging():
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

from api.crews.blueprint_crew.blueprint_crew import BlueprintCrew
from api.routers.schemas import Blueprint  # Import Blueprint schema
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

    topic = "Python Programming"
    description = "Introduction to Python programming language basics"
    #taxonomy_pdf_path = os.path.join(backend_dir, "api", "crews", "reference_documents", "The Revised Blooms Taxonomy.pdf")
    #taxonomy_pdf_path_string = str(taxonomy_pdf_path)

    #if not os.path.exists(taxonomy_pdf_path):
    #    logger.error(f"Taxonomy PDF file not found: {taxonomy_pdf_path}")
    #    sys.exit(1)

    try:
        # Create logs directory and topic-specific output folder
        logs_dir = os.path.join('C:\\', 'data', 'crewai-quizmaster-pro', 'logs')
        topic_dir = os.path.join(logs_dir, sanitize_filename(topic))
        os.makedirs(topic_dir, exist_ok=True)
        logger.info(f"Created output directory: {topic_dir}")

        # Define the input parameters
        inputs = {
            "blueprint_id": uuid.uuid4(),  # Issue a new UUID
            "topic": topic,
            "description": description,
            #"taxonomy_pdf_path": taxonomy_pdf_path_string,
            "topic_id": uuid.uuid4(),  # For production this should be the topic_id
            "created_by": uuid.uuid4(),  # For production this should be the user_id
            "output_folder": topic_dir
        }

        # Create an instance of BlueprintCrew with inputs
        logger.info("Initializing BlueprintCrew...")
        blueprint_crew = BlueprintCrew(inputs=inputs)
        
        logger.info("Getting crew instance...")
        crew = blueprint_crew.crew()
        
        logger.info(f"Starting blueprint generation with inputs: {inputs}")
        result = crew.kickoff(inputs)
        
        # Print the result
        if isinstance(result, Blueprint):
            logger.info("\nGenerated Blueprint:")
            logger.info(result.model_dump_json(indent=2))
        else:
            logger.info("\nRaw Result:")
            logger.info(result)
            
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {dir(e)}")
        raise

if __name__ == "__main__":
    main()
