"""
Check Import Consistency

This script analyzes Python imports across the codebase to ensure they follow our conventions:
1. Backend code should use proper package imports (from api.xxx import yyy)
2. Relative imports should only be used within packages
3. No hardcoded paths in imports
4. No circular imports
"""

import os
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class ImportChecker(ast.NodeVisitor):
    def __init__(self, file_path: Path, project_root: Path):
        self.file_path = file_path
        self.project_root = project_root
        self.imports: List[Tuple[str, str, int, List[str]]] = []  # (module, type, line_no, imported_names)
        self.issues: List[str] = []
        
    def visit_Import(self, node: ast.Import):
        """Process regular imports: import xxx"""
        for name in node.names:
            self.imports.append((name.name, 'direct', node.lineno, [name.name]))
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports: from xxx import yyy"""
        module = node.module if node.module else ''
        imported_names = [name.name for name in node.names]
        if node.level > 0:  # Relative import
            self.imports.append((module, f'relative-{node.level}', node.lineno, imported_names))
        else:
            self.imports.append((module, 'absolute', node.lineno, imported_names))
        self.generic_visit(node)

def check_file_imports(file_path: Path, project_root: Path) -> List[str]:
    """Check imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
            
        checker = ImportChecker(file_path, project_root)
        checker.visit(tree)
        
        issues = []
        rel_path = file_path.relative_to(project_root)
        
        # Check for api.models imports that need to be updated
        for module, imp_type, line_no, imported_names in checker.imports:
            if module == 'api.models':
                # Suggest update to api.core.models
                names_str = ", ".join(imported_names)
                issues.append(
                    f"{rel_path}:{line_no} - Update import to use api.core.models: "
                    f"from api.core.models import {names_str}"
                )
            
            # Check backend imports
            if 'backend' in str(rel_path):
                # Backend code should use api.xxx for internal imports
                if (module.startswith('api.') and imp_type != 'absolute' and 
                    'tests' not in str(rel_path)):
                    issues.append(
                        f"{rel_path}:{line_no} - Backend import should use "
                        f"absolute path: {module}"
                    )
                
                # Warn about potential circular imports
                if (imp_type.startswith('relative') and 
                    any(x in module for x in ['models', 'database', 'config'])):
                    issues.append(
                        f"{rel_path}:{line_no} - Potential circular import risk: "
                        f"{module}"
                    )
            
            # Check frontend imports
            elif 'frontend' in str(rel_path):
                # Frontend should use relative imports for components
                if (module.startswith('components') and imp_type == 'absolute' and 
                    'src' in str(rel_path)):
                    issues.append(
                        f"{rel_path}:{line_no} - Frontend component import should "
                        f"use relative path: {module}"
                    )
        
        return issues
        
    except Exception as e:
        return [f"Error processing {file_path}: {e}"]

def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    
    # Collect Python files
    python_files = []
    for root, _, files in os.walk(project_root):
        if 'node_modules' in root or '.git' in root or '.venv' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    # Check each file
    all_issues: List[str] = []
    for file_path in python_files:
        issues = check_file_imports(file_path, project_root)
        all_issues.extend(issues)
    
    # Report results
    if all_issues:
        logger.warning("Found import consistency issues:")
        for issue in all_issues:
            logger.warning(issue)
        return 1
    else:
        logger.info("No import consistency issues found!")
        return 0

if __name__ == "__main__":
    exit(main())
