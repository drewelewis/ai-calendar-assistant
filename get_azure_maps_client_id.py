#!/usr/bin/env python3
"""
Azure Maps Client ID Helper

This script helps you get the Azure Maps Client ID (unique ID) needed for managed identity authentication.
"""

import subprocess
import json
import sys

def run_az_command(command):
    """Run Azure CLI command and return result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"❌ Command failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_azure_maps_client_id():
    """Get the Azure Maps Client ID from Azure CLI."""
    print("🗺️ Azure Maps Client ID Helper")
    print("=" * 40)
    
    # Check if Azure CLI is available
    test_result = run_az_command("az --version")
    if not test_result:
        print("❌ Azure CLI not available")
        print("💡 Install Azure CLI or run this script in Azure Cloud Shell")
        return
    
    # Check if logged in
    account_result = run_az_command("az account show")
    if not account_result:
        print("❌ Not logged into Azure CLI")
        print("💡 Run 'az login' first")
        return
    
    print("✅ Azure CLI is ready")
    print()
    
    # List Azure Maps accounts
    print("📋 Finding Azure Maps accounts...")
    command = 'az maps account list -o json'
    result = run_az_command(command)
    
    if not result:
        print("❌ Failed to list Azure Maps accounts")
        return
    
    try:
        accounts = json.loads(result)
        
        if not accounts:
            print("❌ No Azure Maps accounts found")
            print("💡 Create an Azure Maps account first")
            return
        
        print(f"Found {len(accounts)} Azure Maps account(s):")
        print()
        
        for i, account in enumerate(accounts, 1):
            name = account.get('name', 'Unknown')
            resource_group = account.get('resourceGroup', 'Unknown')
            location = account.get('location', 'Unknown')
            
            # Get the unique ID (client ID)
            properties = account.get('properties', {})
            unique_id = properties.get('uniqueId', 'Not found')
            
            print(f"Account {i}: {name}")
            print(f"   • Resource Group: {resource_group}")
            print(f"   • Location: {location}")
            print(f"   • Client ID (uniqueId): {unique_id}")
            print()
            
            if unique_id and unique_id != 'Not found':
                print("🎯 TO USE THIS CLIENT ID:")
                print(f"   Set environment variable: AZURE_MAPS_CLIENT_ID={unique_id}")
                print()
                print("   For Container Apps, add this as an environment variable:")
                print(f"   AZURE_MAPS_CLIENT_ID={unique_id}")
                print()
                
                # Also show the command to get it programmatically
                print("📋 Azure CLI Command to get this Client ID:")
                print(f"   az maps account show --name {name} --resource-group {resource_group} --query properties.uniqueId -o tsv")
                print()
        
        # If there's a specific account named "azure-maps-instance" (from the role assignments)
        target_account = None
        for account in accounts:
            if account.get('name') == 'azure-maps-instance':
                target_account = account
                break
        
        if target_account:
            name = target_account.get('name')
            unique_id = target_account.get('properties', {}).get('uniqueId')
            print("🎯 FOUND YOUR TARGET ACCOUNT: azure-maps-instance")
            print(f"   Client ID: {unique_id}")
            print()
            print("💡 This is the account your managed identity has permissions to.")
            print(f"   Use this Client ID: {unique_id}")
        else:
            print("⚠️  Could not find 'azure-maps-instance' account.")
            print("💡 Use the Client ID from the account where you assigned the managed identity roles.")
            
    except json.JSONDecodeError:
        print("❌ Failed to parse Azure Maps accounts")

if __name__ == "__main__":
    try:
        get_azure_maps_client_id()
    except KeyboardInterrupt:
        print("\n🚫 Script cancelled")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)
