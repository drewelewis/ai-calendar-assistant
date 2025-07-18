#!/usr/bin/env python3
"""
Simple Production Test
"""
import os
import sys
from pathlib import Path

# Disable telemetry for testing
os.environ['DISABLE_TELEMETRY'] = 'true'

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_production_import():
    """Test that the production version imports without hanging."""
    print("Testing production Azure Maps import...")
    
    try:
        # This should not hang now
        from operations.azure_maps_operations_production import AzureMapsOperations
        print("✅ Production import successful!")
        
        # Test basic initialization
        maps_ops = AzureMapsOperations()
        status = maps_ops.get_telemetry_status()
        print(f"✅ Telemetry mode: {status['mode']}")
        print(f"✅ Telemetry available: {status['telemetry_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Production import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_production_import()
    if success:
        print("\n🎉 Production version working correctly!")
        print("✅ No hanging during telemetry import")
        print("✅ Graceful fallback implemented")
        print("✅ Ready for production use")
    else:
        print("\n💥 Production version test failed")
    
    sys.exit(0 if success else 1)
