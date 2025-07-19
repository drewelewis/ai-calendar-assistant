#!/usr/bin/env python3
"""
Test Managed Identity with Enhanced Debugging

This script temporarily removes the subscription key to force managed identity testing.
"""

import asyncio
import os
import sys

# Temporarily disable subscription key to force managed identity
os.environ['AZURE_MAPS_SUBSCRIPTION_KEY'] = ''
# Disable telemetry to avoid hangs
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'

async def test_managed_identity_with_debug():
    """Test managed identity with enhanced debugging."""
    print("🧪 Testing Managed Identity with Enhanced Debug Logging")
    print("=" * 60)
    print("Managed Identity: 5238e629-da2f-4bb0-aea5-14d45526c864")
    print("Subscription Key: DISABLED (forced managed identity test)")
    print()
    
    try:
        from operations.azure_maps_operations import AzureMapsOperations
        
        async with AzureMapsOperations() as azure_maps:
            print("✅ AzureMapsOperations initialized")
            
            # Test connection first
            print("\n🔗 Testing Connection...")
            connection_result = await azure_maps.test_connection()
            
            print(f"\n📊 Connection Test Result:")
            print(f"   • Status: {connection_result.get('overall_status', 'unknown')}")
            if 'auth_method' in connection_result:
                print(f"   • Auth method: {connection_result['auth_method']}")
            if 'error' in connection_result:
                print(f"   • Error: {connection_result['error']}")
            if 'status_code' in connection_result:
                print(f"   • HTTP Status: {connection_result['status_code']}")
            
            # Test geocoding if connection works
            if connection_result.get("overall_status") == "success":
                print(f"\n📍 Testing Geocoding...")
                result = await azure_maps.geolocate_city_state("Charlotte", "NC")
                
                if result:
                    print("✅ Geocoding successful!")
                    features = result.get('features', [])
                    if features:
                        coords = features[0].get('geometry', {}).get('coordinates', [])
                        if len(coords) >= 2:
                            print(f"   • Coordinates: {coords[1]:.6f}, {coords[0]:.6f}")
                        address = features[0].get('properties', {}).get('address', {})
                        print(f"   • Address: {address.get('formattedAddress', 'N/A')}")
                else:
                    print("❌ Geocoding failed")
            else:
                print(f"\n⚠️ Skipping geocoding test due to connection failure")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function."""
    await test_managed_identity_with_debug()
    
    print(f"\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print("This test forced managed identity by disabling the subscription key.")
    print("The detailed debug logs above show:")
    print("  • Environment variable checks")
    print("  • Token acquisition attempts")
    print("  • API request details")
    print("  • Specific error messages")
    print("")
    print("If you see environment variables missing (MSI_ENDPOINT, etc.),")
    print("it confirms you're running locally, not in Azure Container App.")
    print("")
    print("Deploy this to Azure Container App to see managed identity work!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🚫 Test cancelled")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
