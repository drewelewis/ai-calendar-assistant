#!/usr/bin/env python3
"""
Detailed Azure Maps Key Validation
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def validate_key_format():
    """Validate the Azure Maps subscription key format."""
    
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        print("❌ No AZURE_MAPS_SUBSCRIPTION_KEY found")
        return False
    
    print(f"🔍 Key Analysis:")
    print(f"   Length: {len(subscription_key)} characters")
    print(f"   First 12 chars: {subscription_key[:12]}")
    print(f"   Last 8 chars: {subscription_key[-8:]}")
    
    # Azure Maps keys are typically 64 characters long
    if len(subscription_key) != 64:
        print(f"⚠️  Warning: Expected 64 characters, got {len(subscription_key)}")
    else:
        print(f"✅ Key length looks correct (64 characters)")
    
    # Check if it contains only valid characters (base64-like)
    import re
    if re.match(r'^[A-Za-z0-9+/=]+$', subscription_key):
        print(f"✅ Key format looks valid (base64-like characters)")
    else:
        print(f"⚠️  Key contains unexpected characters")
    
    return True

async def test_with_detailed_headers():
    """Test with detailed request/response headers."""
    
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        return False
    
    print(f"\n🌐 Testing Azure Maps API...")
    
    url = "https://atlas.microsoft.com/search/poi/category/json"
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "User-Agent": "ai-calendar-assistant/1.0",
        "Accept": "application/json"
    }
    params = {"api-version": "1.0"}
    
    print(f"🔗 URL: {url}")
    print(f"📋 Parameters: {params}")
    print(f"🔑 Headers: {list(headers.keys())}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, params=params) as response:
                print(f"\n📊 Response Details:")
                print(f"   Status: {response.status}")
                print(f"   Reason: {response.reason}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                
                # Read response body
                response_text = await response.text()
                print(f"   Response Length: {len(response_text)} bytes")
                
                if response.status == 200:
                    print(f"✅ SUCCESS!")
                    try:
                        result = await response.json()
                        categories = result.get("poiCategories", [])
                        print(f"   Found {len(categories)} POI categories")
                        
                        # Show sample categories
                        for i, cat in enumerate(categories[:3]):
                            print(f"   Sample {i+1}: {cat.get('name', 'Unknown')}")
                        
                        return True
                    except Exception as json_error:
                        print(f"❌ JSON parsing error: {json_error}")
                        
                elif response.status == 401:
                    print(f"❌ 401 Unauthorized")
                    print(f"   Full response: {response_text}")
                    
                    # Check for specific error patterns
                    if "Unauthorized" in response_text:
                        print(f"\n💡 Analysis:")
                        print(f"   - The subscription key is not valid")
                        print(f"   - Key might be expired, disabled, or from wrong region")
                        print(f"   - Check Azure portal for key status")
                    
                elif response.status == 403:
                    print(f"❌ 403 Forbidden")
                    print(f"   Response: {response_text}")
                    print(f"\n💡 This means the key is valid but lacks permissions")
                    
                else:
                    print(f"❌ Unexpected status: {response.status}")
                    print(f"   Response: {response_text}")
                
                return False
                
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_alternative_endpoints():
    """Test alternative Azure Maps endpoints."""
    
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        return False
    
    print(f"\n🧪 Testing Alternative Endpoints:")
    
    endpoints = [
        {
            "name": "Search Address",
            "url": "https://atlas.microsoft.com/search/address/json",
            "params": {"api-version": "1.0", "query": "Seattle"}
        },
        {
            "name": "Geocoding",
            "url": "https://atlas.microsoft.com/search/geocoding",
            "params": {"api-version": "2023-06-01", "query": "Seattle"}
        }
    ]
    
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    
    for endpoint in endpoints:
        print(f"\n  Testing {endpoint['name']}...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint["url"], headers=headers, params=endpoint["params"]) as response:
                    print(f"    Status: {response.status}")
                    if response.status == 200:
                        print(f"    ✅ {endpoint['name']} works!")
                    elif response.status == 401:
                        print(f"    ❌ 401 Unauthorized")
                    else:
                        print(f"    ⚠️  Status {response.status}")
                        
        except Exception as e:
            print(f"    ❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Azure Maps Key Detailed Validation")
    print("=" * 60)
    
    asyncio.run(validate_key_format())
    asyncio.run(test_with_detailed_headers())
    asyncio.run(test_alternative_endpoints())
