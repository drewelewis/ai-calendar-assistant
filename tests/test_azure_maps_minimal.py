#!/usr/bin/env python3
"""
Minimal Azure Maps Test - No Dependencies

This script tests Azure Maps operations without any telemetry or external dependencies.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_minimal_azure_maps():
    """Test Azure Maps with minimal dependencies."""
    print("🧪 Starting Minimal Azure Maps Test")
    
    # Check environment variables
    client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    print("=== Environment Check ===")
    print(f"AZURE_MAPS_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
    print(f"AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if subscription_key else '❌ Not set'}")
    
    if not client_id and not subscription_key:
        print("❌ No authentication credentials found!")
        print("Please set either AZURE_MAPS_CLIENT_ID or AZURE_MAPS_SUBSCRIPTION_KEY")
        return False
    
    print("\n=== Creating Minimal Azure Maps Client ===")
    
    # Create a minimal version inline
    import aiohttp
    from azure.identity import DefaultAzureCredential
    
    class MinimalAzureMaps:
        def __init__(self):
            self.base_url = "https://atlas.microsoft.com"
            self.subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
            self.client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
            
        async def test_connection(self):
            """Test basic connection to Azure Maps."""
            try:
                async with aiohttp.ClientSession() as session:
                    # Build auth headers
                    headers = {}
                    if self.subscription_key:
                        headers["Ocp-Apim-Subscription-Key"] = self.subscription_key
                        auth_method = "subscription_key"
                    else:
                        # Try managed identity
                        credential = DefaultAzureCredential()
                        token = await credential.get_token("https://atlas.microsoft.com/.default")
                        headers["Authorization"] = f"Bearer {token.token}"
                        auth_method = "managed_identity"
                    
                    # Test with a simple POI categories request
                    url = f"{self.base_url}/search/poi/category/json"
                    params = {"api-version": "1.0"}
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "success": True,
                                "auth_method": auth_method,
                                "status_code": response.status,
                                "categories_count": len(result.get("poiCategories", []))
                            }
                        else:
                            return {
                                "success": False,
                                "auth_method": auth_method,
                                "status_code": response.status,
                                "error": await response.text()
                            }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
    
    # Test the minimal client
    maps_client = MinimalAzureMaps()
    result = await maps_client.test_connection()
    
    print("\n=== Test Results ===")
    if result["success"]:
        print("✅ Connection successful!")
        print(f"Auth method: {result['auth_method']}")
        print(f"Status code: {result['status_code']}")
        if "categories_count" in result:
            print(f"POI categories available: {result['categories_count']}")
    else:
        print("❌ Connection failed!")
        print(f"Error: {result['error']}")
        if "auth_method" in result:
            print(f"Auth method attempted: {result['auth_method']}")
        if "status_code" in result:
            print(f"Status code: {result['status_code']}")
    
    return result["success"]

def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_minimal_azure_maps())
        
        if success:
            print("\n🎉 Minimal Azure Maps test completed successfully!")
            print("✅ Core functionality is working")
            print("✅ Azure Maps API is accessible")
            print("✅ Authentication is working")
            return 0
        else:
            print("\n💥 Minimal Azure Maps test failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
