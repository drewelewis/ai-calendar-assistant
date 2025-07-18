#!/usr/bin/env python3
"""
Minimal test to find the hanging issue
"""

print("Starting minimal test...")

try:
    print("Testing basic imports...")
    import os
    print("✅ os imported")
    
    import sys  
    print("✅ sys imported")
    
    from datetime import datetime
    print("✅ datetime imported")
    
    from typing import Optional, Dict, Any
    print("✅ typing imported")
    
    from enum import Enum
    print("✅ enum imported")
    
    print("Testing environment variable access...")
    test_env = os.getenv('TELEMETRY_CONSOLE_LEVEL', 'INFO')
    print(f"✅ Environment access works: {test_env}")
    
    print("Testing class definition...")
    from telemetry.console_output import ConsoleLevel
    print("✅ ConsoleLevel imported")
    
    print("Testing TelemetryConsole class...")
    from telemetry.console_output import TelemetryConsole
    print("✅ TelemetryConsole imported")
    
    print("Testing TelemetryConsole instantiation...")
    console = TelemetryConsole()
    print("✅ TelemetryConsole instantiated")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
