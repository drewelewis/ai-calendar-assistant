#!/usr/bin/env python3
import sys
from pathlib import Path

print("Step 1: Setting up path")
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

print("Step 2: Testing import")
try:
    from operations.azure_maps_operations import AzureMapsOperations
    print("SUCCESS: Import worked!")
    
    print("Step 3: Creating instance")
    maps = AzureMapsOperations()
    print("SUCCESS: Instance created!")
    
    print("Step 4: Testing methods")
    status = maps.get_telemetry_status()
    print(f"SUCCESS: Telemetry status: {status}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("Test completed!")
