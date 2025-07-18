#!/usr/bin/env python3
"""
Quick path diagnostic script to check project structure
"""

import sys
from pathlib import Path

print("=== Path Diagnostics ===")
print(f"Current file: {__file__}")
print(f"Current file parent: {Path(__file__).parent}")
print(f"Project root (parent.parent): {Path(__file__).parent.parent}")

# Check what's in the project root
project_root = Path(__file__).parent.parent
print(f"\nContents of project root ({project_root}):")
for item in sorted(project_root.iterdir()):
    if item.is_dir():
        print(f"  📁 {item.name}/")
    else:
        print(f"  📄 {item.name}")

# Check for operations folder specifically
operations_path = project_root / "operations"
print(f"\nOperations folder exists: {operations_path.exists()}")
if operations_path.exists():
    print("Contents of operations folder:")
    for item in sorted(operations_path.iterdir()):
        print(f"  📄 {item.name}")

# Check if we can import
sys.path.insert(0, str(project_root))
try:
    from operations.azure_maps_operations import AzureMapsOperations
    print("\n✅ Import successful!")
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    print(f"sys.path: {sys.path}")
