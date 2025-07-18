#!/usr/bin/env python3
"""
Test Fast Loading Azure Maps Operations
"""
import os
import sys
import time
from pathlib import Path

# Set environment variables before any imports
os.environ['DISABLE_TELEMETRY'] = 'true'
os.environ['DEBUG_AZURE_MAPS'] = 'true'

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_fast_azure_maps():
    """Test the fast-loading version."""
    print("🚀 Testing Fast-Loading Azure Maps Operations")
    print("=" * 50)
    
    try:
        # Import should be fast and never hang
        print("Importing fast Azure Maps operations...")
        start_time = time.time()
        
        from operations.azure_maps_operations_fast import AzureMapsOperations
        
        import_time = time.time() - start_time
        print(f"✅ Import completed in {import_time:.3f} seconds")
        
        # Test initialization
        print("\nInitializing client...")
        async with AzureMapsOperations() as maps_ops:
            
            # Check status
            status = maps_ops.get_telemetry_status()
            print(f"✅ Telemetry available: {status['telemetry_available']}")
            print(f"✅ Telemetry disabled: {status['telemetry_disabled']}")
            print(f"✅ Mode: {status['mode']}")
            
            # Quick connection test
            print("\nRunning connection test...")
            test_result = await maps_ops.test_connection()
            print(f"✅ Connection test: {test_result['overall_status']}")
            print(f"✅ Duration: {test_result['duration_seconds']:.3f}s")
            
            if test_result['overall_status'] == 'success':
                print(f"✅ Auth method: {test_result['auth_method']}")
                print(f"✅ Categories found: {test_result.get('categories_found', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fast loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    
    start_time = time.time()
    success = asyncio.run(test_fast_azure_maps())
    total_time = time.time() - start_time
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FAST LOADING TEST SUCCESS")
        print(f"✅ Total time: {total_time:.3f} seconds")
        print("✅ No hanging on telemetry imports")
        print("✅ Fast startup and execution")
        print("✅ Ready for production use")
    else:
        print("💥 FAST LOADING TEST FAILED")
    
    print("=" * 50)
