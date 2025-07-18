#!/usr/bin/env python3
"""
Test Azure Maps endpoints to find the right one for categories
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

async def test_different_endpoints():
    """Test different Azure Maps endpoints."""
    
    load_dotenv()
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    print("🧪 Testing Different Azure Maps Endpoints")
    print("=" * 60)
    
    endpoints = [
        {
            "name": "POI Categories (original)",
            "url": "https://atlas.microsoft.com/search/poi/category/json",
            "params": {"api-version": "1.0", "subscription-key": subscription_key}
        },
        {
            "name": "POI Search (your working curl)",
            "url": "https://atlas.microsoft.com/search/poi/json",
            "params": {"api-version": "1.0", "query": "restaurant", "lat": 47.6062, "lon": -122.3321, "subscription-key": subscription_key}
        },
        {
            "name": "Search Address",
            "url": "https://atlas.microsoft.com/search/address/json",
            "params": {"api-version": "1.0", "query": "Seattle", "subscription-key": subscription_key}
        },
        {
            "name": "Search Nearby",
            "url": "https://atlas.microsoft.com/search/nearby/json",
            "params": {"api-version": "1.0", "lat": 47.6062, "lon": -122.3321, "subscription-key": subscription_key}
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint["url"], params=endpoint["params"]) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if "poiCategories" in result:
                            categories = result["poiCategories"]
                            print(f"   ✅ SUCCESS! Found {len(categories)} POI categories")
                        elif "results" in result:
                            results = result["results"]
                            print(f"   ✅ SUCCESS! Found {len(results)} search results")
                            if results:
                                first_result = results[0]
                                name = first_result.get("poi", {}).get("name", "Unknown")
                                print(f"      First result: {name}")
                        else:
                            print(f"   ✅ SUCCESS! Response keys: {list(result.keys())}")
                            
                    elif response.status == 400:
                        error_text = await response.text()
                        print(f"   ❌ 400 Bad Request: {error_text[:100]}...")
                    elif response.status == 401:
                        print(f"   ❌ 401 Unauthorized")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ {response.status}: {error_text[:100]}...")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_different_endpoints())
