#!/usr/bin/env python3
"""
Specific Managed Identity Debug Tool

This script tests the specific managed identity: 5238e629-da2f-4bb0-aea5-14d45526c864
and diagnoses why it's not working with Azure Maps.
"""

import asyncio
import os
import sys
import json

async def test_specific_managed_identity():
    """Test the specific managed identity configuration."""
    print("🔍 Testing Specific Managed Identity")
    print("=" * 50)
    print("Identity: 5238e629-da2f-4bb0-aea5-14d45526c864")
    print()
    
    # Check environment
    print("🏗️ Environment Analysis:")
    
    # Check for Azure Container App environment variables
    env_vars = {
        'MSI_ENDPOINT': os.environ.get('MSI_ENDPOINT'),
        'IDENTITY_ENDPOINT': os.environ.get('IDENTITY_ENDPOINT'),
        'IDENTITY_HEADER': os.environ.get('IDENTITY_HEADER'),
        'AZURE_CLIENT_ID': os.environ.get('AZURE_CLIENT_ID'),
        'AZURE_TENANT_ID': os.environ.get('AZURE_TENANT_ID'),
        'AZURE_SUBSCRIPTION_ID': os.environ.get('AZURE_SUBSCRIPTION_ID'),
        'AZURE_MAPS_SUBSCRIPTION_KEY': os.environ.get('AZURE_MAPS_SUBSCRIPTION_KEY'),
        'AZURE_MAPS_CLIENT_ID': os.environ.get('AZURE_MAPS_CLIENT_ID')
    }
    
    for var, value in env_vars.items():
        if value:
            if 'KEY' in var or 'SECRET' in var or 'HEADER' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else value
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Determine environment type
    if env_vars['MSI_ENDPOINT'] or env_vars['IDENTITY_ENDPOINT']:
        print("\n✅ Running in Azure managed identity environment")
        environment_type = "azure"
    else:
        print("\n❌ Running locally (not in Azure)")
        environment_type = "local"
        print("💡 This script needs to run inside Azure Container App to test managed identity")
        return False
    
    # Test Azure packages
    print("\n📦 Testing Required Packages:")
    try:
        from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
        print("   ✅ azure.identity: Available")
    except ImportError as e:
        print(f"   ❌ azure.identity: Missing - {e}")
        return False
    
    try:
        import aiohttp
        print("   ✅ aiohttp: Available")
    except ImportError as e:
        print(f"   ❌ aiohttp: Missing - {e}")
        return False
    
    # Test managed identity token acquisition
    print("\n🎫 Testing Token Acquisition:")
    
    # Method 1: DefaultAzureCredential (recommended)
    print("   🔄 Method 1: DefaultAzureCredential")
    try:
        credential = DefaultAzureCredential()
        token_scope = "https://atlas.microsoft.com/.default"
        
        print(f"      • Requesting token for scope: {token_scope}")
        token = credential.get_token(token_scope)
        
        if token and token.token:
            print("      ✅ SUCCESS: Token obtained via DefaultAzureCredential")
            print(f"      • Token length: {len(token.token)} characters")
            print(f"      • Token expires: {token.expires_on}")
            access_token = token.token
            auth_method = "DefaultAzureCredential"
        else:
            print("      ❌ FAILED: No token returned")
            access_token = None
            
    except Exception as e:
        print(f"      ❌ FAILED: {e}")
        access_token = None
    
    # Method 2: Explicit ManagedIdentityCredential
    if not access_token:
        print("   🔄 Method 2: ManagedIdentityCredential (system-assigned)")
        try:
            managed_credential = ManagedIdentityCredential()
            token = managed_credential.get_token(token_scope)
            
            if token and token.token:
                print("      ✅ SUCCESS: Token obtained via ManagedIdentityCredential")
                access_token = token.token
                auth_method = "ManagedIdentityCredential"
            else:
                print("      ❌ FAILED: No token returned")
                
        except Exception as e:
            print(f"      ❌ FAILED: {e}")
    
    # Method 3: Explicit client ID (if available)
    if not access_token and env_vars['AZURE_CLIENT_ID']:
        print(f"   🔄 Method 3: ManagedIdentityCredential with client_id")
        try:
            client_credential = ManagedIdentityCredential(client_id=env_vars['AZURE_CLIENT_ID'])
            token = client_credential.get_token(token_scope)
            
            if token and token.token:
                print("      ✅ SUCCESS: Token obtained with explicit client_id")
                access_token = token.token
                auth_method = "ManagedIdentityCredential (client_id)"
            else:
                print("      ❌ FAILED: No token returned")
                
        except Exception as e:
            print(f"      ❌ FAILED: {e}")
    
    if not access_token:
        print("\n❌ CRITICAL: Unable to obtain access token")
        print("🔧 Troubleshooting steps:")
        print("   1. Verify system-assigned managed identity is enabled")
        print("   2. Check that Container App has been restarted after enabling identity")
        print("   3. Ensure you're running this script inside the Container App")
        print("   4. Verify role assignments are correctly configured")
        return False
    
    # Test Azure Maps API access
    print(f"\n🗺️ Testing Azure Maps API Access (using {auth_method}):")
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'AzureMapsTest/1.0'
        }
        
        # Test the search endpoint
        url = "https://atlas.microsoft.com/search/address/json"
        params = {
            'api-version': '1.0',
            'query': 'Microsoft Way, Redmond, WA',
            'limit': 1
        }
        
        print(f"   • URL: {url}")
        print(f"   • Query: {params['query']}")
        print(f"   • Auth method: Bearer token")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=20) as response:
                status_code = response.status
                print(f"   • Response status: {status_code}")
                
                if status_code == 200:
                    result = await response.json()
                    results = result.get('results', [])
                    
                    print("   ✅ SUCCESS: Azure Maps API accessible!")
                    print(f"   • Results found: {len(results)}")
                    
                    if results:
                        first_result = results[0]
                        position = first_result.get('position', {})
                        address = first_result.get('address', {})
                        
                        print(f"   • Coordinates: {position.get('lat', 'N/A')}, {position.get('lon', 'N/A')}")
                        print(f"   • Address: {address.get('formattedAddress', 'N/A')}")
                    
                    return True
                    
                elif status_code == 401:
                    response_text = await response.text()
                    print("   ❌ AUTHENTICATION FAILED (401)")
                    print(f"   • Response: {response_text}")
                    print("   🔧 Possible causes:")
                    print("     - Token is invalid or expired")
                    print("     - Managed identity not properly configured")
                    print("     - Token scope is incorrect")
                    
                elif status_code == 403:
                    response_text = await response.text()
                    print("   ❌ ACCESS FORBIDDEN (403)")
                    print(f"   • Response: {response_text}")
                    print("   🔧 Permission issues:")
                    print("     - 'Azure Maps Data Reader' role not assigned")
                    print("     - Role assignment scope is incorrect")
                    print("     - Role propagation still in progress (wait 5-10 minutes)")
                    print(f"     - Verify identity {env_vars.get('AZURE_CLIENT_ID', 'system-assigned')} has correct roles")
                    
                else:
                    response_text = await response.text()
                    print(f"   ❌ UNEXPECTED RESPONSE ({status_code})")
                    print(f"   • Response: {response_text[:300]}...")
                
                return False
                
    except asyncio.TimeoutError:
        print("   ❌ REQUEST TIMEOUT")
        print("   🔧 Network issues:")
        print("     - Check connectivity to atlas.microsoft.com")
        print("     - Verify firewall/network security group rules")
        return False
        
    except Exception as e:
        print(f"   ❌ REQUEST FAILED: {e}")
        print("   🔧 Troubleshooting:")
        print("     - Check network connectivity")
        print("     - Verify aiohttp is properly installed")
        print("     - Check for proxy/firewall issues")
        return False

async def compare_with_working_code():
    """Compare the results with your existing Azure Maps operations."""
    print(f"\n🔄 Testing with Your Existing Azure Maps Code:")
    print("=" * 50)
    
    try:
        # Import your existing code
        from operations.azure_maps_operations import AzureMapsOperations
        
        print("   ✅ Successfully imported AzureMapsOperations")
        
        # Test with your existing implementation
        async with AzureMapsOperations() as azure_maps:
            print("   ✅ AzureMapsOperations initialized")
            
            # Run diagnosis
            print("   🔍 Running built-in diagnosis...")
            diagnosis = await azure_maps.diagnose_azure_maps_setup()
            
            auth_method = "Unknown"
            if diagnosis.get("subscription_key_available"):
                auth_method = "Subscription Key"
            elif diagnosis.get("managed_identity_test", {}).get("status") == "success":
                auth_method = "Managed Identity"
            
            print(f"   • Detected auth method: {auth_method}")
            
            # Test connection
            print("   🔗 Testing connection...")
            connection_result = await azure_maps.test_connection()
            
            if connection_result.get("overall_status") == "success":
                print("   ✅ Connection successful with your existing code!")
                print(f"   • Auth method: {connection_result.get('auth_method', 'Unknown')}")
                return True
            else:
                print("   ❌ Connection failed with your existing code")
                print(f"   • Status: {connection_result.get('overall_status')}")
                if 'error' in connection_result:
                    print(f"   • Error: {connection_result['error']}")
                return False
                
    except Exception as e:
        print(f"   ❌ Failed to test existing code: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main diagnostic function."""
    print("🧪 Managed Identity Debug Tool")
    print("=" * 50)
    print("Testing managed identity: 5238e629-da2f-4bb0-aea5-14d45526c864")
    print("Permissions:")
    print("  ✅ Azure Maps Data Reader")
    print("  ✅ Azure Maps Search and Render Data Reader")
    print()
    
    # Test managed identity access
    mi_success = await test_specific_managed_identity()
    
    # Test with existing code
    code_success = await compare_with_working_code()
    
    print(f"\n📊 FINAL DIAGNOSIS")
    print("=" * 30)
    print(f"Managed Identity Direct Test: {'✅ SUCCESS' if mi_success else '❌ FAILED'}")
    print(f"Existing Code Test: {'✅ SUCCESS' if code_success else '❌ FAILED'}")
    
    if not mi_success and not code_success:
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print(f"1. Verify this script runs inside Azure Container App (not locally)")
        print(f"2. Check managed identity is enabled and restarted")
        print(f"3. Verify role assignments for identity: 5238e629-da2f-4bb0-aea5-14d45526c864")
        print(f"4. Wait 10 minutes after role assignment for propagation")
        print(f"5. Check Azure Maps account is in same subscription")
    elif not mi_success and code_success:
        print(f"\n✅ Your existing code works - managed identity is functional!")
        print(f"The direct test may have failed due to token caching or timing")
    elif mi_success and not code_success:
        print(f"\n⚠️ Managed identity works, but your code has issues")
        print(f"Check your AzureMapsOperations implementation")
    else:
        print(f"\n🎉 SUCCESS: Both managed identity and your code work perfectly!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🚫 Diagnostic cancelled by user")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
