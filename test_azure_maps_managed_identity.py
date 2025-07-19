#!/usr/bin/env python3
"""
Azure Maps Managed Identity Diagnostic Tool

This script helps diagnose Azure Maps configuration issues,
particularly with managed identity authentication in Azure deployments.

Usage:
    python test_azure_maps_managed_identity.py
"""

import asyncio
import os
import sys
from operations.azure_maps_operations import AzureMapsOperations

async def main():
    """Main diagnostic function."""
    print("🔍 Azure Maps Managed Identity Diagnostic Tool")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Configuration:")
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    
    print(f"   • AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if subscription_key else '❌ Not set'}")
    print(f"   • AZURE_MAPS_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
    
    # Initialize Azure Maps client
    print("\n🗺️ Initializing Azure Maps Operations...")
    try:
        async with AzureMapsOperations() as azure_maps:
            
            # Run comprehensive diagnosis
            print("\n🔍 Running Azure Maps Setup Diagnosis...")
            diagnosis = await azure_maps.diagnose_azure_maps_setup()
            
            # Test connection
            print("\n🔗 Testing Azure Maps Connection...")
            connection_result = await azure_maps.test_connection()
            
            if connection_result.get("overall_status") == "success":
                print("✅ Connection test successful!")
                print(f"   • Authentication: {connection_result.get('auth_method')}")
                print(f"   • Duration: {connection_result.get('duration_seconds', 0):.3f}s")
                print(f"   • Results found: {connection_result.get('results_found', 0)}")
            else:
                print("❌ Connection test failed!")
                print(f"   • Status: {connection_result.get('overall_status')}")
                if 'error' in connection_result:
                    print(f"   • Error: {connection_result['error']}")
                if 'status_code' in connection_result:
                    print(f"   • HTTP Status: {connection_result['status_code']}")
            
            # Test geocoding if connection works
            if connection_result.get("overall_status") == "success":
                print("\n📍 Testing Geocoding Function...")
                try:
                    result = await azure_maps.geolocate_city_state("Charlotte", "NC")
                    if result:
                        print("✅ Geocoding test successful!")
                        features = result.get('features', [])
                        if features:
                            coords = features[0].get('geometry', {}).get('coordinates', [])
                            if len(coords) >= 2:
                                print(f"   • Coordinates: {coords[1]:.6f}, {coords[0]:.6f}")
                            address = features[0].get('properties', {}).get('address', {})
                            print(f"   • Address: {address.get('formattedAddress', 'N/A')}")
                    else:
                        print("❌ Geocoding test failed - no results returned")
                except Exception as e:
                    print(f"❌ Geocoding test failed: {e}")
            
            # Summary and recommendations
            print("\n📊 Diagnosis Summary:")
            print("=" * 30)
            
            if diagnosis.get("subscription_key_available"):
                print("✅ Using subscription key authentication (recommended for development)")
            elif diagnosis.get("managed_identity_test", {}).get("status") == "success":
                print("✅ Managed identity authentication working")
            else:
                print("❌ Authentication issues detected")
                print("\n💡 Recommendations:")
                for rec in diagnosis.get("recommendations", []):
                    print(f"   • {rec}")
                
                print("\n🔧 Azure Setup Steps:")
                print("   1. Enable system-assigned managed identity on your Azure resource")
                print("   2. In Azure Maps account, go to Access Control (IAM)")
                print("   3. Add role assignment: 'Azure Maps Data Reader'")
                print("   4. Assign to your resource's managed identity")
                print("   5. Restart your Azure service")
                
    except Exception as e:
        print(f"❌ Failed to initialize Azure Maps: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Check that azure-identity and aiohttp packages are installed")
        print("   • Verify Azure Maps account is created and active")
        print("   • Ensure network connectivity to atlas.microsoft.com")

if __name__ == "__main__":
    print("Starting Azure Maps diagnostic...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🚫 Diagnostic cancelled by user")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        sys.exit(1)
