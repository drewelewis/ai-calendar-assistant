#!/usr/bin/env python3
"""
Azure Maps Production 401 Error Diagnostic Script
Tests managed identity authentication step by step.
"""

import os
import asyncio
import aiohttp
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.core.exceptions import ClientAuthenticationError

async def test_azure_maps_auth():
    print("🔍 Azure Maps Production Authentication Test")
    print("=" * 60)
    
    # Check environment variables
    print("\n📋 Environment Check:")
    env_vars = {
        "MSI_ENDPOINT": os.environ.get("MSI_ENDPOINT"),
        "IDENTITY_ENDPOINT": os.environ.get("IDENTITY_ENDPOINT"), 
        "IDENTITY_HEADER": os.environ.get("IDENTITY_HEADER"),
        "AZURE_CLIENT_ID": os.environ.get("AZURE_CLIENT_ID"),
        "AZURE_MAPS_CLIENT_ID": os.environ.get("AZURE_MAPS_CLIENT_ID"),
        "AZURE_MAPS_SUBSCRIPTION_KEY": os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    }
    
    for key, value in env_vars.items():
        status = "✅ Set" if value else "❌ Missing"
        if key == "AZURE_MAPS_SUBSCRIPTION_KEY":
            status = "❌ SET (should be removed for production)" if value else "✅ Not set (good)"
        print(f"   {key}: {status}")
    
    # Check if running in Azure environment
    if not (env_vars["MSI_ENDPOINT"] or env_vars["IDENTITY_ENDPOINT"]):
        print("\n❌ NOT RUNNING IN AZURE ENVIRONMENT")
        print("This test must be run in Azure Container App to work properly.")
        return
    
    print("\n✅ Running in Azure environment detected")
    
    # Test 1: DefaultAzureCredential
    print("\n🧪 TEST 1: DefaultAzureCredential")
    try:
        credential = DefaultAzureCredential()
        print("   ✅ DefaultAzureCredential created")
        
        token = credential.get_token("https://atlas.microsoft.com/.default")
        if token:
            print(f"   ✅ Token acquired - Length: {len(token.token)} chars")
            print(f"   ✅ Token expires: {token.expires_on}")
            default_token = token.token
        else:
            print("   ❌ No token returned")
            return
            
    except Exception as e:
        print(f"   ❌ DefaultAzureCredential failed: {e}")
        return
    
    # Test 2: ManagedIdentityCredential (explicit)
    print("\n🧪 TEST 2: ManagedIdentityCredential")
    try:
        mi_credential = ManagedIdentityCredential()
        mi_token = mi_credential.get_token("https://atlas.microsoft.com/.default")
        if mi_token:
            print(f"   ✅ ManagedIdentity token acquired - Length: {len(mi_token.token)} chars")
            managed_token = mi_token.token
        else:
            print("   ❌ No managed identity token returned")
            managed_token = None
    except Exception as e:
        print(f"   ❌ ManagedIdentityCredential failed: {e}")
        managed_token = None
    
    # Test 3: Azure Maps API Call
    print("\n🌐 TEST 3: Azure Maps API Call")
    
    # Use the working token (prefer DefaultAzureCredential)
    test_token = default_token
    
    headers = {"Authorization": f"Bearer {test_token}"}
    params = {
        "api-version": "1.0",
        "lat": 47.6062,
        "lon": -122.3321
    }
    
    url = "https://atlas.microsoft.com/search/nearby/json"
    
    print(f"   🌐 URL: {url}")
    print(f"   🔐 Auth: Bearer token ({len(test_token)} chars)")
    print(f"   📍 Test location: Seattle (47.6062, -122.3321)")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                print(f"   📡 Response: HTTP {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    results_count = len(result.get("results", []))
                    print(f"   ✅ SUCCESS! Found {results_count} nearby results")
                    print("\n🎉 Azure Maps authentication is working correctly!")
                    
                elif response.status == 401:
                    error_text = await response.text()
                    print(f"   ❌ 401 UNAUTHORIZED")
                    print(f"   📄 Response: {error_text}")
                    print("\n💡 401 Error Troubleshooting:")
                    print("   1. Azure Maps account may not have 'disableLocalAuth: true'")
                    print("   2. Role assignment may be missing or incorrect")
                    print("   3. Container App may need restart after configuration changes")
                    
                elif response.status == 403:
                    error_text = await response.text()
                    print(f"   ❌ 403 FORBIDDEN")
                    print(f"   📄 Response: {error_text}")
                    print("\n💡 403 Error Troubleshooting:")
                    print("   1. Check 'Azure Maps Data Reader' role assignment")
                    print("   2. Verify role scope includes the Azure Maps account")
                    print("   3. Wait 5-10 minutes for role propagation")
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ HTTP {response.status}")
                    print(f"   📄 Response: {error_text}")
                    
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Diagnostic complete")

if __name__ == "__main__":
    asyncio.run(test_azure_maps_auth())
