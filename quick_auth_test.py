#!/usr/bin/env python3
"""
Quick Azure Authentication Diagnostic
Simple test to identify AAD token issues
"""

import os
import sys
from azure.identity import DefaultAzureCredential, AzureCliCredential, EnvironmentCredential

def test_credential(credential_name, credential):
    """Test a credential and return results"""
    print(f"\n🔍 Testing {credential_name}...")
    
    try:
        # Test basic Azure Resource Management scope
        token = credential.get_token("https://management.azure.com/.default")
        if token and token.token:
            print(f"  ✅ {credential_name}: Successfully acquired token")
            print(f"  📝 Token length: {len(token.token)} characters")
            return True
        else:
            print(f"  ❌ {credential_name}: No token returned")
            return False
    except Exception as e:
        print(f"  ❌ {credential_name}: {str(e)}")
        return False

def main():
    print("🔐 Quick Azure Authentication Test")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    env_vars = [
        "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
        "COSMOS_ENDPOINT", "AZURE_MAPS_SUBSCRIPTION_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Show partial value for security
            if len(value) > 10:
                display_value = f"{value[:6]}...{value[-4:]}"
            else:
                display_value = value[:4] + "..."
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Test credential methods
    print("\n🧪 Testing Credential Methods:")
    working_methods = 0
    
    # Test Azure CLI
    if test_credential("Azure CLI", AzureCliCredential()):
        working_methods += 1
    
    # Test Environment Credential
    if test_credential("Environment Credential", EnvironmentCredential()):
        working_methods += 1
    
    # Test Default Credential
    if test_credential("Default Azure Credential", DefaultAzureCredential()):
        working_methods += 1
    
    # Summary
    print(f"\n🎯 RESULTS:")
    print(f"Working authentication methods: {working_methods}")
    
    if working_methods > 0:
        print("✅ Authentication is working!")
        print("\n💡 If you're still seeing AAD token errors in Azure portal:")
        print("   1. Check your user's permissions in Azure AD")
        print("   2. Verify RBAC assignments on specific resources")
        print("   3. Ensure you're in the correct tenant")
    else:
        print("❌ No authentication methods working!")
        print("\n🔧 To fix AAD token issues:")
        print("   1. Run: az login")
        print("   2. Set environment variables (see .env.example)")
        print("   3. Check Azure permissions")

if __name__ == "__main__":
    main()
