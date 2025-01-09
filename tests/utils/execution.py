"""
Test execution utilities
"""

import os
import time
import logging
import asyncio
import importlib.util
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

from .metadata import TestMetadata

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test execution result"""
    success: bool
    duration: float
    error: Optional[str] = None

class TestExecutor:
    """Test execution manager"""
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[str, TestResult] = {}

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

    def setup_python_path(self, working_dir: str) -> str:
        """Set up PYTHONPATH for the test"""
        if working_dir == 'backend':
            return os.path.join(self.project_root, 'backend')
        elif working_dir == 'frontend':
            return os.path.join(self.project_root, 'frontend')
        return str(self.project_root)

async def run_test(self, test_path: str, metadata: TestMetadata) -> TestResult:
    """Run a single test file"""
    # Validate working directory and required paths
    if not self.validate_working_directory(metadata):
        return TestResult(success=False, duration=0, error="Invalid working directory or required paths")
    
    start_time = time.time()
    try:
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
            logger.info(f"Attempting to import test module: {test_path}")
            spec = importlib.util.spec_from_file_location(
                "test_module",
                self.project_root / test_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load test module: {test_path}")
            
            module = importlib.util.module_from_spec(spec)
            logger.info(f"Executing test module: {test_path}")
            spec.loader.exec_module(module)
            
            # Run test_main function if it exists
            if hasattr(module, 'test_main'):
                logger.info(f"Running test_main function in {test_path}")
                await module.test_main()
            elif hasattr(module, 'test_auth'):
                logger.info(f"Running test_auth function in {test_path}")
                module.test_auth()
            else:
                logger.warning(f"No test_main or test_auth function found in {test_path}")
            
            duration = time.time() - start_time
            logger.info(f"Test {test_path} completed successfully in {duration:.2f} seconds")
            return TestResult(success=True, duration=duration)
            
        finally:
            # Restore original directory and PYTHONPATH
            os.chdir(original_dir)
            os.environ['PYTHONPATH'] = original_pythonpath
            
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error running test {test_path}: {e}")
        return TestResult(success=False, duration=duration, error=str(e))

    async def run_parallel_tests(self, test_paths: list[str], test_metadata: Dict[str, TestMetadata]) -> None:
        """Run multiple tests in parallel"""
        tasks = []
        for test_path in test_paths:
            metadata = test_metadata[test_path]
            if metadata.parallel_safe:
                task = asyncio.create_task(self.run_test(test_path, metadata))
                tasks.append((test_path, task))
            else:
                # Run non-parallel-safe tests sequentially
                result = await self.run_test(test_path, metadata)
                self.results[test_path] = result

        # Wait for parallel tests to complete
        for test_path, task in tasks:
            try:
                result = await task
                self.results[test_path] = result
            except Exception as e:
                logger.error(f"Error in parallel test {test_path}: {e}")
                self.results[test_path] = TestResult(success=False, duration=0, error=str(e))

    def get_results_summary(self) -> str:
        """Generate a summary of test results"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.success)
        total_duration = sum(result.duration for result in self.results.values())
        
        summary = [
            f"\nTest Results Summary",
            f"-------------------",
            f"Total Tests: {total_tests}",
            f"Passed Tests: {passed_tests}",
            f"Failed Tests: {total_tests - passed_tests}",
            f"Total Duration: {total_duration:.2f} seconds\n"
        ]
        
        if total_tests - passed_tests > 0:
            summary.append("Failed Tests:")
            for test_path, result in self.results.items():
                if not result.success:
                    summary.append(f"  - {test_path}")
                    if result.error:
                        summary.append(f"    Error: {result.error}")
        
        return "\n".join(summary)
