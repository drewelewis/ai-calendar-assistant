#!/usr/bin/env python3
"""
Simple Azure Maps subscription key test
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_subscription_key():
    """Test the Azure Maps subscription key directly."""
    
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        print("❌ No AZURE_MAPS_SUBSCRIPTION_KEY found in environment")
        return
    
    print(f"🔑 Testing subscription key: {subscription_key[:12]}...{subscription_key[-8:]}")
    
    url = "https://atlas.microsoft.com/search/poi/category/json"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"api-version": "1.0"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                print(f"📊 Status Code: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    categories = result.get("poiCategories", [])
                    print(f"✅ SUCCESS! Found {len(categories)} POI categories")
                    return True
                
                elif response.status == 401:
                    print("❌ 401 Unauthorized")
                    error_text = await response.text()
                    print(f"   Response: {error_text}")
                    
                    # Common causes of 401
                    print("\n💡 Possible causes:")
                    print("   1. Invalid subscription key")
                    print("   2. Subscription key expired")
                    print("   3. Azure Maps service not enabled for this subscription")
                    print("   4. Key doesn't have proper permissions")
                    
                elif response.status == 403:
                    print("❌ 403 Forbidden")
                    error_text = await response.text()
                    print(f"   Response: {error_text}")
                    print("\n💡 This usually means the key is valid but lacks permissions")
                    
                else:
                    print(f"❌ Unexpected status: {response.status}")
                    error_text = await response.text()
                    print(f"   Response: {error_text}")
                
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

async def check_azure_maps_service():
    """Check if Azure Maps service is generally available."""
    print("\n🌐 Testing Azure Maps service availability...")
    
    # Test with a known invalid key to see if service responds
    url = "https://atlas.microsoft.com/search/poi/category/json"
    headers = {"Ocp-Apim-Subscription-Key": "invalid-key-test"}
    params = {"api-version": "1.0"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                print(f"📊 Service response: {response.status}")
                
                if response.status == 401:
                    print("✅ Azure Maps service is responding (401 expected with invalid key)")
                    return True
                else:
                    print(f"⚠️  Unexpected response: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Cannot reach Azure Maps service: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Azure Maps Subscription Key Test")
    print("=" * 50)
    
    asyncio.run(check_azure_maps_service())
    asyncio.run(test_subscription_key())
