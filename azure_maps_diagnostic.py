#!/usr/bin/env python3
"""
Azure Maps Connection Diagnostic Tool
This script performs detailed diagnostics to identify connection issues.
"""

import os
import asyncio
import aiohttp
from datetime import datetime

# Disable telemetry for faster testing
os.environ['TELEMETRY_EXPLICITLY_DISABLED'] = 'true'

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded")
except ImportError:
    print("⚠️  python-dotenv not available - using system environment variables only")

def check_environment_variables():
    """Check all Azure Maps related environment variables."""
    print("\n" + "=" * 60)
    print("🔍 ENVIRONMENT VARIABLES DIAGNOSTIC")
    print("=" * 60)
    
    env_vars = {
        "AZURE_MAPS_SUBSCRIPTION_KEY": os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY"),
        "AZURE_MAPS_CLIENT_ID": os.environ.get("AZURE_MAPS_CLIENT_ID"),
        "AZURE_CLIENT_ID": os.environ.get("AZURE_CLIENT_ID"),
        "AZURE_TENANT_ID": os.environ.get("AZURE_TENANT_ID"),
        "AZURE_CLIENT_SECRET": os.environ.get("AZURE_CLIENT_SECRET"),
        "TELEMETRY_EXPLICITLY_DISABLED": os.environ.get("TELEMETRY_EXPLICITLY_DISABLED")
    }
    
    for var_name, var_value in env_vars.items():
        if var_value:
            if "KEY" in var_name or "SECRET" in var_name:
                # Mask sensitive values
                masked_value = f"{var_value[:8]}...{var_value[-4:]}" if len(var_value) > 12 else f"{var_value[:4]}..."
                print(f"✅ {var_name}: {masked_value}")
            else:
                print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: Not set")
    
    # Check which authentication method should be used
    print(f"\n🔑 AUTHENTICATION METHOD:")
    if env_vars["AZURE_MAPS_SUBSCRIPTION_KEY"]:
        print("   Primary: Subscription Key")
    elif env_vars["AZURE_MAPS_CLIENT_ID"] or env_vars["AZURE_CLIENT_ID"]:
        print("   Primary: Managed Identity")
        if not env_vars["AZURE_TENANT_ID"]:
            print("   ⚠️  Warning: AZURE_TENANT_ID not set (may be needed for managed identity)")
    else:
        print("   ❌ No authentication credentials found!")
        return False
    
    return True

async def test_direct_api_call():
    """Test direct API call without using our wrapper class."""
    print("\n" + "=" * 60)
    print("🌐 DIRECT API CALL TEST")
    print("=" * 60)
    
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        print("❌ No subscription key available for direct test")
        return False
    
    url = "https://atlas.microsoft.com/search/poi/category/json"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"api-version": "1.0"}
    
    print(f"🔗 URL: {url}")
    print(f"🔑 Using subscription key: {subscription_key[:8]}...{subscription_key[-4:]}")
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"⏱️  Making request...")
            start_time = datetime.now()
            
            async with session.get(url, headers=headers, params=params) as response:
                duration = (datetime.now() - start_time).total_seconds()
                
                print(f"📊 Response Status: {response.status}")
                print(f"⏱️  Response Time: {duration:.3f}s")
                
                if response.status == 200:
                    result = await response.json()
                    categories = result.get("poiCategories", [])
                    print(f"✅ Success! Found {len(categories)} POI categories")
                    
                    if categories:
                        print(f"📋 Sample categories:")
                        for i, cat in enumerate(categories[:5]):
                            print(f"   {i+1}. {cat.get('name', 'Unknown')} (ID: {cat.get('id', 'N/A')})")
                    
                    return True
                    
                elif response.status == 401:
                    print("❌ 401 Unauthorized - Invalid subscription key")
                    response_text = await response.text()
                    print(f"   Error details: {response_text}")
                    
                elif response.status == 403:
                    print("❌ 403 Forbidden - Subscription key valid but access denied")
                    response_text = await response.text()
                    print(f"   Error details: {response_text}")
                    
                else:
                    print(f"❌ Unexpected status: {response.status}")
                    response_text = await response.text()
                    print(f"   Response: {response_text}")
                
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

async def test_azure_maps_operations():
    """Test using our Azure Maps Operations wrapper."""
    print("\n" + "=" * 60)
    print("🔧 AZURE MAPS OPERATIONS TEST")
    print("=" * 60)
    
    try:
        from operations.azure_maps_operations import AzureMapsOperations
        
        print("✅ Azure Maps Operations imported successfully")
        
        # Create client
        maps_ops = AzureMapsOperations()
        
        # Check telemetry status
        telemetry_status = maps_ops.get_telemetry_status()
        print(f"📊 Telemetry Status: {telemetry_status}")
        
        # Test connection
        print(f"\n🔗 Testing connection...")
        async with maps_ops as client:
            connection_result = await client.test_connection()
            
            print(f"\n📋 Connection Test Results:")
            for key, value in connection_result.items():
                print(f"   {key}: {value}")
                
            return connection_result.get('overall_status') == 'success'
            
    except Exception as e:
        print(f"❌ Azure Maps Operations test failed: {e}")
        import traceback
        print(f"📜 Full traceback:\n{traceback.format_exc()}")
        return False

async def run_full_diagnostic():
    """Run complete diagnostic suite."""
    print("🔍 Azure Maps Connection Diagnostic Tool")
    print("=" * 80)
    
    # Step 1: Check environment variables
    env_ok = check_environment_variables()
    
    # Step 2: Test direct API call (if subscription key available)
    direct_ok = await test_direct_api_call()
    
    # Step 3: Test Azure Maps Operations wrapper
    wrapper_ok = await test_azure_maps_operations()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"Environment Variables: {'✅ OK' if env_ok else '❌ Issues Found'}")
    print(f"Direct API Call: {'✅ OK' if direct_ok else '❌ Failed'}")
    print(f"Azure Maps Operations: {'✅ OK' if wrapper_ok else '❌ Failed'}")
    
    if direct_ok and wrapper_ok:
        print(f"\n🎉 All tests passed! Azure Maps is working correctly.")
    elif direct_ok and not wrapper_ok:
        print(f"\n⚠️  API works directly but wrapper has issues.")
    elif not direct_ok:
        print(f"\n❌ API connection failed - check credentials and network.")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if not env_ok:
        print(f"   1. Check your .env file for AZURE_MAPS_SUBSCRIPTION_KEY")
        print(f"   2. Verify the subscription key is correct and active")
    
    if env_ok and not direct_ok:
        print(f"   1. Verify your Azure Maps subscription is active")
        print(f"   2. Check if the subscription key has the correct permissions")
        print(f"   3. Ensure your IP is not blocked by Azure Maps")
    
    if direct_ok and not wrapper_ok:
        print(f"   1. Check the Azure Maps Operations implementation")
        print(f"   2. Verify all imports are working correctly")

if __name__ == "__main__":
    asyncio.run(run_full_diagnostic())
