#!/usr/bin/env python3
"""
Azure Container App (ACA) Managed Identity Diagnostic Tool

This script helps diagnose ACA managed identity configuration for Azure Maps access.
It checks the managed identity setup, role assignments, and Azure Maps permissions.

Usage:
    python check_aca_managed_identity.py
"""

import subprocess
import json
import sys
import os

# Global variable to store the az command path
AZ_COMMAND = "az"

def run_az_command(command, description):
    """Run an Azure CLI command and return the result."""
    print(f"🔍 {description}...")
    try:
        # Replace 'az' with the full path if needed
        if command.startswith('az '):
            command = command.replace('az ', f'"{AZ_COMMAND}" ', 1)
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Success")
            return result.stdout.strip()
        else:
            print(f"❌ Failed: {result.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_azure_cli():
    """Check if Azure CLI is installed and user is logged in."""
    global AZ_COMMAND
    print("🔧 Checking Azure CLI Setup...")
    
    # Try different az command paths
    az_paths = [
        "az",
        r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
        r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
    ]
    
    for path in az_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                AZ_COMMAND = path
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    else:
        print("❌ Azure CLI not found. Please install Azure CLI first.")
        return False
    
    print("✅ Azure CLI is installed")
    
    # Check if logged in
    result = subprocess.run([AZ_COMMAND, "account", "show"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Not logged into Azure. Please run 'az login' first.")
        return False
    
    account_info = json.loads(result.stdout)
    print(f"✅ Logged in as: {account_info.get('user', {}).get('name', 'Unknown')}")
    print(f"✅ Subscription: {account_info.get('name', 'Unknown')} ({account_info.get('id', 'Unknown')})")
    
    return True

def get_aca_resources():
    """Get all Container Apps in the subscription."""
    print("\n🏗️ Finding Azure Container Apps...")
    
    command = 'az containerapp list --query "[].{name:name, resourceGroup:resourceGroup, location:location}" -o json'
    result = run_az_command(command, "Listing Container Apps")
    
    if result:
        try:
            apps = json.loads(result)
            if apps:
                print(f"📋 Found {len(apps)} Container App(s):")
                for i, app in enumerate(apps, 1):
                    print(f"   {i}. {app['name']} (RG: {app['resourceGroup']}, Location: {app['location']})")
                return apps
            else:
                print("❌ No Container Apps found in this subscription")
                return []
        except json.JSONDecodeError:
            print("❌ Failed to parse Container Apps list")
            return []
    return []

def check_managed_identity(app_name, resource_group):
    """Check managed identity configuration for a specific Container App."""
    print(f"\n🔐 Checking Managed Identity for '{app_name}'...")
    
    # Get Container App details including identity
    command = f'az containerapp show --name {app_name} --resource-group {resource_group} --query "{{identity:identity, name:name}}" -o json'
    result = run_az_command(command, f"Getting identity info for {app_name}")
    
    if not result:
        return None
    
    try:
        app_info = json.loads(result)
        identity = app_info.get('identity')
        
        if not identity:
            print("❌ No managed identity configured")
            print("💡 To enable managed identity:")
            print(f"   az containerapp identity assign --name {app_name} --resource-group {resource_group} --system-assigned")
            return None
        
        identity_type = identity.get('type', '').lower()
        principal_id = identity.get('principalId')
        
        print(f"✅ Managed Identity Type: {identity_type}")
        
        if 'systemassigned' in identity_type and principal_id:
            print(f"✅ System-Assigned Principal ID: {principal_id}")
            return {
                'type': 'system',
                'principal_id': principal_id,
                'app_name': app_name,
                'resource_group': resource_group
            }
        elif 'userassigned' in identity_type:
            user_identities = identity.get('userAssignedIdentities', {})
            if user_identities:
                print(f"✅ User-Assigned Identities: {len(user_identities)}")
                for identity_id, identity_info in user_identities.items():
                    client_id = identity_info.get('clientId')
                    principal_id = identity_info.get('principalId')
                    print(f"   • Identity: {identity_id}")
                    print(f"   • Client ID: {client_id}")
                    print(f"   • Principal ID: {principal_id}")
                
                # Return the first user-assigned identity
                first_identity = next(iter(user_identities.values()))
                return {
                    'type': 'user',
                    'principal_id': first_identity.get('principalId'),
                    'client_id': first_identity.get('clientId'),
                    'app_name': app_name,
                    'resource_group': resource_group
                }
        
        print("❌ Managed identity exists but missing principal ID")
        return None
        
    except json.JSONDecodeError:
        print("❌ Failed to parse Container App identity info")
        return None

def check_azure_maps_accounts():
    """Get Azure Maps accounts in the subscription."""
    print("\n🗺️ Finding Azure Maps Accounts...")
    
    command = 'az maps account list --query "[].{name:name, resourceGroup:resourceGroup, id:id}" -o json'
    result = run_az_command(command, "Listing Azure Maps accounts")
    
    if result:
        try:
            maps_accounts = json.loads(result)
            if maps_accounts:
                print(f"📋 Found {len(maps_accounts)} Azure Maps account(s):")
                for i, account in enumerate(maps_accounts, 1):
                    print(f"   {i}. {account['name']} (RG: {account['resourceGroup']})")
                return maps_accounts
            else:
                print("❌ No Azure Maps accounts found")
                return []
        except json.JSONDecodeError:
            print("❌ Failed to parse Azure Maps accounts list")
            return []
    return []

def check_role_assignments(principal_id, maps_accounts):
    """Check role assignments for the managed identity on Azure Maps accounts."""
    print(f"\n🔑 Checking Role Assignments for Principal ID: {principal_id}")
    
    # Check role assignments for the principal
    command = f'az role assignment list --assignee {principal_id} --query "[].{{roleDefinitionName:roleDefinitionName, scope:scope, principalType:principalType}}" -o json'
    result = run_az_command(command, "Getting role assignments")
    
    if not result:
        print("❌ Failed to get role assignments")
        return False
    
    try:
        assignments = json.loads(result)
        
        if not assignments:
            print("❌ No role assignments found for this managed identity")
            print("💡 You need to assign roles to access Azure Maps")
            return False
        
        print(f"📋 Found {len(assignments)} role assignment(s):")
        
        maps_reader_found = False
        for assignment in assignments:
            role_name = assignment.get('roleDefinitionName', 'Unknown')
            scope = assignment.get('scope', 'Unknown')
            principal_type = assignment.get('principalType', 'Unknown')
            
            print(f"   • Role: {role_name}")
            print(f"     Scope: {scope}")
            print(f"     Type: {principal_type}")
            
            # Check if this is Azure Maps Data Reader role
            if 'azure maps data reader' in role_name.lower():
                maps_reader_found = True
                
                # Check if the scope matches any of our Maps accounts
                for maps_account in maps_accounts:
                    if maps_account['id'].lower() in scope.lower():
                        print(f"     ✅ Grants access to Azure Maps account: {maps_account['name']}")
        
        if maps_reader_found:
            print("✅ Found Azure Maps Data Reader role assignment")
            return True
        else:
            print("❌ No 'Azure Maps Data Reader' role found")
            print("💡 To assign the role:")
            for maps_account in maps_accounts:
                print(f"   az role assignment create --assignee {principal_id} --role \"Azure Maps Data Reader\" --scope {maps_account['id']}")
            return False
            
    except json.JSONDecodeError:
        print("❌ Failed to parse role assignments")
        return False

def main():
    """Main diagnostic function."""
    print("🔍 Azure Container App Managed Identity Diagnostic Tool")
    print("=" * 60)
    
    # Check Azure CLI setup
    if not check_azure_cli():
        return
    
    # Get Container Apps
    aca_apps = get_aca_resources()
    if not aca_apps:
        print("\n❌ No Container Apps found. Cannot proceed with diagnosis.")
        return
    
    # Get Azure Maps accounts
    maps_accounts = check_azure_maps_accounts()
    if not maps_accounts:
        print("\n❌ No Azure Maps accounts found. Cannot check permissions.")
        return
    
    print("\n" + "="*60)
    print("🔬 DETAILED ANALYSIS")
    print("="*60)
    
    # Check each Container App
    for app in aca_apps:
        app_name = app['name']
        resource_group = app['resourceGroup']
        
        print(f"\n📱 Analyzing Container App: {app_name}")
        print("-" * 40)
        
        # Check managed identity
        identity_info = check_managed_identity(app_name, resource_group)
        
        if identity_info:
            # Check role assignments
            has_maps_access = check_role_assignments(identity_info['principal_id'], maps_accounts)
            
            # Summary for this app
            print(f"\n📊 Summary for {app_name}:")
            print(f"   • Managed Identity: ✅ Configured ({identity_info['type']}-assigned)")
            print(f"   • Azure Maps Access: {'✅ Configured' if has_maps_access else '❌ Missing'}")
            
            if not has_maps_access:
                print(f"\n🔧 To fix Azure Maps access for {app_name}:")
                print(f"   1. Assign 'Azure Maps Data Reader' role to principal ID: {identity_info['principal_id']}")
                print(f"   2. Restart the Container App: az containerapp restart --name {app_name} --resource-group {resource_group}")
        else:
            print(f"\n📊 Summary for {app_name}:")
            print(f"   • Managed Identity: ❌ Not configured")
            print(f"   • Azure Maps Access: ❌ Cannot check without managed identity")
    
    print(f"\n" + "="*60)
    print("💡 GENERAL RECOMMENDATIONS")
    print("="*60)
    print("1. Ensure managed identity is enabled on your Container App")
    print("2. Assign 'Azure Maps Data Reader' role to the managed identity")
    print("3. Use the correct scope (Azure Maps account resource ID)")
    print("4. Wait 5-10 minutes after role assignment for propagation")
    print("5. Restart your Container App after configuration changes")
    print("6. Test the connection from within the Container App environment")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🚫 Diagnostic cancelled by user")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
