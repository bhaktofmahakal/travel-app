#!/usr/bin/env python
"""
Script to check for unused imports in Django project
"""

import os
import re
import ast
import sys

def get_imports_from_file(filepath):
    """Extract imports from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    imports.append(alias.name)
        
        return imports, content
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return [], ""

def check_usage(import_name, content):
    """Check if import is used in the content"""
    # Simple regex check - not perfect but covers most cases
    patterns = [
        rf'\b{re.escape(import_name)}\s*\(',  # Function calls
        rf'\b{re.escape(import_name)}\s*\.',  # Attribute access
        rf'\b{re.escape(import_name)}\s*\[',  # Index access
        rf'class.*\({import_name}\)',  # Inheritance
        rf'isinstance.*{re.escape(import_name)}',  # isinstance checks
        rf'except\s+{re.escape(import_name)}',  # Exception handling
    ]
    
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False

def scan_directory(directory):
    """Scan directory for Python files and check imports"""
    unused_imports = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        if any(skip in root for skip in ['__pycache__', '.git', 'migrations', 'venv', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)
                imports, content = get_imports_from_file(filepath)
                
                file_unused = []
                for imp in imports:
                    if not check_usage(imp, content):
                        file_unused.append(imp)
                
                if file_unused:
                    unused_imports[filepath] = file_unused
    
    return unused_imports

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    unused = scan_directory(project_dir)
    
    if unused:
        print("Potentially unused imports found:")
        print("=" * 50)
        for filepath, imports in unused.items():
            print(f"\n{filepath}:")
            for imp in imports:
                print(f"  - {imp}")
    else:
        print("No obvious unused imports found!")