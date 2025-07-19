#!/usr/bin/env python3
"""
Simple ACA Managed Identity Check

This script performs basic checks for Azure Container App managed identity configuration.
"""

import os
import sys

def check_environment_variables():
    """Check for Azure and ACA-related environment variables."""
    print("🔍 Checking Environment Variables...")
    print("=" * 40)
    
    # Azure managed identity environment variables
    azure_vars = {
        'AZURE_CLIENT_ID': 'Azure Client ID',
        'AZURE_TENANT_ID': 'Azure Tenant ID', 
        'AZURE_SUBSCRIPTION_ID': 'Azure Subscription ID',
        'MSI_ENDPOINT': 'Managed Service Identity endpoint',
        'MSI_SECRET': 'Managed Service Identity secret',
        'IDENTITY_ENDPOINT': 'Identity endpoint (ACA)',
        'IDENTITY_HEADER': 'Identity header (ACA)',
        'AZURE_MAPS_SUBSCRIPTION_KEY': 'Azure Maps Subscription Key',
        'AZURE_MAPS_CLIENT_ID': 'Azure Maps Client ID'
    }
    
    found_vars = {}
    missing_vars = []
    
    for var, description in azure_vars.items():
        value = os.environ.get(var)
        if value:
            found_vars[var] = value
            # Mask sensitive values
            if any(word in var.lower() for word in ['secret', 'key', 'header']):
                display_value = f"{value[:8]}{'*' * (len(value) - 8)}" if len(value) > 8 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
    
    print(f"\n📊 Summary:")
    print(f"   • Found variables: {len(found_vars)}")
    print(f"   • Missing variables: {len(missing_vars)}")
    
    return found_vars, missing_vars

def analyze_aca_environment(found_vars):
    """Analyze if we're in an ACA environment and what's configured."""
    print(f"\n🏗️ Azure Container App Analysis...")
    print("=" * 40)
    
    # Check for ACA-specific variables
    aca_indicators = ['MSI_ENDPOINT', 'IDENTITY_ENDPOINT', 'IDENTITY_HEADER']
    aca_found = [var for var in aca_indicators if var in found_vars]
    
    if aca_found:
        print("✅ Azure Container App environment detected")
        print(f"   • ACA indicators found: {', '.join(aca_found)}")
        
        # Check authentication method
        if 'AZURE_MAPS_SUBSCRIPTION_KEY' in found_vars:
            print("⚠️ Using subscription key authentication")
            print("   • Consider switching to managed identity for production")
        elif any(var in found_vars for var in ['MSI_ENDPOINT', 'IDENTITY_ENDPOINT']):
            print("✅ Managed identity environment available")
            print("   • Ready for managed identity authentication")
        
        return True
    else:
        print("❌ Not detected as Azure Container App environment")
        print("💡 This might be running locally or in a different environment")
        return False

def check_azure_packages():
    """Check if required Azure packages are available."""
    print(f"\n📦 Checking Azure Packages...")
    print("=" * 40)
    
    required_packages = [
        ('azure.identity', 'Azure Identity SDK'),
        ('aiohttp', 'HTTP client for async requests'),
        ('azure.core', 'Azure Core library')
    ]
    
    available_packages = []
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Available")
            available_packages.append(package)
        except ImportError:
            print(f"❌ {package}: Missing")
            missing_packages.append(package)
    
    print(f"\n📊 Package Summary:")
    print(f"   • Available: {len(available_packages)}")
    print(f"   • Missing: {len(missing_packages)}")
    
    if missing_packages:
        print(f"\n💡 To install missing packages:")
        print(f"   pip install azure-identity aiohttp azure-core")
    
    return len(missing_packages) == 0

def provide_recommendations(found_vars, in_aca, packages_ok):
    """Provide specific recommendations based on the analysis."""
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 40)
    
    if not in_aca:
        print("🏠 Local Development:")
        print("   • Use AZURE_MAPS_SUBSCRIPTION_KEY for local testing")
        print("   • Test managed identity in Azure Container App environment")
        
    elif in_aca and 'AZURE_MAPS_SUBSCRIPTION_KEY' in found_vars:
        print("🔄 Migration to Managed Identity:")
        print("   1. Enable system-assigned managed identity on Container App")
        print("   2. Assign 'Azure Maps Data Reader' role to the managed identity")
        print("   3. Remove AZURE_MAPS_SUBSCRIPTION_KEY environment variable")
        print("   4. Restart the Container App")
        
    elif in_aca and 'MSI_ENDPOINT' in found_vars:
        print("🔐 Managed Identity Setup:")
        print("   1. Verify managed identity is enabled in Azure Portal")
        print("   2. Check role assignment: 'Azure Maps Data Reader'")
        print("   3. Ensure role scope includes your Azure Maps account")
        print("   4. Wait 5-10 minutes for role propagation")
        
    if not packages_ok:
        print("📦 Package Installation:")
        print("   • Install required Azure packages for full functionality")
        print("   • Run: pip install azure-identity aiohttp azure-core")

def main():
    """Main diagnostic function."""
    print("🔍 Simple ACA Managed Identity Check")
    print("=" * 50)
    
    try:
        # Check environment variables
        found_vars, missing_vars = check_environment_variables()
        
        # Analyze ACA environment
        in_aca = analyze_aca_environment(found_vars)
        
        # Check Azure packages
        packages_ok = check_azure_packages()
        
        # Provide recommendations
        provide_recommendations(found_vars, in_aca, packages_ok)
        
        print(f"\n📋 NEXT STEPS")
        print("=" * 30)
        
        if in_aca:
            print("1. Use the detailed checklist: ACA_MANAGED_IDENTITY_CHECKLIST.md")
            print("2. Run the full diagnostic: python check_aca_python.py")
            print("3. Test Azure Maps access in your application")
        else:
            print("1. Deploy to Azure Container App for managed identity testing")
            print("2. Use subscription key authentication for local development")
            print("3. Follow the ACA setup guide when ready to deploy")
            
    except Exception as e:
        print(f"❌ Error during check: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🚫 Check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
