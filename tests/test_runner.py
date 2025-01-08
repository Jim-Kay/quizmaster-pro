#!/usr/bin/env python
"""
QuizMasterPro Test Runner
Executes tests in the correct sequence based on level and dependencies.

Environment Setup:
    1. Activate the conda environment:
       ```bash
       conda activate crewai-quizmaster-pro
       ```
    
    2. Required Environment Variables:
       - TEST_MODE: Set to 'true' to run against test database
       - PYTHONPATH: Set to backend directory (e.g., c:/ParseThat/QuizMasterPro/backend)
       - POSTGRES_USER: Database username
       - POSTGRES_PASSWORD: Database password
       - POSTGRES_HOST: Database host (default: localhost)
       - POSTGRES_PORT: Database port (default: 5432)
       - TEST_DB_NAME: Test database name (default: quizmaster_test)
       - API_HOST: Backend API host (default: localhost)
       - API_PORT: Backend API port (default: 8000)

    3. Required Services:
       - PostgreSQL database running
       - Backend API server:
         Run _start_backend.bat in the project root directory
         (This will activate the correct conda environment and start the backend server)
       
       - Frontend development server:
         Run _start_frontend.bat in the project root directory
         (This will start the frontend development server)

       Note: The batch files handle environment activation and correct working directory
       automatically. If running services manually, use these commands:
         ```bash
         # Backend (from /backend directory)
         uvicorn api.main:app --reload
         
         # Frontend (from /frontend directory)
         npm run dev
         ```

Execution:
    1. Change to the project root directory:
       ```bash
       cd /path/to/QuizMasterPro
       ```
    
    2. Run the test runner:
       ```bash
       # First activate conda environment and set required environment variables
       cmd /c call conda activate crewai-quizmaster-pro && set TEST_MODE=true && set PYTHONPATH=/path/to/QuizMasterPro/backend && python tests/test_runner.py
       
       # Optionally specify mode (default is quick):
       cmd /c call conda activate crewai-quizmaster-pro && set TEST_MODE=true && set PYTHONPATH=/path/to/QuizMasterPro/backend && python tests/test_runner.py --mode quick
       cmd /c call conda activate crewai-quizmaster-pro && set TEST_MODE=true && set PYTHONPATH=/path/to/QuizMasterPro/backend && python tests/test_runner.py --mode full
       ```

Modes:
    - quick: Run only essential tests (Levels 0-2)
    - full: Run all tests (Levels 0-4)
    - ci: Run tests suitable for continuous integration
    - pre-release: Run comprehensive tests with extended validation

Output:
    - Console output shows real-time test progress
    - Log file created in current directory: test_run_YYYYMMDD_HHMMSS.log
    - Test report shows summary of passed/failed tests and execution times

Exit Codes:
    0: All tests passed
    1: One or more tests failed
    2: Environment setup or configuration error
"""

import os
import sys
import logging
import asyncio
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import httpx
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from utils.metadata import TestMetadata
from utils.discovery import discover_tests, validate_dependencies, detect_cycles, group_tests_by_level
from utils.execution import TestExecutor

# Load test environment variables
env_file = Path(__file__).parent.parent / '.env.test'
if env_file.exists():
    load_dotenv(env_file)
else:
    logger = logging.getLogger(__name__)
    logger.warning("No .env.test file found, using default environment variables")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

async def check_services(mode: str = 'quick') -> bool:
    """Check if required services are running"""
    try:
        # Check database connection
        db_url = (
            f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('TEST_DB_NAME', 'quizmaster_test')}"
        )
        engine = create_async_engine(db_url, poolclass=NullPool)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")

        # Check backend API
        if mode != 'quick':
            api_url = f"http://{os.getenv('API_HOST', 'localhost')}:{os.getenv('API_PORT', '8000')}/health"
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url)
                if response.status_code != 200:
                    logger.error(f"Backend API health check failed: {response.status_code}")
                    return False
            logger.info("Backend API connection successful")

        return True

    except Exception as e:
        logger.error(f"Service check failed: {e}")
        return False

def validate_environment() -> bool:
    """Validate that the test runner is being executed in the correct environment"""
    try:
        # Check conda environment
        conda_env = os.environ.get('CONDA_DEFAULT_ENV')
        if conda_env != 'crewai-quizmaster-pro':
            logger.error(f"Incorrect conda environment. Expected 'crewai-quizmaster-pro', got '{conda_env}'")
            logger.error("Please run: conda activate crewai-quizmaster-pro")
            return False

        # Check required environment variables
        required_vars = ['TEST_MODE', 'PYTHONPATH', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False

        # Validate PYTHONPATH
        pythonpath = os.getenv('PYTHONPATH', '')
        if not any(p.endswith('backend') for p in pythonpath.split(os.pathsep)):
            logger.error("PYTHONPATH must include path to backend directory")
            return False

        # Check test mode
        if os.getenv('TEST_MODE') != 'true':
            logger.error("TEST_MODE must be set to 'true'")
            return False

        return True

    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='QuizMasterPro Test Runner')
    parser.add_argument('--mode', choices=['quick', 'full', 'ci', 'pre-release'],
                      default='quick', help='Test execution mode')
    args = parser.parse_args()

    # Validate environment
    if not validate_environment():
        sys.exit(2)

    # Check required services
    if not await check_services(args.mode):
        sys.exit(2)

    try:
        # Initialize test executor
        project_root = Path.cwd()
        executor = TestExecutor(project_root)

        # Discover and validate tests
        tests = discover_tests(project_root)
        if not validate_dependencies(tests):
            sys.exit(2)

        # Check for dependency cycles
        cycles = detect_cycles(tests)
        if cycles:
            logger.error("Dependency cycles detected:")
            for cycle in cycles:
                logger.error(f"  {' -> '.join(cycle)}")
            sys.exit(2)

        # Group tests by level
        levels = group_tests_by_level(tests)
        max_level = 2 if args.mode == 'quick' else 4

        # Run tests by level
        for level in sorted(levels.keys()):
            if level > max_level:
                logger.info(f"Skipping tests at level {level} in {args.mode} mode")
                continue

            logger.info(f"\nRunning Level {level} tests...")
            level_tests = levels[level]

            # Run blocking tests first
            blocking_tests = [t for t in level_tests if tests[t].blocking]
            for test in blocking_tests:
                result = await executor.run_test(test, tests[test])
                executor.results[test] = result
                if not result.success:
                    logger.error(f"Blocking test {test} failed, stopping execution")
                    print(executor.get_results_summary())
                    sys.exit(1)

            # Run remaining tests in parallel
            parallel_tests = [t for t in level_tests if not tests[t].blocking]
            if parallel_tests:
                await executor.run_parallel_tests(parallel_tests, tests)

        # Print results summary
        print(executor.get_results_summary())

        # Exit with status code based on results
        if any(not result.success for result in executor.results.values()):
            sys.exit(1)
        sys.exit(0)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
