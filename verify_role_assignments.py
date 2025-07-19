#!/usr/bin/env python3
"""
Azure Role Assignment Verification Script

This script helps you verify the exact role assignments for your managed identity.
Run this to see what roles are assigned and at what scope.
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

def check_role_assignments():
    """Check role assignments for the specific managed identity."""
    identity_id = "5238e629-da2f-4bb0-aea5-14d45526c864"
    
    print("🔍 Checking Role Assignments")
    print("=" * 50)
    print(f"Managed Identity: {identity_id}")
    print()
    
    # Get all role assignments for this identity
    command = f'az role assignment list --assignee {identity_id} -o json'
    result = run_az_command(command)
    
    if not result:
        print("❌ Failed to get role assignments")
        return False
    
    try:
        assignments = json.loads(result)
        
        if not assignments:
            print("❌ NO ROLE ASSIGNMENTS FOUND!")
            print("💡 This is the problem - your managed identity has no role assignments.")
            print()
            print("🔧 TO FIX:")
            print("1. Go to Azure Portal → Azure Maps → Access Control (IAM)")
            print("2. Add role assignment: 'Azure Maps Data Reader'")
            print("3. Assign to your Container App's managed identity")
            return False
        
        print(f"📋 Found {len(assignments)} role assignment(s):")
        print()
        
        maps_reader_found = False
        for i, assignment in enumerate(assignments, 1):
            role_name = assignment.get('roleDefinitionName', 'Unknown')
            scope = assignment.get('scope', 'Unknown')
            principal_type = assignment.get('principalType', 'Unknown')
            
            print(f"Assignment {i}:")
            print(f"   • Role: {role_name}")
            print(f"   • Scope: {scope}")
            print(f"   • Type: {principal_type}")
            
            # Check if this is Azure Maps Data Reader
            if 'azure maps data reader' in role_name.lower():
                maps_reader_found = True
                print(f"   ✅ Found Azure Maps Data Reader role!")
                
                # Analyze the scope
                if '/providers/Microsoft.Maps/accounts/' in scope:
                    print(f"   ✅ Scope is at Azure Maps account level")
                    print(f"   ✅ This should work - role assignment looks correct")
                elif '/resourceGroups/' in scope and '/providers/Microsoft.Maps/accounts/' not in scope:
                    print(f"   ⚠️  Scope is at Resource Group level")
                    print(f"   💡 This might work, but Azure Maps account level is preferred")
                elif '/subscriptions/' in scope and '/resourceGroups/' not in scope:
                    print(f"   ⚠️  Scope is at Subscription level")
                    print(f"   💡 This should work but is overly broad")
                else:
                    print(f"   ❌ Scope is unclear or incorrect")
            else:
                print(f"   ⚠️  Not an Azure Maps role")
            
            print()
        
        if not maps_reader_found:
            print("❌ NO AZURE MAPS DATA READER ROLE FOUND!")
            print("💡 This is the problem!")
            print()
            print("🔧 TO FIX:")
            print("1. Go to Azure Portal → Azure Maps → Access Control (IAM)")
            print("2. Add role assignment: 'Azure Maps Data Reader'")
            print("3. Assign to your Container App's managed identity")
            return False
        else:
            print("🤔 Azure Maps Data Reader role is assigned...")
            print("💡 Possible issues:")
            print("   • Role propagation delay (wait 10-15 minutes)")
            print("   • Azure Maps account region mismatch")
            print("   • Cached permissions (restart Container App)")
            print("   • Wrong Azure Maps account")
            return True
            
    except json.JSONDecodeError:
        print("❌ Failed to parse role assignments")
        return False

def check_azure_maps_accounts():
    """List Azure Maps accounts to help identify the correct one."""
    print("\n🗺️ Available Azure Maps Accounts")
    print("=" * 40)
    
    command = 'az maps account list -o json'
    result = run_az_command(command)
    
    if not result:
        print("❌ Failed to list Azure Maps accounts")
        return
    
    try:
        accounts = json.loads(result)
        
        if not accounts:
            print("❌ No Azure Maps accounts found")
            return
        
        for i, account in enumerate(accounts, 1):
            name = account.get('name', 'Unknown')
            resource_group = account.get('resourceGroup', 'Unknown')
            location = account.get('location', 'Unknown')
            account_id = account.get('id', 'Unknown')
            
            print(f"Account {i}:")
            print(f"   • Name: {name}")
            print(f"   • Resource Group: {resource_group}")
            print(f"   • Location: {location}")
            print(f"   • Full ID: {account_id}")
            print()
            
            # Check if there are role assignments for this specific account
            print(f"   🔍 Checking role assignments for this account...")
            identity_id = "5238e629-da2f-4bb0-aea5-14d45526c864"
            scope_command = f'az role assignment list --assignee {identity_id} --scope "{account_id}" -o json'
            scope_result = run_az_command(scope_command)
            
            if scope_result:
                try:
                    scope_assignments = json.loads(scope_result)
                    if scope_assignments:
                        print(f"   ✅ Found {len(scope_assignments)} role assignment(s) for this account")
                        for assignment in scope_assignments:
                            role = assignment.get('roleDefinitionName', 'Unknown')
                            print(f"      - {role}")
                    else:
                        print(f"   ❌ No role assignments found for this specific account")
                        print(f"   💡 Try assigning 'Azure Maps Data Reader' to this account specifically")
                except:
                    print(f"   ⚠️  Could not parse role assignments for this account")
            else:
                print(f"   ⚠️  Could not check role assignments for this account")
            
            print()
            
    except json.JSONDecodeError:
        print("❌ Failed to parse Azure Maps accounts")

def main():
    """Main verification function."""
    print("🧪 Azure Role Assignment Verification")
    print("=" * 50)
    print("This script will help identify why your managed identity")
    print("is getting 401 errors from Azure Maps.")
    print()
    
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
    
    # Check role assignments
    has_role = check_role_assignments()
    
    # List Azure Maps accounts
    check_azure_maps_accounts()
    
    print("📊 SUMMARY")
    print("=" * 20)
    if has_role:
        print("✅ Azure Maps Data Reader role is assigned")
        print("🤔 If you're still getting 401 errors:")
        print("   • Wait 15 minutes for propagation")
        print("   • Restart your Container App")
        print("   • Verify you're using the correct Azure Maps account")
        print("   • Check Azure Maps account is in the same region")
    else:
        print("❌ Missing or incorrect role assignment")
        print("💡 Follow the fix instructions above")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🚫 Verification cancelled")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)
