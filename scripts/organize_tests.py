#!/usr/bin/env python
"""
Test Organization Script
Helps reorganize tests into the new structure defined in TEST_PLAN.md
"""

import os
import shutil
from pathlib import Path

def create_test_structure():
    """Create the new test directory structure"""
    base_dir = Path("tests")
    directories = [
        "unit/backend",
        "unit/frontend",
        "integration/api",
        "integration/flows",
        "integration/e2e",
        "verified/unit",
        "verified/integration",
        "verified/documentation"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        (full_path / "__init__.py").touch()

def is_pytest_file(file_path):
    """Check if a file uses pytest"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        return 'pytest' in content or 'def test_' in content

def add_test_header_template(file_path):
    """Add the standard test header template to a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    header_template = '''"""
Test Name: {name}
Description: [TODO: Add test description]

Environment:
    - Conda Environment: quiz_master_backend
    - Working Directory: {working_dir}
    - Required Services: [TODO: List required services]

Setup:
    1. [TODO: Add setup steps]

Execution:
    [TODO: Add execution command]

Expected Results:
    [TODO: Add expected results]
"""

'''
    name = os.path.basename(file_path).replace('.py', '')
    working_dir = os.path.dirname(file_path)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header_template.format(
            name=name,
            working_dir=working_dir
        ) + content)

def cleanup_original_tests():
    """Remove original test files and empty test directories"""
    test_directories = [
        "backend/tests",
        "frontend/tests",
        "backend/api/tests"
    ]
    
    for test_dir in test_directories:
        if not os.path.exists(test_dir):
            continue
            
        # Remove test files
        for root, dirs, files in os.walk(test_dir, topdown=False):
            for file in files:
                if 'test_' in file or file.endswith('.spec.ts'):
                    os.remove(os.path.join(root, file))
            
            # Remove empty directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    os.rmdir(dir_path)  # This will only remove empty directories
                except OSError:
                    pass  # Directory not empty, skip it
        
        # Try to remove the main test directory if empty
        try:
            os.rmdir(test_dir)
        except OSError:
            pass  # Directory not empty, skip it

def main():
    # Create new structure
    create_test_structure()
    
    # Process existing test files
    test_directories = [
        "backend/tests",
        "frontend/tests",
        "backend/api/tests"
    ]
    
    for test_dir in test_directories:
        if not os.path.exists(test_dir):
            continue
            
        for root, _, files in os.walk(test_dir):
            for file in files:
                if (file.endswith('.py') and 'test_' in file) or file.endswith('.spec.ts'):
                    src_path = os.path.join(root, file)
                    
                    # Determine destination based on pytest usage and file type
                    if file.endswith('.spec.ts'):
                        dest_dir = "tests/unit/frontend"
                    elif is_pytest_file(src_path):
                        dest_dir = "tests/unit/backend"
                    else:
                        dest_dir = "tests/integration/api"
                    
                    # Copy file to new location
                    dest_path = os.path.join(dest_dir, file)
                    shutil.copy2(src_path, dest_path)
                    
                    # Add header template
                    if file.endswith('.py'):  # Only add header to Python files
                        add_test_header_template(dest_path)
    
    # Clean up original test files and directories
    cleanup_original_tests()

if __name__ == "__main__":
    main()
