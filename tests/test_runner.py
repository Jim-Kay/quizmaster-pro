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
import re
import sys
import time
import json
import yaml
import logging
import asyncio
import argparse
import importlib
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import httpx
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from dataclasses import dataclass, field

# Load test environment variables
env_file = Path(__file__).parent.parent / '.env.test'
if env_file.exists():
    load_dotenv(env_file)
else:
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

@dataclass
class TestMetadata:
    """Test file metadata"""
    level: int = 0
    dependencies: List[str] = field(default_factory=list)
    blocking: bool = False
    parallel_safe: bool = True
    estimated_duration: int = 0
    file_path: str = ""
    working_directory: str = "project_root"
    required_paths: List[str] = field(default_factory=list)

class TestRunner:
    """Test runner class"""
    mode: str = 'quick'
    tests: Dict[str, TestMetadata] = {}
    results: Dict[str, bool] = {}
    start_times: Dict[str, float] = {}
    project_root: Path = Path.cwd()

    def extract_metadata(self, file_path: str) -> Optional[TestMetadata]:
        """Extract metadata from test file docstring"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check for docstring
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if not docstring_match:
                logger.error(f"No docstring found in {file_path}")
                return None
            
            docstring = docstring_match.group(1)
            
            # Check for Test Metadata section
            if 'Test Metadata:' not in docstring:
                logger.error(f"No 'Test Metadata:' section found in {file_path}")
                return None
                
            metadata_section = docstring.split('Test Metadata:')[1].split('\n\n')[0]
            
            metadata = TestMetadata()
            metadata.file_path = file_path

            # Extract level
            level_match = re.search(r'Level:\s*(\d+)', metadata_section)
            if level_match:
                metadata.level = int(level_match.group(1))
            else:
                logger.error(f"No Level field found in {file_path}")
                return None

            # Extract dependencies
            deps_match = re.search(r'Dependencies:\s*\[(.*?)\]', metadata_section)
            if deps_match:
                deps = deps_match.group(1).strip()
                if deps:
                    metadata.dependencies = [d.strip() for d in deps.split(',')]

            # Extract blocking flag
            blocking_match = re.search(r'Blocking:\s*(True|False)', metadata_section)
            if blocking_match:
                metadata.blocking = blocking_match.group(1) == 'True'
            else:
                logger.error(f"No Blocking field found in {file_path}")
                return None

            # Extract parallel_safe flag
            parallel_match = re.search(r'Parallel_Safe:\s*(True|False)', metadata_section)
            if parallel_match:
                metadata.parallel_safe = parallel_match.group(1) == 'True'
            else:
                logger.error(f"No Parallel_Safe field found in {file_path}")
                return None

            # Extract estimated duration
            duration_match = re.search(r'Estimated_Duration:\s*(\d+)', metadata_section)
            if duration_match:
                metadata.estimated_duration = int(duration_match.group(1))
            else:
                logger.error(f"No Estimated_Duration field found in {file_path}")
                return None

            # Extract working directory
            working_dir_match = re.search(r'Working_Directory:\s*(\w+)', metadata_section)
            if working_dir_match:
                metadata.working_directory = working_dir_match.group(1)
            else:
                logger.error(f"No Working_Directory field found in {file_path}")
                return None

            # Extract required paths
            required_paths_match = re.search(r'Required_Paths:\s*\n((?:\s*-.*\n)*)', metadata_section, re.MULTILINE)
            if required_paths_match:
                paths_text = required_paths_match.group(1)
                paths = [line.strip('- \n') for line in paths_text.split('\n') if line.strip()]
                metadata.required_paths = paths
            else:
                logger.error(f"No Required_Paths field found in {file_path}")
                return None

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None

    def validate_working_directory(self, metadata: TestMetadata) -> bool:
        """Validate that the working directory and required paths exist"""
        try:
            if metadata.working_directory == 'project_root':
                working_dir = self.project_root
            else:
                working_dir = self.project_root / metadata.working_directory

            if not working_dir.exists():
                logger.error(f"Working directory {working_dir} does not exist")
                return False

            for path in metadata.required_paths:
                if not (working_dir / path).exists():
                    logger.error(f"Required path {path} does not exist")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating working directory: {e}")
            return False

    def discover_tests(self):
        """Discover all test files and their metadata"""
        logger.info("Discovering tests...")
        verified_dir = Path('tests/verified')
        
        if not verified_dir.exists():
            logger.error("Verified tests directory not found!")
            return
        
        test_files_found = False
        for test_file in verified_dir.rglob('*.py'):
            if test_file.name.startswith('test_'):
                test_files_found = True
                is_valid, error = validate_test_metadata(str(test_file))
                if not is_valid:
                    logger.error(f"Invalid metadata in {test_file}:")
                    logger.error(f"  {error}")
                    raise ValueError(f"Test file {test_file} has invalid metadata: {error}")
                
                metadata = self.extract_metadata(str(test_file))
                if metadata:
                    self.tests[str(test_file)] = metadata
        
        if not test_files_found:
            logger.error("No test files found in the verified directory!")
            raise ValueError("No test files found in the verified directory!")
        
        logger.info(f"Discovered {len(self.tests)} test files")

    def validate_dependencies(self) -> bool:
        """Validate that all test dependencies exist"""
        all_tests = set(self.tests.keys())
        for test, metadata in self.tests.items():
            for dep in metadata.dependencies:
                if dep and dep not in all_tests:
                    logger.error(f"Missing dependency {dep} for test {test}")
                    return False
        return True

    def setup_python_path(self, working_dir: str) -> str:
        """Set up PYTHONPATH for the test"""
        if working_dir == 'backend':
            return os.path.join(self.project_root, 'backend')
        elif working_dir == 'frontend':
            return os.path.join(self.project_root, 'frontend')
        return str(self.project_root)

    async def run_test(self, test_path: str) -> bool:
        """Run a single test file"""
        metadata = self.tests[test_path]
        
        # Validate working directory and required paths
        if not self.validate_working_directory(metadata):
            return False
        
        try:
            self.start_times[test_path] = time.time()
            logger.info(f"Starting test: {test_path}")
            
            # Determine working directory and python path
            if metadata.working_directory == 'project_root':
                working_dir = self.project_root
            else:
                working_dir = self.project_root / metadata.working_directory
            
            python_path = self.setup_python_path(metadata.working_directory)
            
            # Store current directory and PYTHONPATH
            original_dir = os.getcwd()
            original_pythonpath = os.environ.get('PYTHONPATH', '')
            
            try:
                # Change to test working directory
                os.chdir(working_dir)
                os.environ['PYTHONPATH'] = f"{python_path}{os.pathsep}{original_pythonpath}"
                logger.info(f"Changed to working directory: {working_dir}")
                logger.info(f"Set PYTHONPATH: {os.environ['PYTHONPATH']}")
                
                # Import and run the test
                spec = importlib.util.spec_from_file_location(
                    "test_module",
                    self.project_root / test_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for and run test_main function
                if hasattr(module, 'test_main'):
                    if asyncio.iscoroutinefunction(module.test_main):
                        await module.test_main()
                    else:
                        module.test_main()
                        
                duration = time.time() - self.start_times[test_path]
                logger.info(f"Test {test_path} completed in {duration:.2f}s")
                return True
                
            finally:
                # Always restore original directory and PYTHONPATH
                os.chdir(original_dir)
                os.environ['PYTHONPATH'] = original_pythonpath
                logger.info(f"Restored working directory: {original_dir}")
                logger.info(f"Restored PYTHONPATH: {original_pythonpath}")
        
        except Exception as e:
            logger.error(f"Test {test_path} failed: {e}")
            return False

    async def run_level(self, level: int) -> bool:
        """Run all tests for a given level"""
        level_tests = {k: v for k, v in self.tests.items() if v.level == level}
        if not level_tests:
            return True

        logger.info(f"\nExecuting Level {level} tests...")
        
        # Sort tests by dependencies
        sorted_tests = []
        remaining_tests = set(level_tests.keys())
        while remaining_tests:
            for test in remaining_tests.copy():
                metadata = self.tests[test]
                if all(dep in self.results and self.results[dep] for dep in metadata.dependencies):
                    sorted_tests.append(test)
                    remaining_tests.remove(test)
        
        # Run tests
        for test in sorted_tests:
            metadata = level_tests[test]
            success = await self.run_test(test)
            self.results[test] = success
            
            if not success and metadata.blocking:
                logger.error(f"Blocking test {test} failed! Stopping execution.")
                return False
                
        return True

    async def run_all(self):
        """Run all tests in sequence"""
        logger.info(f"Starting test run in {self.mode} mode")
        
        self.discover_tests()
        if not self.tests:
            logger.error("No tests found!")
            return
            
        if not self.validate_dependencies():
            logger.error("Dependency validation failed!")
            return
            
        max_level = 2 if self.mode == 'quick' else 4
        
        for level in range(max_level + 1):
            if not await self.run_level(level):
                break
                
        self.report_results()

    def report_results(self):
        """Generate test execution report"""
        logger.info("\nTest Execution Report")
        logger.info("===================")
        
        # Calculate statistics
        total_discovered = len(self.tests)
        total_executed = len(self.results)
        total_passed = sum(1 for success in self.results.values() if success)
        total_failed = sum(1 for success in self.results.values() if not success)
        total_not_run = total_discovered - total_executed
        
        success_rate = (total_passed / total_executed * 100) if total_executed > 0 else 0
        
        # Print summary
        logger.info(f"Total Tests Discovered: {total_discovered}")
        logger.info(f"Tests Executed: {total_executed}")
        logger.info(f"Tests Not Run: {total_not_run}")
        logger.info(f"Passed: {total_passed}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Print failed tests with duration
        if total_failed > 0:
            logger.info("\nFailed Tests:")
            for test_path, success in self.results.items():
                if not success:
                    duration = time.time() - self.start_times[test_path]
                    logger.info(f"- {test_path} (Duration: {duration:.2f}s)")
        
        # Print tests not run
        if total_not_run > 0:
            logger.info("\nTests Not Run:")
            not_run_tests = set(self.tests.keys()) - set(self.results.keys())
            for test_path in not_run_tests:
                metadata = self.tests[test_path]
                reason = "Skipped due to previous blocking test failure"
                logger.info(f"- {test_path}")
                logger.info(f"  Level: {metadata.level}")
                logger.info(f"  Dependencies: {', '.join(metadata.dependencies) if metadata.dependencies else 'None'}")
                logger.info(f"  Reason: {reason}")

async def check_services(mode: str = 'quick') -> bool:
    """Check if required services are running"""
    logger.info("Checking required services...")
    
    # Check PostgreSQL
    try:
        engine = create_async_engine(
            f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('TEST_DB_NAME')}",
            poolclass=NullPool
        )
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("[OK] PostgreSQL database is running")
    except Exception as e:
        logger.error(f"[X] PostgreSQL database is not accessible: {e}")
        logger.error("  Please ensure PostgreSQL is running")
        return False

    # Check Backend API
    if mode != 'quick':
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{os.getenv('API_HOST', 'localhost')}:{os.getenv('API_PORT', '8000')}/api/health"
                )
                response.raise_for_status()
                logger.info("[OK] Backend API server is running")
        except Exception as e:
            logger.error(f"[X] Backend API server is not accessible: {e}")
            logger.error("  Please ensure the backend server is running")
            return False

    return True

def validate_test_metadata(file_path: str) -> tuple[bool, str]:
    """
    Validate that a test file has the required metadata in the correct format.
    Returns (is_valid, error_message).
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check for docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            return False, "No docstring found"
        
        docstring = docstring_match.group(1)
        
        # Required metadata fields and their types
        required_fields = {
            'Level': int,
            'Dependencies': list,
            'Blocking': bool,
            'Parallel_Safe': bool,
            'Estimated_Duration': int,
            'Working_Directory': str,
            'Required_Paths': list
        }
        
        # Check for Test Metadata section
        if 'Test Metadata:' not in docstring:
            return False, "No 'Test Metadata:' section found"
            
        metadata_section = docstring.split('Test Metadata:')[1].split('\n\n')[0]
        
        # Check each required field
        for field, field_type in required_fields.items():
            # Check if field exists
            if field + ':' not in metadata_section:
                return False, f"Missing required field: {field}"
                
            # Get field value
            field_value = metadata_section.split(field + ':')[1].split('\n')[0].strip()
            
            # Validate field type
            try:
                if field_type == bool:
                    if field_value not in ['True', 'False']:
                        return False, f"Invalid boolean value for {field}: {field_value}"
                elif field_type == int:
                    int(field_value)
                elif field_type == list:
                    if not (field_value.startswith('[') and field_value.endswith(']')):
                        # Check if it's an indented list format
                        next_lines = metadata_section.split(field + ':')[1].split('\n')[1:]
                        has_items = False
                        for line in next_lines:
                            if line.strip().startswith('-'):
                                has_items = True
                                break
                        if not has_items:
                            return False, f"Invalid list format for {field}"
            except ValueError:
                return False, f"Invalid {field_type.__name__} value for {field}: {field_value}"
                
        return True, ""
        
    except Exception as e:
        return False, f"Error validating metadata: {str(e)}"

def validate_all_tests() -> bool:
    """
    Validate metadata for all test files in the verified directory.
    Returns True if all tests are valid, False otherwise.
    """
    verified_dir = Path('tests/verified')
    if not verified_dir.exists():
        logger.error("Verified tests directory not found!")
        return False
        
    all_valid = True
    test_files_found = False
    
    for test_file in verified_dir.rglob('*.py'):
        if test_file.name.startswith('test_'):
            test_files_found = True
            is_valid, error = validate_test_metadata(str(test_file))
            if not is_valid:
                logger.error(f"Invalid metadata in {test_file}:")
                logger.error(f"  {error}")
                all_valid = False
    
    if not test_files_found:
        logger.error("No test files found in the verified directory!")
        return False
        
    return all_valid

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='QuizMasterPro Test Runner')
    parser.add_argument('--mode', choices=['quick', 'full', 'ci', 'pre-release'],
                      default='quick', help='Test execution mode')
    args = parser.parse_args()

    # Validate environment
    if not validate_environment():
        sys.exit(2)

    # Validate test metadata
    logger.info("Validating test metadata...")
    if not validate_all_tests():
        sys.exit(2)

    # Check required services
    logger.info("Checking required services...")
    if not await check_services(args.mode):
        sys.exit(2)

    # Run tests
    logger.info(f"Starting test run in {args.mode} mode")
    runner = TestRunner()
    runner.mode = args.mode
    success = await runner.run_all()
    
    sys.exit(0 if success else 1)

def validate_environment() -> bool:
    """Validate that the test runner is being executed in the correct environment"""
    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'crewai-quizmaster-pro':
        logger.error(f"Incorrect conda environment. Expected 'crewai-quizmaster-pro', got '{conda_env}'")
        logger.error("Please run: conda activate crewai-quizmaster-pro")
        return False
    
    # Check working directory
    try:
        # Check if we're in the project root by looking for key directories and files
        required_items = {
            'directories': ['backend', 'frontend', 'tests'],
            'files': ['_start_backend.bat', '_start_frontend.bat']
        }
        current_dir = Path.cwd()
        
        missing_dirs = [d for d in required_items['directories'] if not (current_dir / d).exists()]
        missing_files = [f for f in required_items['files'] if not (current_dir / f).exists()]
        
        if missing_dirs or missing_files:
            if missing_dirs:
                logger.error(f"Missing directories: {missing_dirs}")
            if missing_files:
                logger.error(f"Missing files: {missing_files}")
            logger.error("Please run from the QuizMasterPro root directory")
            return False
    except Exception as e:
        logger.error(f"Error checking working directory: {e}")
        return False
    
    # Check required environment variables
    required_vars = [
        'TEST_MODE',
        'PYTHONPATH',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'TEST_DB_NAME',
        'API_HOST',
        'API_PORT'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set all required environment variables")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
