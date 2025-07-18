#!/usr/bin/env python3
"""
Test Azure Maps with URL parameter (like curl command)
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

async def test_url_parameter_method():
    """Test Azure Maps using subscription key as URL parameter (like curl)."""
    
    # Load .env
    load_dotenv()
    
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        print("❌ No subscription key found")
        return False
    
    print("🧪 Testing Azure Maps with URL parameter method")
    print("=" * 60)
    print(f"🔑 Using key: {subscription_key[:15]}...{subscription_key[-8:]}")
    
    # Test 1: POI Categories (original failing endpoint)
    print(f"\n📋 Test 1: POI Categories")
    url1 = "https://atlas.microsoft.com/search/poi/category/json"
    params1 = {
        "api-version": "1.0",
        "subscription-key": subscription_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url1, params=params1) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    categories = result.get("poiCategories", [])
                    print(f"   ✅ SUCCESS! Found {len(categories)} POI categories")
                else:
                    text = await response.text()
                    print(f"   ❌ Failed: {text[:100]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: POI Search (like your working curl)
    print(f"\n🔍 Test 2: POI Search (like your curl command)")
    url2 = "https://atlas.microsoft.com/search/poi/json"
    params2 = {
        "api-version": "1.0",
        "query": "coffee",
        "lat": 47.6062,
        "lon": -122.3321,
        "subscription-key": subscription_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url2, params=params2) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    results = result.get("results", [])
                    print(f"   ✅ SUCCESS! Found {len(results)} coffee shops")
                    
                    # Show first few results
                    for i, poi in enumerate(results[:3]):
                        name = poi.get("poi", {}).get("name", "Unknown")
                        address = poi.get("address", {}).get("freeformAddress", "No address")
                        print(f"      {i+1}. {name} - {address}")
                        
                    return True
                else:
                    text = await response.text()
                    print(f"   ❌ Failed: {text[:100]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Header method (our original approach)
    print(f"\n🔑 Test 3: Header method (original approach)")
    url3 = "https://atlas.microsoft.com/search/poi/category/json"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params3 = {"api-version": "1.0"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url3, headers=headers, params=params3) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    categories = result.get("poiCategories", [])
                    print(f"   ✅ SUCCESS! Found {len(categories)} POI categories")
                else:
                    text = await response.text()
                    print(f"   ❌ Failed: {text[:100]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_url_parameter_method())
