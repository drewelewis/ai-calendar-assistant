#!/usr/bin/env python3
"""
Test the fixed Azure Maps implementation
"""

import asyncio
import os
from dotenv import load_dotenv

# Set telemetry disabled
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'

from operations.azure_maps_operations import AzureMapsOperations

async def test_fixed_implementation():
    """Test the fixed Azure Maps implementation."""
    
    print("🧪 Testing Fixed Azure Maps Implementation")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    async with AzureMapsOperations() as maps_ops:
        
        # Test 1: Connection test
        print("\n🔗 Test 1: Connection Test")
        try:
            result = await maps_ops.test_connection()
            print(f"   Status: {result.get('overall_status')}")
            print(f"   Duration: {result.get('duration_seconds', 0):.3f}s")
            
            if result.get('overall_status') == 'success':
                print(f"   ✅ Connection successful!")
                print(f"   Auth Method: {result.get('auth_method')}")
                print(f"   Categories Found: {result.get('categories_found', 0)}")
            else:
                print(f"   ❌ Connection failed")
                print(f"   Error: {result.get('error', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: POI Categories
        print("\n📋 Test 2: POI Categories")
        try:
            categories = await maps_ops.get_poi_categories()
            print(f"   ✅ Found {len(categories)} POI categories")
            
            # Show sample categories
            for i, cat in enumerate(categories[:5]):
                print(f"      {i+1}. {cat.get('name', 'Unknown')} (ID: {cat.get('id', 'N/A')})")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 3: Nearby Search (Seattle coffee shops)
        print("\n🔍 Test 3: Nearby Search (Seattle)")
        try:
            results = await maps_ops.search_nearby(47.6062, -122.3321, radius=1000, limit=5)
            pois = results.get('results', [])
            print(f"   ✅ Found {len(pois)} nearby POIs")
            
            # Show sample POIs
            for i, poi in enumerate(pois[:3]):
                name = poi.get('poi', {}).get('name', 'Unknown')
                address = poi.get('address', {}).get('freeformAddress', 'No address')
                print(f"      {i+1}. {name} - {address}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_implementation())
