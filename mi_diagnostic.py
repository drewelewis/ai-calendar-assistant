#!/usr/bin/env python3
"""
Managed Identity Diagnostic for Azure Container App

Specifically tests managed identity: 5238e629-da2f-4bb0-aea5-14d45526c864
This script helps debug why managed identity isn't working.
"""

import asyncio
import os
import sys

# Disable telemetry to avoid hangs
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'

async def main():
    """Main diagnostic function."""
    print("🔍 Managed Identity Diagnostic")
    print("=" * 40)
    print("Identity: 5238e629-da2f-4bb0-aea5-14d45526c864")
    print()
    
    # Environment check
    print("🏗️ Environment Check:")
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    client_id = os.environ.get("AZURE_MAPS_CLIENT_ID") 
    msi_endpoint = os.environ.get("MSI_ENDPOINT")
    identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
    
    print(f"   • Subscription Key: {'✅ Set' if subscription_key else '❌ Not set'}")
    print(f"   • Client ID: {'✅ Set' if client_id else '❌ Not set'}")
    print(f"   • MSI Endpoint: {'✅ Set' if msi_endpoint else '❌ Not set'}")
    print(f"   • Identity Endpoint: {'✅ Set' if identity_endpoint else '❌ Not set'}")
    
    if not (msi_endpoint or identity_endpoint):
        print("\n❌ Not running in Azure Container App")
        print("💡 Managed identity only works inside Azure Container App")
        print("   • Deploy this script to your Container App")
        print("   • Remove AZURE_MAPS_SUBSCRIPTION_KEY environment variable")
        print("   • Test again in the Azure environment")
        return
    
    print("\n✅ Running in Azure Container App environment")
    
    # Package check
    print("\n📦 Package Check:")
    try:
        from azure.identity import DefaultAzureCredential
        import aiohttp
        print("   ✅ Required packages available")
    except ImportError as e:
        print(f"   ❌ Missing package: {e}")
        return
    
    # Token test
    print("\n🎫 Testing Token Acquisition:")
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://atlas.microsoft.com/.default")
        
        if token and token.token:
            print("   ✅ Token acquired successfully")
            print(f"   • Length: {len(token.token)} chars")
            access_token = token.token
        else:
            print("   ❌ No token returned")
            return
            
    except Exception as e:
        print(f"   ❌ Token failed: {e}")
        print("   🔧 Check:")
        print("      • Managed identity is enabled")
        print("      • Container App was restarted")
        print("      • Roles are assigned")
        return
    
    # API test
    print("\n🗺️ Testing Azure Maps API:")
    try:
        url = "https://atlas.microsoft.com/search/address/json"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'api-version': '1.0', 'query': 'Seattle, WA', 'limit': 1}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                print(f"   • Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("   ✅ SUCCESS: Managed identity works!")
                    print(f"   • Results: {len(result.get('results', []))}")
                    
                elif response.status == 401:
                    print("   ❌ Authentication failed")
                    print("   🔧 Token issue - check identity configuration")
                    
                elif response.status == 403:
                    print("   ❌ Permission denied")
                    print("   🔧 Check role assignments:")
                    print("      • Azure Maps Data Reader role")
                    print("      • Role scope includes Azure Maps account")
                    print(f"      • Identity: 5238e629-da2f-4bb0-aea5-14d45526c864")
                    
                else:
                    text = await response.text()
                    print(f"   ❌ Unexpected: {text[:100]}")
                    
    except Exception as e:
        print(f"   ❌ API test failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
