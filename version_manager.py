#!/usr/bin/env python3
"""
Version increment utility
Automatically increments the minor version in pyproject.toml
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def increment_minor_version():
    """Increment the minor version in pyproject.toml"""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found", file=sys.stderr)
        sys.exit(1)
    
    # Read the current content
    content = pyproject_path.read_text(encoding='utf-8')
    
    # Find the version line in [project] section
    version_pattern = r'(version\s*=\s*["\'])(\d+)\.(\d+)\.(\d+)(["\'])'
    version_match = re.search(version_pattern, content)
    
    if not version_match:
        print("Error: Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    
    # Extract version components
    prefix = version_match.group(1)  # 'version = "'
    major = int(version_match.group(2))
    minor = int(version_match.group(3))
    patch = int(version_match.group(4))
    suffix = version_match.group(5)  # '"'
    
    # Increment minor version and reset patch to 0
    new_minor = minor + 1
    new_patch = 0
    new_version = f"{major}.{new_minor}.{new_patch}"
    
    # Replace the version in [project] section
    new_version_line = f"{prefix}{new_version}{suffix}"
    new_content = re.sub(version_pattern, new_version_line, content, count=1)
    
    # Also update the version in [tool.ai-calendar-assistant] section if it exists
    tool_version_pattern = r'(\[tool\.ai-calendar-assistant\][\s\S]*?version\s*=\s*["\'])(\d+)\.(\d+)\.(\d+)(["\'])'
    tool_match = re.search(tool_version_pattern, new_content)
    
    if tool_match:
        tool_prefix = tool_match.group(1)
        tool_suffix = tool_match.group(5)
        new_tool_version_line = f"{tool_prefix}{new_version}{tool_suffix}"
        new_content = re.sub(tool_version_pattern, new_tool_version_line, new_content)
    
    # Update release date in [tool.ai-calendar-assistant] section
    today = datetime.now().strftime("%Y-%m-%d")
    release_date_pattern = r'(release_date\s*=\s*["\'])[^"\']+(["\'])'
    new_content = re.sub(release_date_pattern, f'\\g<1>{today}\\g<2>', new_content)
    
    # Write back to file
    pyproject_path.write_text(new_content, encoding='utf-8')
    
    print(f"✅ Version incremented to {new_version}")
    print(f"📅 Release date updated to {today}")
    
    return new_version

def get_current_version():
    """Get the current version from pyproject.toml"""
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Version management utility')
    parser.add_argument('action', choices=['increment', 'get'], 
                       help='Action to perform: increment or get current version')
    
    args = parser.parse_args()
    
    if args.action == 'increment':
        new_version = increment_minor_version()
        print(new_version, end='')  # Output for batch file capture
    elif args.action == 'get':
        current_version = get_current_version()
        print(current_version, end='')  # Output for batch file capture
