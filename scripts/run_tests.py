#!/usr/bin/env python
"""Test runner script with enhanced output and logging.

Usage:
    1. Activate the conda environment:
       ```
       conda activate crewai-quizmaster-pro
       ```

    2. Run all verified tests:
       ```
       python scripts/run_tests.py
       ```

    3. Run specific test file:
       ```
       python scripts/run_tests.py tests/verified/test_environment.py
       ```

    4. Run with options:
       ```
       python scripts/run_tests.py -v  # verbose output
       python scripts/run_tests.py -s  # show real-time output
       python scripts/run_tests.py -e development  # run against development environment
       ```

Note: Always run this script from the project root directory (QuizMasterPro/).
      The conda environment must be activated before running tests.
"""
import argparse
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command: list[str], cwd: str = None) -> subprocess.CompletedProcess:
    """Run a command and stream output."""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True
    )
    
    output_lines = []
    for line in process.stdout:
        output_lines.append(line)
        print(line.rstrip())
    
    process.wait()
    
    if process.returncode != 0:
        error = process.stderr.read()
        if error:
            print(f"Error: {error}")
    
    return subprocess.CompletedProcess(
        command,
        process.returncode,
        stdout=''.join(output_lines),
        stderr=process.stderr.read() if process.stderr else ''
    )

def print_test_summary(result: subprocess.CompletedProcess):
    """Print a formatted test summary."""
    output = result.stdout
    
    # Extract test summary
    summary_lines = [
        line for line in output.split('\n')
        if any(x in line.lower() for x in ['failed', 'passed', 'skipped', 'error'])
    ]
    
    if summary_lines:
        print("\nTest Summary:")
        print("-" * 40)
        for line in summary_lines:
            print(line)
        print("-" * 40)

def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="QuizMasterPro Test Runner")
    parser.add_argument(
        "test_path",
        help="Test path to run (file or directory)",
        nargs='?',
        default="tests/verified"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    parser.add_argument(
        "-s", "--show-output",
        action="store_true",
        help="Show test output in real-time"
    )
    parser.add_argument(
        "-e", "--environment",
        choices=["test", "development"],
        default="test",
        help="Environment to run tests against"
    )
    args = parser.parse_args()

    try:
        print("Setting up test environment...")
        
        # Project root directory
        root_dir = Path(__file__).parent.parent
        
        # Load environment variables from .env file
        env_file = root_dir / "backend" / f".env.{args.environment}"
        if env_file.exists():
            print(f"Loading environment variables from {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        os.environ[key] = value
        
        # Set environment variables
        os.environ["QUIZMASTER_ENVIRONMENT"] = args.environment
        os.environ["TEST_MODE"] = "true"
        os.environ["NODE_ENV"] = "test"
        os.environ["PYTHONPATH"] = str(root_dir / "backend")

        # Prepare pytest command
        pytest_args = ["pytest"]
        if args.verbose:
            pytest_args.append("-v")
        if args.show_output:
            pytest_args.append("-s")

        # Add test path
        pytest_args.append(args.test_path)

        print(f"Running tests from {args.test_path}...")
        
        # Run tests
        start_time = time.time()
        result = run_command(pytest_args)
        duration = time.time() - start_time

        # Print results
        print_test_summary(result)
        print(f"\nTest duration: {duration:.2f} seconds")

        if result.returncode != 0:
            sys.exit(result.returncode)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
