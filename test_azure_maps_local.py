#!/usr/bin/env python3
"""
Test Azure Maps Operations with telemetry disabled for local development.
This script demonstrates how to use TELEMETRY_EXPLICITLY_DISABLED for local testing.
"""

import os
import asyncio
import time

# Set the telemetry disable flag BEFORE importing azure_maps_operations
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'

# Now import azure_maps_operations - it will detect the flag and skip telemetry
from operations.azure_maps_operations import AzureMapsOperations

async def test_local_development():
    """Test Azure Maps operations in local development mode with telemetry disabled."""
    print("=" * 80)
    print("🧪 Testing Azure Maps Operations - Local Development Mode")
    print("   (Telemetry explicitly disabled for fast startup)")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # Create Azure Maps client
        print("\n📍 Initializing Azure Maps Operations...")
        maps_ops = AzureMapsOperations()
        
        # Check telemetry status
        telemetry_status = maps_ops.get_telemetry_status()
        print(f"\n📊 Telemetry Status:")
        for key, value in telemetry_status.items():
            print(f"   {key}: {value}")
        
        # Test connection (this will fail gracefully if no credentials)
        print(f"\n🔗 Testing connection...")
        async with maps_ops as client:
            connection_result = await client.test_connection()
            
            print(f"\n📋 Connection Test Results:")
            print(f"   Status: {connection_result.get('overall_status', 'unknown')}")
            print(f"   Duration: {connection_result.get('duration_seconds', 0):.3f}s")
            
            if connection_result.get('overall_status') == 'success':
                print(f"   Auth Method: {connection_result.get('auth_method', 'unknown')}")
                print(f"   Categories Found: {connection_result.get('categories_found', 0)}")
                print("   ✅ Connection successful!")
            else:
                print(f"   Error: {connection_result.get('error', 'Unknown error')}")
                print("   ❌ Connection failed (expected without credentials)")
                
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        total_time = time.time() - start_time
        print(f"\n⏱️  Total test time: {total_time:.3f} seconds")
        print("\n✅ Local development test completed!")

def test_environment_variable_usage():
    """Demonstrate different ways to set the DISABLE_TELEMETRY environment variable."""
    print("\n" + "=" * 80)
    print("📚 How to disable telemetry for local development:")
    print("=" * 80)
    
    methods = [
        {
            "method": "1. Environment Variable (Command Line)",
            "example": "set TELEMETRY_EXPLICITLY_DISABLED=true && python test_azure_maps_local.py",
            "description": "Set environment variable before running script"
        },
        {
            "method": "2. In Python Code (Before Import)",
            "example": "os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'",
            "description": "Set in code before importing azure_maps_operations"
        },
        {
            "method": "3. .env File",
            "example": "TELEMETRY_EXPLICITLY_DISABLED=true",
            "description": "Add to .env file in project root"
        },
        {
            "method": "4. VS Code Launch Configuration",
            "example": '{"env": {"TELEMETRY_EXPLICITLY_DISABLED": "true"}}',
            "description": "Add to VS Code launch.json configuration"
        }
    ]
    
    for method_info in methods:
        print(f"\n{method_info['method']}:")
        print(f"   Example: {method_info['example']}")
        print(f"   Description: {method_info['description']}")
    
    print(f"\n💡 Accepted values for TELEMETRY_EXPLICITLY_DISABLED:")
    print(f"   'true', '1', 'yes' (case insensitive)")
    
    print(f"\n🚀 Benefits of disabling telemetry for local development:")
    print(f"   - Faster startup (no telemetry module imports)")
    print(f"   - No hanging on import failures")
    print(f"   - Simplified output (fallback logging)")
    print(f"   - Better development experience")

if __name__ == "__main__":
    print("🔧 Azure Maps Operations - Local Development Test")
    
    # Show environment variable usage examples
    test_environment_variable_usage()
    
    # Run the actual test
    asyncio.run(test_local_development())
