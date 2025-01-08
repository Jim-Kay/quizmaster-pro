"""
Test metadata handling utilities
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

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

def extract_metadata(file_path: str) -> Optional[TestMetadata]:
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

def validate_metadata(file_path: str) -> tuple[bool, str]:
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
        
        # Check for Test Metadata section
        if 'Test Metadata:' not in docstring:
            return False, "No 'Test Metadata:' section found"
        
        metadata_section = docstring.split('Test Metadata:')[1].split('\n\n')[0]
        
        # Required fields
        required_fields = [
            ('Level', r'Level:\s*(\d+)'),
            ('Dependencies', r'Dependencies:\s*\[(.*?)\]'),
            ('Blocking', r'Blocking:\s*(True|False)'),
            ('Parallel_Safe', r'Parallel_Safe:\s*(True|False)'),
            ('Estimated_Duration', r'Estimated_Duration:\s*(\d+)'),
            ('Working_Directory', r'Working_Directory:\s*(\w+)'),
            ('Required_Paths', r'Required_Paths:\s*\n(?:\s*-.*\n)*')
        ]
        
        for field_name, pattern in required_fields:
            if not re.search(pattern, metadata_section):
                return False, f"Missing or invalid {field_name} field"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error validating metadata: {str(e)}"
