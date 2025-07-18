#!/usr/bin/env python3
"""
Quick Azure Maps test with current environment
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

async def quick_test():
    # Load .env
    load_dotenv()
    
    key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    print(f"🔑 Key loaded: {key[:15]}... (length: {len(key)})")
    
    # Test API
    url = "https://atlas.microsoft.com/search/poi/category/json"
    headers = {"Ocp-Apim-Subscription-Key": key}
    params = {"api-version": "1.0"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            print(f"📊 Status: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                categories = result.get("poiCategories", [])
                print(f"✅ SUCCESS! Found {len(categories)} categories")
                return True
            else:
                text = await response.text()
                print(f"❌ Failed: {text}")
                return False

if __name__ == "__main__":
    asyncio.run(quick_test())
