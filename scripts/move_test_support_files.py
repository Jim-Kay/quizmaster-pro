#!/usr/bin/env python
"""
Script to move test support files to the new uncategorized structure
"""

import os
import shutil
from pathlib import Path

def create_uncategorized_structure():
    """Create the uncategorized directory structure"""
    base_dir = Path("tests/uncategorized")
    directories = [
        "config",
        "data",
        "requirements",
        "logs"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

def move_support_files():
    """Move support files to their new locations"""
    # Define file mappings (source -> destination)
    file_mappings = {
        # Config files
        "backend/tests/conftest.py": "tests/uncategorized/config/backend_conftest.py",
        
        # Requirements files
        "backend/tests/requirements-test.txt": "tests/uncategorized/requirements/backend-requirements-test.txt",
        
        # Data files
        "backend/tests/sample_blueprint_full.json": "tests/uncategorized/data/sample_blueprint_full.json",
        "backend/tests/sample_blueprint_partial.json": "tests/uncategorized/data/sample_blueprint_partial.json",
        
        # Integration tests
        "backend/tests/manual_test.py": "tests/integration/api/manual_integration_test.py",
    }
    
    # Directory mappings (source -> destination)
    dir_mappings = {
        "backend/tests/data": "tests/uncategorized/data/backend",
        "backend/tests/logs": "tests/uncategorized/logs/backend",
    }
    
    # Move individual files
    for src, dst in file_mappings.items():
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            os.remove(src)
            print(f"Moved {src} to {dst}")
    
    # Move directories
    for src, dst in dir_mappings.items():
        if os.path.exists(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
            shutil.rmtree(src)
            print(f"Moved directory {src} to {dst}")

def cleanup_empty_dirs():
    """Remove empty test directories"""
    test_dirs = [
        "backend/tests",
        "frontend/tests",
        "backend/api/tests"
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                # Remove empty directories recursively
                for root, dirs, files in os.walk(test_dir, topdown=False):
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except OSError:
                            pass  # Directory not empty
                
                # Try to remove the main test directory
                os.rmdir(test_dir)
                print(f"Removed empty directory: {test_dir}")
            except OSError:
                print(f"Directory not empty, skipping: {test_dir}")

def update_test_references():
    """Create a README explaining the new file locations"""
    readme_content = """# Test Support Files Migration

The test support files have been reorganized into the following structure:

- /tests/uncategorized/config/: Configuration files
  - backend_conftest.py (moved from backend/tests/conftest.py)

- /tests/uncategorized/data/: Test data files
  - sample_blueprint_full.json
  - sample_blueprint_partial.json
  - backend/ (contents from backend/tests/data/)

- /tests/uncategorized/requirements/: Test requirements
  - backend-requirements-test.txt

- /tests/uncategorized/logs/: Test logs
  - backend/ (contents from backend/tests/logs/)

Note: You may need to update import paths in your test files to reflect these new locations.
"""
    
    with open("tests/uncategorized/README.md", "w") as f:
        f.write(readme_content)

def main():
    print("Creating uncategorized structure...")
    create_uncategorized_structure()
    
    print("\nMoving support files...")
    move_support_files()
    
    print("\nCleaning up empty directories...")
    cleanup_empty_dirs()
    
    print("\nCreating documentation...")
    update_test_references()
    
    print("\nMigration complete!")

if __name__ == "__main__":
    main()
