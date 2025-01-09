"""
Test discovery and dependency management utilities
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .metadata import TestMetadata, extract_metadata, validate_metadata

logger = logging.getLogger(__name__)

def normalize_path(path: str) -> str:
    """Normalize path to use forward slashes and lowercase drive letters"""
    normalized = str(Path(path)).replace('\\', '/')
    if len(normalized) > 1 and normalized[1] == ':':
        return normalized[0].lower() + normalized[1:]
    return normalized

def discover_tests(project_root: Path) -> Dict[str, TestMetadata]:
    """Discover all test files and their metadata"""
    logger.info("Discovering tests...")
    verified_dir = project_root / 'tests/verified'
    tests: Dict[str, TestMetadata] = {}
    
    if not verified_dir.exists():
        logger.error("Verified tests directory not found!")
        return tests
    
    test_files_found = False
    for test_file in verified_dir.rglob('*.py'):
        if test_file.name.startswith('test_'):
            test_files_found = True
            test_path = normalize_path(str(test_file))
            is_valid, error = validate_metadata(test_path)
            if not is_valid:
                logger.error(f"Invalid metadata in {test_path}:")
                logger.error(f"  {error}")
                raise ValueError(f"Test file {test_path} has invalid metadata: {error}")
            
            metadata = extract_metadata(test_path)
            if metadata:
                tests[test_path] = metadata
    
    if not test_files_found:
        logger.error("No test files found in the verified directory!")
        raise ValueError("No test files found in the verified directory!")
    
    logger.info(f"Discovered {len(tests)} test files")
    return tests

def validate_dependencies(tests: Dict[str, TestMetadata]) -> bool:
    """Validate that all test dependencies exist"""
    all_tests = set(normalize_path(test) for test in tests.keys())
    for test, metadata in tests.items():
        for dep in metadata.dependencies:
            if dep:
                normalized_dep = normalize_path(dep)
                if normalized_dep not in all_tests:
                    logger.error(f"Missing dependency {dep} for test {test}")
                    return False
    return True

def detect_cycles(tests: Dict[str, TestMetadata]) -> List[List[str]]:
    """Detect cycles in test dependencies"""
    def find_cycles(node: str, visited: Set[str], path: List[str]) -> List[List[str]]:
        if node in visited:
            cycle_start = path.index(node)
            return [path[cycle_start:]]
        cycles = []
        visited.add(node)
        path.append(node)
        for dep in tests[node].dependencies:
            if dep:
                normalized_dep = normalize_path(dep)
                cycles.extend(find_cycles(normalized_dep, visited.copy(), path.copy()))
        return cycles

    cycles = []
    for test in tests:
        cycles.extend(find_cycles(test, set(), []))
    return cycles

def group_tests_by_level(tests: Dict[str, TestMetadata]) -> Dict[int, List[str]]:
    """Group tests by their level"""
    levels: Dict[int, List[str]] = {}
    for test, metadata in tests.items():
        if metadata.level not in levels:
            levels[metadata.level] = []
        levels[metadata.level].append(test)
    return levels
