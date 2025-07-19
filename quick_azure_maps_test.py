import os
import asyncio
import sys

# Set telemetry to be explicitly disabled
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'

async def quick_test():
    """Quick test of Azure Maps functionality."""
    print("🔍 Quick Azure Maps Test")
    print("=" * 30)
    
    try:
        from operations.azure_maps_operations import AzureMapsOperations
        print("✅ Successfully imported AzureMapsOperations")
        
        # Check environment variables
        subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
        client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
        
        print(f"📋 Environment Configuration:")
        print(f"   • AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if subscription_key else '❌ Not set'}")
        print(f"   • AZURE_MAPS_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
        
        # Create instance
        azure_maps = AzureMapsOperations()
        print("✅ AzureMapsOperations instance created")
        
        # Test telemetry status
        status = azure_maps.get_telemetry_status()
        print(f"📊 Telemetry Status: {status}")
        
        # Clean up
        await azure_maps.close()
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
