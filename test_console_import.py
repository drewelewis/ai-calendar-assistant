#!/usr/bin/env python3
"""
Test script to isolate the console_error import issue
"""

print("Testing console_error import...")

try:
    print("Step 1: Testing basic module import...")
    import telemetry.console_output as console_module
    print("✅ Module import successful")
    
    print("Step 2: Checking if console_error exists in module...")
    if hasattr(console_module, 'console_error'):
        print("✅ console_error found in module")
    else:
        print("❌ console_error NOT found in module")
        print("Available functions:", [name for name in dir(console_module) if name.startswith('console_')])
    
    print("Step 3: Testing direct import...")
    from telemetry.console_output import console_error
    print("✅ Direct import successful")
    
    print("Step 4: Testing function call...")
    console_error("Test error message", "TestModule")
    print("✅ Function call successful")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except NameError as e:
    print(f"❌ Name error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")
