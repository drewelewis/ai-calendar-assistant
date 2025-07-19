#!/usr/bin/env python3
"""
Test Managed Identity Access to Azure Maps

This script specifically tests if your managed identity with the assigned permissions
can successfully access Azure Maps APIs.
"""

import asyncio
import os
import sys

async def test_managed_identity_azure_maps():
    """Test managed identity access to Azure Maps."""
    print("🔍 Testing Managed Identity Access to Azure Maps")
    print("=" * 55)
    
    # Check if we're in an Azure environment
    print("\n🏗️ Environment Check:")
    
    # Check for Azure Container App managed identity indicators
    msi_endpoint = os.environ.get("MSI_ENDPOINT")
    identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
    identity_header = os.environ.get("IDENTITY_HEADER")
    azure_client_id = os.environ.get("AZURE_CLIENT_ID")
    
    if msi_endpoint or identity_endpoint:
        print("✅ Azure managed identity environment detected")
        print(f"   • MSI_ENDPOINT: {'✅ Present' if msi_endpoint else '❌ Not found'}")
        print(f"   • IDENTITY_ENDPOINT: {'✅ Present' if identity_endpoint else '❌ Not found'}")
        print(f"   • IDENTITY_HEADER: {'✅ Present' if identity_header else '❌ Not found'}")
        print(f"   • AZURE_CLIENT_ID: {'✅ Present' if azure_client_id else '❌ Not found'}")
    else:
        print("❌ Not running in Azure managed identity environment")
        print("💡 This test should be run inside Azure Container App")
        return False
    
    # Test Azure Identity and HTTP packages
    print("\n📦 Package Check:")
    try:
        from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
        print("✅ azure.identity package available")
    except ImportError:
        print("❌ azure.identity package missing")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp package available")
    except ImportError:
        print("❌ aiohttp package missing")
        return False
    
    # Test managed identity token acquisition
    print("\n🎫 Testing Managed Identity Token:")
    try:
        # Use DefaultAzureCredential first (recommended)
        credential = DefaultAzureCredential()
        
        # Get token for Azure Maps
        token_scope = "https://atlas.microsoft.com/.default"
        token = credential.get_token(token_scope)
        
        if token and token.token:
            print("✅ Successfully obtained Azure Maps token via DefaultAzureCredential")
            print(f"   • Token length: {len(token.token)} characters")
            print(f"   • Expires: {token.expires_on}")
            access_token = token.token
        else:
            print("❌ Failed to get token via DefaultAzureCredential")
            return False
            
    except Exception as e:
        print(f"❌ Token acquisition failed: {e}")
        
        # Try with explicit ManagedIdentityCredential
        print("🔄 Trying with explicit ManagedIdentityCredential...")
        try:
            managed_credential = ManagedIdentityCredential()
            token = managed_credential.get_token(token_scope)
            
            if token and token.token:
                print("✅ Successfully obtained token via ManagedIdentityCredential")
                access_token = token.token
            else:
                print("❌ Failed to get token via ManagedIdentityCredential")
                return False
        except Exception as e2:
            print(f"❌ ManagedIdentityCredential also failed: {e2}")
            return False
    
    # Test Azure Maps API access
    print("\n🗺️ Testing Azure Maps API Access:")
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test the search/address/json endpoint (covered by Azure Maps Data Reader)
        url = "https://atlas.microsoft.com/search/address/json"
        params = {
            'api-version': '1.0',
            'query': 'Charlotte, NC, USA',
            'limit': 1
        }
        
        async with aiohttp.ClientSession() as session:
            print(f"   • Making request to: {url}")
            print(f"   • Query: {params['query']}")
            
            async with session.get(url, headers=headers, params=params, timeout=15) as response:
                print(f"   • Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    results = result.get('results', [])
                    
                    print("✅ Azure Maps API access successful!")
                    print(f"   • Results found: {len(results)}")
                    
                    if results:
                        first_result = results[0]
                        position = first_result.get('position', {})
                        address = first_result.get('address', {})
                        
                        print(f"   • Coordinates: {position.get('lat', 'N/A')}, {position.get('lon', 'N/A')}")
                        print(f"   • Address: {address.get('formattedAddress', 'N/A')}")
                        print(f"   • Country: {address.get('country', 'N/A')}")
                        print(f"   • Admin District: {address.get('adminDistrict', 'N/A')}")
                    
                    return True
                    
                elif response.status == 401:
                    print("❌ Authentication failed (401 Unauthorized)")
                    print("💡 Possible issues:")
                    print("   • Managed identity not properly configured")
                    print("   • Token scope incorrect")
                    print("   • Azure Maps account access issues")
                    
                elif response.status == 403:
                    print("❌ Access forbidden (403 Forbidden)")
                    print("💡 Permission issues:")
                    print("   • Check if 'Azure Maps Data Reader' role is assigned")
                    print("   • Verify role assignment scope includes the Azure Maps account")
                    print("   • Wait 5-10 minutes for role propagation")
                    
                else:
                    response_text = await response.text()
                    print(f"❌ Unexpected response: {response.status}")
                    print(f"   • Response: {response_text[:200]}...")
                
                return False
                
    except asyncio.TimeoutError:
        print("❌ Request timed out")
        print("💡 Check network connectivity to atlas.microsoft.com")
        return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Troubleshooting:")
        print("   • Verify Azure Maps account is active")
        print("   • Check network security rules")
        print("   • Ensure aiohttp package is properly installed")
        return False

async def main():
    """Main test function."""
    print("🧪 Azure Container App Managed Identity Test")
    print("=" * 50)
    print("Testing your managed identity configuration:")
    print("   ✅ Azure Maps Data Reader")
    print("   ✅ Azure Maps Search and Render Data Reader")
    print()
    
    success = await test_managed_identity_azure_maps()
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 30)
    
    if success:
        print("🎉 SUCCESS! Your managed identity is properly configured")
        print("   • Managed identity authentication: ✅ Working")
        print("   • Azure Maps permissions: ✅ Correct")
        print("   • API access: ✅ Functional")
        print("\n💡 Your Azure Maps integration should work in production!")
        
    else:
        print("❌ ISSUES DETECTED with managed identity configuration")
        print("\n🔧 Next Steps:")
        print("   1. Verify you're running this test inside Azure Container App")
        print("   2. Check that system-assigned managed identity is enabled")
        print("   3. Confirm role assignments are correct and propagated")
        print("   4. Restart the Container App after making changes")
        print("   5. Wait 5-10 minutes for Azure role propagation")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🚫 Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
