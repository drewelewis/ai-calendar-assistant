#!/usr/bin/env python3
"""
Simple script to check Azure Container App environment variables
specifically for Azure Maps configuration.
"""

import subprocess
import json
import sys

def run_az_command(command):
    """Run an Azure CLI command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"❌ Error running command: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🔍 Azure Container App Environment Variables Check")
    print("=" * 60)
    
    # Command to get environment variables
    command = 'az containerapp show --name aiwrapper --resource-group devops-ai-rg --query "properties.template.containers[0].env" --output json'
    
    print("📋 Retrieving environment variables...")
    result = run_az_command(command)
    
    if not result:
        print("❌ Failed to retrieve environment variables")
        print("💡 Make sure you're authenticated: az login")
        return
    
    try:
        env_vars = json.loads(result)
        
        print(f"✅ Found {len(env_vars)} environment variables")
        print("\n🗺️ Azure Maps Configuration:")
        print("-" * 30)
        
        # Check for Azure Maps related variables
        azure_maps_vars = [var for var in env_vars if 'AZURE_MAPS' in var.get('name', '')]
        
        if azure_maps_vars:
            for var in azure_maps_vars:
                name = var.get('name', '')
                value = var.get('value', '')
                
                if name == 'AZURE_MAPS_SUBSCRIPTION_KEY':
                    if value:
                        print(f"⚠️  {name}: PRESENT (This will override managed identity!)")
                        print("🔧 RECOMMENDATION: Remove this environment variable")
                    else:
                        print(f"✅ {name}: NOT SET (Good for managed identity)")
                else:
                    # Show other Azure Maps variables
                    status = "SET" if value else "NOT SET"
                    print(f"📝 {name}: {status}")
        else:
            print("❌ No Azure Maps environment variables found")
        
        print("\n🔐 Managed Identity Related Variables:")
        print("-" * 40)
        
        # Check for managed identity variables
        identity_vars = ['AZURE_CLIENT_ID', 'AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID']
        for var_name in identity_vars:
            var = next((v for v in env_vars if v.get('name') == var_name), None)
            if var:
                value = var.get('value', '')
                status = "SET" if value else "NOT SET"
                print(f"📝 {var_name}: {status}")
            else:
                print(f"❌ {var_name}: NOT FOUND")
        
        print("\n📊 Summary:")
        print("-" * 20)
        
        # Check if subscription key is blocking managed identity
        sub_key_var = next((v for v in env_vars if v.get('name') == 'AZURE_MAPS_SUBSCRIPTION_KEY'), None)
        if sub_key_var and sub_key_var.get('value'):
            print("🚨 ISSUE: AZURE_MAPS_SUBSCRIPTION_KEY is set")
            print("   This will prevent managed identity authentication!")
            print("   Remove this environment variable to fix 401 errors.")
        else:
            print("✅ AZURE_MAPS_SUBSCRIPTION_KEY is not set")
            print("   Managed identity authentication should work.")
            print("   If you're still getting 401 errors, check:")
            print("   1. Azure Maps account has 'disableLocalAuth: true'")
            print("   2. Managed identity has 'Azure Maps Data Reader' role")
            print("   3. Container app was restarted after configuration changes")
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
