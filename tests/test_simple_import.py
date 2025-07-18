#!/usr/bin/env python3
"""
Simple import test for Azure Maps operations
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Starting simple import test...")
print(f"Project root: {project_root}")
print(f"Operations path exists: {(project_root / 'operations').exists()}")

try:
    print("Attempting import...")
    from operations.azure_maps_operations import AzureMapsOperations
    print("✅ SUCCESS: Import completed")
    
    # Try to create instance (but don't initialize it)
    print("Creating instance...")
    maps_ops = AzureMapsOperations()
    print("✅ SUCCESS: Instance created")
    
    # Check if it has the methods we expect
    print("Checking methods...")
    if hasattr(maps_ops, 'test_connection'):
        print("✅ SUCCESS: test_connection method exists")
    if hasattr(maps_ops, 'get_telemetry_status'):
        print("✅ SUCCESS: get_telemetry_status method exists")
    
    print("\n🎉 All import tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Available modules in operations:")
    try:
        import operations
        import os
        ops_dir = os.path.dirname(operations.__file__) if hasattr(operations, '__file__') else project_root / 'operations'
        for f in os.listdir(ops_dir):
            if f.endswith('.py'):
                print(f"  - {f}")
    except:
        pass
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()
