#!/usr/bin/env python3
"""
ACA Managed Identity Diagnostic Tool (Python-only version)

This script helps diagnose ACA managed identity configuration for Azure Maps access
using Python and Azure SDK instead of Azure CLI.

Usage:
    python check_aca_python.py
"""

import asyncio
import os
import sys

# Check if we have the required Azure packages
try:
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.authorization import AuthorizationManagementClient
    from azure.mgmt.maps import MapsManagementClient
    import aiohttp
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("💡 Install required packages:")
    print("   pip install azure-identity azure-mgmt-containerinstance azure-mgmt-resource azure-mgmt-authorization azure-mgmt-maps aiohttp")
    sys.exit(1)

async def test_azure_authentication():
    """Test Azure authentication using DefaultAzureCredential."""
    print("🔐 Testing Azure Authentication...")
    
    try:
        # Try to get a credential
        credential = DefaultAzureCredential()
        
        # Try to get a token for Azure Resource Manager
        token_request = credential.get_token("https://management.azure.com/.default")
        
        if token_request and token_request.token:
            print("✅ Azure authentication successful")
            print(f"   • Token expires at: {token_request.expires_on}")
            return credential
        else:
            print("❌ Failed to get Azure token")
            return None
            
    except Exception as e:
        print(f"❌ Azure authentication failed: {e}")
        print("\n💡 Authentication troubleshooting:")
        print("   • Make sure you're logged in: az login")
        print("   • Check environment variables: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET")
        print("   • Verify you have the correct permissions")
        return None

async def get_subscription_info(credential):
    """Get current subscription information."""
    print("\n📋 Getting Subscription Information...")
    
    try:
        # Get subscription ID from environment or use default
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        
        if not subscription_id:
            print("❌ AZURE_SUBSCRIPTION_ID environment variable not set")
            print("💡 Set your subscription ID:")
            print("   $env:AZURE_SUBSCRIPTION_ID = 'your-subscription-id'")
            return None
        
        print(f"✅ Using subscription: {subscription_id}")
        return subscription_id
        
    except Exception as e:
        print(f"❌ Failed to get subscription info: {e}")
        return None

async def check_aca_managed_identity_manual():
    """Manual check for ACA managed identity using environment variables."""
    print("\n🔍 Manual ACA Managed Identity Check")
    print("=" * 40)
    
    # Check for common ACA environment variables
    print("🔍 Checking Container App Environment Variables...")
    
    # Common ACA environment variables
    aca_vars = {
        'AZURE_CLIENT_ID': 'Client ID for managed identity',
        'MSI_ENDPOINT': 'Managed Service Identity endpoint',
        'MSI_SECRET': 'Managed Service Identity secret',
        'IDENTITY_ENDPOINT': 'Identity endpoint',
        'IDENTITY_HEADER': 'Identity header',
        'CONTAINER_APP_NAME': 'Container App name',
        'CONTAINER_APP_ENV_NAME': 'Container App environment name'
    }
    
    found_vars = {}
    for var, description in aca_vars.items():
        value = os.environ.get(var)
        if value:
            found_vars[var] = value
            # Don't show secrets in full
            if 'SECRET' in var or 'HEADER' in var:
                display_value = value[:8] + "..." if len(value) > 8 else value
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    if found_vars:
        print(f"\n✅ Found {len(found_vars)} ACA-related environment variables")
        
        # If we have MSI_ENDPOINT or IDENTITY_ENDPOINT, we're likely in ACA
        if 'MSI_ENDPOINT' in found_vars or 'IDENTITY_ENDPOINT' in found_vars:
            print("✅ Appears to be running in Azure Container App environment")
            return True
        else:
            print("⚠️ Some environment variables found, but unclear if in ACA")
            return False
    else:
        print("❌ No ACA environment variables found")
        print("💡 This script might not be running in Azure Container App")
        return False

async def test_managed_identity_token():
    """Test getting a token using managed identity."""
    print("\n🎫 Testing Managed Identity Token...")
    
    try:
        # Try to use managed identity credential
        managed_credential = ManagedIdentityCredential()
        
        # Try to get a token for Azure Maps
        token_request = managed_credential.get_token("https://atlas.microsoft.com/.default")
        
        if token_request and token_request.token:
            print("✅ Managed identity token obtained successfully")
            print(f"   • Token length: {len(token_request.token)} characters")
            print(f"   • Expires at: {token_request.expires_on}")
            return token_request.token
        else:
            print("❌ Failed to get managed identity token")
            return None
            
    except Exception as e:
        print(f"❌ Managed identity token failed: {e}")
        print("\n💡 Managed identity troubleshooting:")
        print("   • Ensure managed identity is enabled on the Container App")
        print("   • Check that the identity has been assigned appropriate roles")
        print("   • Verify the Container App has been restarted after identity assignment")
        return None

async def test_azure_maps_with_managed_identity(token):
    """Test Azure Maps access using managed identity token."""
    print("\n🗺️ Testing Azure Maps Access with Managed Identity...")
    
    try:
        # Use the token to make a request to Azure Maps
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test with a simple geocoding request
        url = "https://atlas.microsoft.com/search/address/json"
        params = {
            'api-version': '1.0',
            'query': 'Charlotte, NC'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    features = result.get('results', [])
                    print("✅ Azure Maps access successful with managed identity")
                    print(f"   • Response status: {response.status}")
                    print(f"   • Results found: {len(features)}")
                    if features:
                        pos = features[0].get('position', {})
                        print(f"   • Sample coordinates: {pos.get('lat', 'N/A')}, {pos.get('lon', 'N/A')}")
                    return True
                else:
                    print(f"❌ Azure Maps request failed with status: {response.status}")
                    response_text = await response.text()
                    print(f"   • Error response: {response_text[:200]}...")
                    return False
                    
    except Exception as e:
        print(f"❌ Azure Maps test failed: {e}")
        print("\n💡 Azure Maps troubleshooting:")
        print("   • Check that the managed identity has 'Azure Maps Data Reader' role")
        print("   • Verify the role assignment scope includes your Azure Maps account")
        print("   • Ensure the Azure Maps account is in the same subscription")
        return False

async def main():
    """Main diagnostic function."""
    print("🔍 ACA Managed Identity Diagnostic Tool (Python Version)")
    print("=" * 60)
    
    # Test Azure authentication
    credential = await test_azure_authentication()
    
    # Check if we're in ACA environment
    in_aca = await check_aca_managed_identity_manual()
    
    if in_aca:
        print("\n✅ Running in Azure Container App environment")
        
        # Test managed identity token
        token = await test_managed_identity_token()
        
        if token:
            # Test Azure Maps access
            maps_success = await test_azure_maps_with_managed_identity(token)
            
            print("\n📊 FINAL SUMMARY")
            print("=" * 30)
            print(f"   • Azure Container App: ✅ Detected")
            print(f"   • Managed Identity: ✅ Working")
            print(f"   • Azure Maps Access: {'✅ Working' if maps_success else '❌ Failed'}")
            
            if not maps_success:
                print(f"\n🔧 NEXT STEPS")
                print(f"   1. Check Azure Maps role assignment in Azure Portal")
                print(f"   2. Assign 'Azure Maps Data Reader' role to the Container App's managed identity")
                print(f"   3. Restart the Container App after role assignment")
                print(f"   4. Wait 5-10 minutes for role propagation")
        else:
            print("\n📊 FINAL SUMMARY")
            print("=" * 30)
            print(f"   • Azure Container App: ✅ Detected")
            print(f"   • Managed Identity: ❌ Not working")
            print(f"   • Azure Maps Access: ❌ Cannot test")
            
            print(f"\n🔧 NEXT STEPS")
            print(f"   1. Enable system-assigned managed identity on the Container App")
            print(f"   2. Restart the Container App")
            print(f"   3. Run this diagnostic again")
    else:
        print("\n⚠️ Not running in Azure Container App environment")
        print("💡 This diagnostic is designed to run inside an Azure Container App")
        print("   • If you're testing locally, use subscription key authentication")
        print("   • If you're in ACA but variables aren't detected, check the deployment")

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
