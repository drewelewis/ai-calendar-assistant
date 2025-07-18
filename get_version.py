#!/usr/bin/env python3
"""
Version extractor utility
Extracts version from pyproject.toml for use in build scripts
"""

import re
import sys
from pathlib import Path

def get_version_from_pyproject():
    """Extract version from pyproject.toml"""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found", file=sys.stderr)
        sys.exit(1)
    
    content = pyproject_path.read_text(encoding='utf-8')
    
    # Look for version = "x.y.z" pattern
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    
    if not version_match:
        print("Error: Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    
    return version_match.group(1)

if __name__ == "__main__":
    version = get_version_from_pyproject()
    print(version, end='')  # No newline for use in batch files
