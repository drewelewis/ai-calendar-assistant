#!/usr/bin/env python3
"""
CosmosDB Permissions Checker
Tests both data plane and control plane permissions for your Azure identities
"""

import os
import asyncio
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, AzureCliCredential, EnvironmentCredential
from azure.cosmos import CosmosClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
import requests

def print_header(title):
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title):
    print(f"\n🔍 {title}")
    print("-" * 40)

async def check_cosmosdb_permissions():
    """Check CosmosDB data and control plane permissions"""
    load_dotenv()
    
    print_header("COSMOSDB PERMISSIONS CHECK")
    
    # Extract relevant IDs from environment
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    cosmos_database = os.getenv("COSMOS_DATABASE", "CalendarAssistant")
    cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    cosmosdb_account = os.getenv("AZURE_COSMOSDB_ACCOUNT")
    managed_identity_id = os.getenv("AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID")
    client_id = os.getenv("ENTRA_GRAPH_APPLICATION_CLIENT_ID")
    tenant_id = os.getenv("ENTRA_GRAPH_APPLICATION_TENANT_ID")
    
    print(f"📋 Configuration:")
    print(f"  CosmosDB Endpoint: {cosmos_endpoint}")
    print(f"  Database: {cosmos_database}")
    print(f"  Container: {cosmos_container}")
    print(f"  Subscription: {subscription_id}")
    print(f"  Resource Group: {resource_group}")
    print(f"  CosmosDB Account: {cosmosdb_account}")
    print(f"  Managed Identity ID: {managed_identity_id}")
    print(f"  Service Principal ID: {client_id}")
    print(f"  Tenant ID: {tenant_id}")
    
    if not cosmos_endpoint:
        print("❌ COSMOS_ENDPOINT not configured!")
        return
    
    # Test different credential methods
    credentials_to_test = [
        ("Azure CLI Credential", AzureCliCredential()),
        ("Environment Credential (Service Principal)", EnvironmentCredential()),
        ("Default Azure Credential", DefaultAzureCredential()),
    ]
    
    working_credential = None
    
    for cred_name, credential in credentials_to_test:
        print_section(f"Testing {cred_name}")
        
        try:
            # Test basic token acquisition
            token = credential.get_token("https://management.azure.com/.default")
            if token and token.token:
                print(f"✅ {cred_name}: Token acquired successfully")
                working_credential = credential
                break
            else:
                print(f"❌ {cred_name}: No token returned")
        except Exception as e:
            print(f"❌ {cred_name}: {str(e)}")
    
    if not working_credential:
        print("\n❌ No working credential found! Please run 'az login' or set environment variables.")
        return
    
    # Test Data Plane Permissions
    print_section("DATA PLANE PERMISSIONS TEST")
    
    try:
        # Create CosmosDB client for data plane operations
        cosmos_client = CosmosClient(cosmos_endpoint, credential=working_credential)
        
        print("🧪 Testing data plane access...")
        
        # Test 1: List databases (requires read access)
        try:
            databases = list(cosmos_client.list_databases())
            print(f"✅ Read databases: Found {len(databases)} databases")
            db_names = [db['id'] for db in databases]
            print(f"   Available databases: {db_names}")
            
            if cosmos_database in db_names:
                print(f"✅ Target database '{cosmos_database}' exists")
            else:
                print(f"❌ Target database '{cosmos_database}' not found")
                
        except Exception as e:
            print(f"❌ List databases failed: {e}")
        
        # Test 2: Database operations
        if cosmos_database:
            try:
                database = cosmos_client.get_database_client(cosmos_database)
                containers = list(database.list_containers())
                print(f"✅ Read containers: Found {len(containers)} containers")
                
                container_names = [c['id'] for c in containers]
                print(f"   Available containers: {container_names}")
                
                if cosmos_container in container_names:
                    print(f"✅ Target container '{cosmos_container}' exists")
                    
                    # Test 3: Container read/write operations
                    try:
                        container = database.get_container_client(cosmos_container)
                        
                        # Test read
                        query = "SELECT TOP 1 * FROM c"
                        items = list(container.query_items(query=query, enable_cross_partition_query=True))
                        print(f"✅ Read items: Query executed successfully")
                        
                        # Test write
                        test_doc = {
                            "id": f"permission-test-{os.urandom(4).hex()}",
                            "session_id": "permission-test",
                            "test": True,
                            "purpose": "checking data plane write permissions"
                        }
                        
                        created_item = container.create_item(test_doc)
                        print(f"✅ Write permissions: Document created")
                        
                        # Test delete
                        container.delete_item(created_item["id"], partition_key=created_item["session_id"])
                        print(f"✅ Delete permissions: Document deleted")
                        
                    except Exception as e:
                        print(f"❌ Container operations failed: {e}")
                        if "Forbidden" in str(e):
                            print("   💡 This suggests missing data plane RBAC roles")
                            print("   💡 Required role: 'Cosmos DB Built-in Data Contributor'")
                        
                else:
                    print(f"❌ Target container '{cosmos_container}' not found")
                    
            except Exception as e:
                print(f"❌ Database operations failed: {e}")
                
    except Exception as e:
        print(f"❌ CosmosDB client creation failed: {e}")
        if "Forbidden" in str(e):
            print("   💡 This suggests missing data plane RBAC roles")
    
    # Test Control Plane Permissions
    print_section("CONTROL PLANE PERMISSIONS TEST")
    
    if subscription_id and resource_group and cosmosdb_account:
        try:
            # Create management client for control plane operations
            mgmt_client = CosmosDBManagementClient(working_credential, subscription_id)
            
            print("🧪 Testing control plane access...")
            
            # Test 1: Get CosmosDB account
            try:
                account = mgmt_client.database_accounts.get(resource_group, cosmosdb_account)
                print(f"✅ Read account: {account.name}")
                print(f"   Location: {account.location}")
                print(f"   Status: {account.provisioning_state}")
            except Exception as e:
                print(f"❌ Get account failed: {e}")
                if "AuthorizationFailed" in str(e):
                    print("   💡 This suggests missing control plane RBAC roles")
                    print("   💡 Required role: 'Cosmos DB Account Reader Role' or 'Contributor'")
            
            # Test 2: List SQL databases
            try:
                sql_databases = mgmt_client.sql_resources.list_sql_databases(resource_group, cosmosdb_account)
                db_list = list(sql_databases)
                print(f"✅ List SQL databases: Found {len(db_list)} databases")
            except Exception as e:
                print(f"❌ List SQL databases failed: {e}")
            
            # Test 3: Get SQL role assignments (RBAC)
            try:
                role_assignments = mgmt_client.sql_resources.list_sql_role_assignments(resource_group, cosmosdb_account)
                assignments = list(role_assignments)
                print(f"✅ List role assignments: Found {len(assignments)} assignments")
                
                print("   📋 Current RBAC assignments:")
                for assignment in assignments:
                    print(f"      - ID: {assignment.name}")
                    print(f"        Principal: {assignment.principal_id}")
                    print(f"        Role: {assignment.role_definition_id}")
                    print(f"        Scope: {assignment.scope}")
                    
            except Exception as e:
                print(f"❌ List role assignments failed: {e}")
            
        except Exception as e:
            print(f"❌ Management client creation failed: {e}")
    else:
        print("❌ Missing required environment variables for control plane testing")
        print("   Required: SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_COSMOSDB_ACCOUNT")
    
    # Check current user identity
    print_section("CURRENT USER IDENTITY")
    
    try:
        # Get current user from Azure CLI
        import subprocess
        result = subprocess.run(["az", "ad", "signed-in-user", "show", "--query", "{id:id,displayName:displayName,userPrincipalName:userPrincipalName}", "--output", "json"], 
                              capture_output=True, text=True, check=True)
        import json
        user_info = json.loads(result.stdout)
        print(f"✅ Current user:")
        print(f"   ID: {user_info.get('id', 'Unknown')}")
        print(f"   Name: {user_info.get('displayName', 'Unknown')}")
        print(f"   UPN: {user_info.get('userPrincipalName', 'Unknown')}")
        
        current_user_id = user_info.get('id')
        
    except Exception as e:
        print(f"❌ Failed to get current user: {e}")
        current_user_id = None
    
    # Provide recommendations
    print_section("RECOMMENDATIONS")
    
    print("📝 To fix missing permissions:")
    print("\n🔹 Data Plane RBAC (for application data access):")
    print("   1. Go to Azure Portal → CosmosDB account → Data Explorer")
    print("   2. Click 'Settings' → 'Access Control (IAM)'")
    print("   3. Add role assignment:")
    print("      - Role: 'Cosmos DB Built-in Data Contributor'")
    if current_user_id:
        print(f"      - Principal: {current_user_id} (current user)")
    if client_id:
        print(f"      - Principal: {client_id} (service principal)")
    if managed_identity_id:
        print(f"      - Principal: {managed_identity_id} (managed identity)")
    
    print("\n🔹 Control Plane RBAC (for account management):")
    print("   1. Go to Azure Portal → CosmosDB account → Access control (IAM)")
    print("   2. Add role assignment:")
    print("      - Role: 'Cosmos DB Account Reader Role' (read) or 'Contributor' (full access)")
    if current_user_id:
        print(f"      - Principal: {current_user_id} (current user)")
    
    print("\n🔹 Alternative: Use Azure CLI commands:")
    if current_user_id and cosmosdb_account and resource_group:
        print(f"   # Grant data plane access to current user")
        print(f"   az cosmosdb sql role assignment create \\")
        print(f"     --account-name {cosmosdb_account} \\")
        print(f"     --resource-group {resource_group} \\")
        print(f"     --scope \"/\" \\")
        print(f"     --principal-id {current_user_id} \\")
        print(f"     --role-definition-name \"Cosmos DB Built-in Data Contributor\"")

if __name__ == "__main__":
    asyncio.run(check_cosmosdb_permissions())
