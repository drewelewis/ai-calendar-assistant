#!/usr/bin/env python3
"""
Azure Maps 401 Error Diagnostic Script
This script helps diagnose and fix Azure Maps authentication issues in production.

Based on your .env configuration:
- Container App: aiwrapper
- Resource Group: devops-ai-rg  
- Managed Identity ID: 5238e629-da2f-4bb0-aea5-14d45526c864
- Subscription: d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e
"""

import os
import asyncio
import json
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

def print_banner(title):
    """Print a formatted banner."""
    print("\n" + "="*80)
    print(f"🔍 {title}")
    print("="*80)

def print_step(step_num, title):
    """Print a formatted step."""
    print(f"\n🚀 STEP {step_num}: {title}")
    print("-" * 60)

def print_azure_cli_commands():
    """Print the Azure CLI commands to run for diagnosis."""
    
    # Get values from environment
    subscription_id = os.getenv("SUBSCRIPTION_ID", "d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP", "devops-ai-rg")
    container_app = os.getenv("AZURE_CONTAINER_APP_NAME", "aiwrapper")
    managed_identity_id = os.getenv("AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID", "5238e629-da2f-4bb0-aea5-14d45526c864")
    
    print_banner("AZURE MAPS 401 ERROR DIAGNOSTIC COMMANDS")
    
    print(f"""
📋 CONFIGURATION SUMMARY:
   • Subscription ID: {subscription_id}
   • Resource Group: {resource_group}
   • Container App: {container_app}
   • Managed Identity ID: {managed_identity_id}
   • Azure Maps Client ID: {os.getenv("AZURE_MAPS_CLIENT_ID", "11b89b23-5401-42af-bce2-79381ec74ef4")}
   • Subscription Key: {'❌ Commented out (GOOD!)' if not os.getenv("AZURE_MAPS_SUBSCRIPTION_KEY") else '⚠️  Still set - should be removed'}
""")

    print_step(1, "Check Container App Managed Identity Status")
    print(f"""
Run this command to check if managed identity is enabled:

az containerapp identity show --name {container_app} --resource-group {resource_group}

Expected output should show:
- "type": "SystemAssigned"
- "principalId": "{managed_identity_id}"
""")

    print_step(2, "Check Current Role Assignments")
    print(f"""
Run this command to see what roles are currently assigned:

az role assignment list --assignee {managed_identity_id} --all --output table

Look for: "Azure Maps Data Reader" role
""")

    print_step(3, "Find Your Azure Maps Account")
    print(f"""
First, find your Azure Maps account name:

az maps account list --subscription {subscription_id} --output table

Note the account name from the output.
""")

    print_step(4, "Assign Azure Maps Data Reader Role (if missing)")
    print(f"""
Replace <AZURE_MAPS_ACCOUNT_NAME> with your actual Azure Maps account name:

az role assignment create \\
  --assignee {managed_identity_id} \\
  --role "Azure Maps Data Reader" \\
  --scope "/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Maps/accounts/<AZURE_MAPS_ACCOUNT_NAME>"

OR assign at resource group level (broader scope):

az role assignment create \\
  --assignee {managed_identity_id} \\
  --role "Azure Maps Data Reader" \\
  --scope "/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
""")

    print_step(5, "Restart Container App (IMPORTANT!)")
    print(f"""
After making role assignments, restart your container app:

az containerapp restart --name {container_app} --resource-group {resource_group}

⚠️  This is CRITICAL - role changes may not take effect without restart!
""")

    print_step(6, "Test Authentication")
    print("""
After restart, test your application to see if the 401 error is resolved.
You can also run this diagnostic script again to test the connection.
""")

async def test_azure_maps_connection():
    """Test Azure Maps connection with current configuration."""
    print_banner("TESTING AZURE MAPS CONNECTION")
    
    try:
        # Import your Azure Maps operations
        from operations.azure_maps_operations import AzureMapsOperations
        
        print("🔄 Creating AzureMapsOperations instance...")
        
        async with AzureMapsOperations() as maps_client:
            print("✅ AzureMapsOperations created successfully")
            
            print("🔗 Testing connection...")
            result = await maps_client.test_connection()
            
            print("\n📊 CONNECTION TEST RESULTS:")
            print("-" * 40)
            for key, value in result.items():
                status_emoji = "✅" if key == "overall_status" and value == "success" else "❌" if key == "overall_status" and value == "error" else "ℹ️"
                print(f"   {status_emoji} {key}: {value}")
            
            if result.get("overall_status") == "success":
                print("\n🎉 SUCCESS! Azure Maps authentication is working!")
                return True
            elif result.get("overall_status") == "error" and "401" in str(result.get("error", "")):
                print("\n❌ 401 ERROR DETECTED!")
                print("💡 This confirms the authentication issue.")
                print("🔧 Please run the Azure CLI commands above to fix the role assignments.")
                return False
            else:
                print(f"\n⚠️  Unexpected result: {result}")
                return False
                
    except ImportError as e:
        print(f"❌ Could not import AzureMapsOperations: {e}")
        print("💡 Make sure you're running this from your project directory")
        return False
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def analyze_environment():
    """Analyze the current environment configuration."""
    print_banner("ENVIRONMENT ANALYSIS")
    
    # Check key environment variables
    env_checks = [
        ("AZURE_MAPS_CLIENT_ID", "Azure Maps Client ID"),
        ("AZURE_MAPS_SUBSCRIPTION_KEY", "Azure Maps Subscription Key"),
        ("SUBSCRIPTION_ID", "Azure Subscription ID"),
        ("AZURE_RESOURCE_GROUP", "Azure Resource Group"),
        ("AZURE_CONTAINER_APP_NAME", "Container App Name"),
        ("AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID", "Managed Identity ID"),
        ("MSI_ENDPOINT", "Managed Identity Endpoint"),
        ("IDENTITY_ENDPOINT", "Identity Endpoint"),
        ("IDENTITY_HEADER", "Identity Header")
    ]
    
    print("🔍 Environment Variable Check:")
    print("-" * 40)
    
    for env_var, description in env_checks:
        value = os.getenv(env_var)
        if env_var == "AZURE_MAPS_SUBSCRIPTION_KEY":
            # Special handling for subscription key
            if value:
                print(f"   ⚠️  {description}: SET (should be removed for production)")
            else:
                print(f"   ✅ {description}: NOT SET (good for managed identity)")
        elif env_var in ["MSI_ENDPOINT", "IDENTITY_ENDPOINT", "IDENTITY_HEADER"]:
            # These are only available in Azure runtime
            if value:
                print(f"   ✅ {description}: SET (Azure environment detected)")
            else:
                print(f"   ❌ {description}: NOT SET (not in Azure environment)")
        else:
            if value:
                # Mask sensitive values
                display_value = value if len(value) < 20 else f"{value[:8]}...{value[-4:]}"
                print(f"   ✅ {description}: {display_value}")
            else:
                print(f"   ❌ {description}: NOT SET")
    
    print("\n🔍 Authentication Mode Analysis:")
    print("-" * 40)
    
    if os.getenv("AZURE_MAPS_SUBSCRIPTION_KEY"):
        print("   🔑 CURRENT MODE: Subscription Key Authentication")
        print("   💡 RECOMMENDATION: Remove AZURE_MAPS_SUBSCRIPTION_KEY for production")
        print("   🎯 TARGET MODE: Managed Identity Authentication")
    else:
        print("   🔐 CURRENT MODE: Managed Identity Authentication")
        print("   ✅ GOOD: This is the recommended production setup")
    
    # Check if running in Azure
    if os.getenv("MSI_ENDPOINT") or os.getenv("IDENTITY_ENDPOINT"):
        print("   🌐 ENVIRONMENT: Azure Container App (managed identity available)")
    else:
        print("   💻 ENVIRONMENT: Local/Non-Azure (managed identity not available)")
        print("   ⚠️  For local testing, you might need subscription key or Azure CLI auth")

async def main():
    """Main diagnostic function."""
    print_banner("Azure Maps 401 Error Diagnostic Tool")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Analyze environment
    analyze_environment()
    
    # Print Azure CLI commands
    print_azure_cli_commands()
    
    # Test connection if possible
    print("\n" + "="*80)
    response = input("🤔 Would you like to test the Azure Maps connection now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        success = await test_azure_maps_connection()
        
        if not success:
            print_banner("NEXT STEPS TO FIX 401 ERROR")
            print("""
1. Run the Azure CLI commands above to check and assign roles
2. Restart your Container App after role assignment  
3. Test again
4. If still failing, check Azure Maps account configuration

🔗 Helpful links:
   • Azure Maps Authentication: https://docs.microsoft.com/en-us/azure/azure-maps/azure-maps-authentication
   • Container Apps Managed Identity: https://docs.microsoft.com/en-us/azure/container-apps/managed-identity
""")
    else:
        print("\n✅ Diagnostic complete. Run the Azure CLI commands above to fix the 401 error.")

if __name__ == "__main__":
    asyncio.run(main())
