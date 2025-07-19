#!/usr/bin/env python3
"""
Simple Debug Test
"""

import os
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'
os.environ['AZURE_MAPS_SUBSCRIPTION_KEY'] = ''

import asyncio
from operations.azure_maps_operations import AzureMapsOperations

async def simple_test():
    print("🧪 Simple Managed Identity Debug Test")
    print("=" * 40)
    
    async with AzureMapsOperations() as azure_maps:
        result = await azure_maps.geolocate_city_state("Seattle", "WA")
        if result:
            print("✅ Success!")
        else:
            print("❌ Failed!")

if __name__ == "__main__":
    asyncio.run(simple_test())
