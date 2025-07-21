#!/usr/bin/env python3
"""
Test Azure Maps authentication with x-ms-client-id header fix.
This script tests the critical fix for Azure Maps 401 errors.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_azure_maps_authentication():
    """Test Azure Maps authentication with the x-ms-client-id header fix."""
    print("🧪 Testing Azure Maps authentication fix...")
    print("=" * 60)
    
    # Check environment variables
    azure_maps_client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    azure_maps_subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    print("📋 Environment Variables Check:")
    print(f"   • AZURE_MAPS_CLIENT_ID: {'✅ Set' if azure_maps_client_id else '❌ Not set'}")
    if azure_maps_client_id:
        print(f"     Value: {azure_maps_client_id}")
    print(f"   • AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if azure_maps_subscription_key else '❌ Not set'}")
    print()
    
    # Import and test Azure Maps operations
    try:
        from operations.azure_maps_operations import AzureMapsOperations
        
        print("🔧 Creating AzureMapsOperations instance...")
        azure_maps = AzureMapsOperations()
        
        print(f"   • Subscription Key Available: {bool(azure_maps.subscription_key)}")
        print(f"   • Client ID Available: {bool(azure_maps.client_id)}")
        if azure_maps.client_id:
            print(f"   • Client ID Value: {azure_maps.client_id}")
        print()
        
        # Test geocoding (this should now include the x-ms-client-id header)
        print("🌍 Testing geocoding with authentication fix...")
        print("   Testing: Seattle, WA")
        
        result = await azure_maps.geocode_city_state("Seattle", "WA")
        
        if result:
            print("✅ SUCCESS: Geocoding completed successfully!")
            print(f"   • Latitude: {result.get('lat', 'N/A')}")
            print(f"   • Longitude: {result.get('lon', 'N/A')}")
            print(f"   • Address: {result.get('address', 'N/A')}")
        else:
            print("❌ FAILED: Geocoding returned no results")
            print("   This could indicate 401 authentication issues")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        print("📋 Full traceback:")
        traceback.print_exc()
    
    print()
    print("🔍 Fix Summary:")
    print("   The x-ms-client-id header has been added to all Azure Maps API calls")
    print("   This header is required for managed identity authentication")
    print("   It should resolve 401 authentication errors in Azure deployment")
    print()

if __name__ == "__main__":
    asyncio.run(test_azure_maps_authentication())
