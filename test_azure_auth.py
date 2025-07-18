#!/usr/bin/env python3
"""
Comprehensive Azure Authentication Test Script
Tests all Azure services used by the AI Calendar Assistant to diagnose AAD token issues.
"""

import os
import asyncio
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, AzureCliCredential, InteractiveBrowserCredential
from azure.cosmos import CosmosClient
from azure.core.exceptions import ClientAuthenticationError
import aiohttp
import json
from datetime import datetime

# Load console output for consistent formatting
try:
    from telemetry.console_output import console_info, console_error, console_warning, console_success
except ImportError:
    # Fallback if telemetry not available
    def console_info(msg, module="TEST"): print(f"[INFO] {msg}")
    def console_error(msg, module="TEST"): print(f"[ERROR] {msg}")
    def console_warning(msg, module="TEST"): print(f"[WARNING] {msg}")
    def console_success(msg, module="TEST"): print(f"[SUCCESS] {msg}")

class AzureAuthenticationTester:
    """Comprehensive Azure authentication testing for AI Calendar Assistant"""
    
    def __init__(self):
        load_dotenv()
        self.test_results = {}
        self.working_credentials = {}
        
    def print_header(self, title):
        """Print formatted section header"""
        console_info("=" * 60, "AUTH_TEST")
        console_info(f" {title}")
        console_info("=" * 60, "AUTH_TEST")
        
    def print_subheader(self, title):
        """Print formatted subsection header"""
        console_info(f"\n🔍 {title}", "AUTH_TEST")
        console_info("-" * 40, "AUTH_TEST")
        
    async def test_credential_methods(self):
        """Test different Azure credential authentication methods"""
        self.print_subheader("Testing Azure Credential Methods")
        
        # Define credentials to test in order of preference
        credentials_to_test = [
            ("Azure CLI Credential", AzureCliCredential),
            ("Environment Credential", EnvironmentCredential),
            ("Default Azure Credential", DefaultAzureCredential),
            ("Managed Identity Credential", ManagedIdentityCredential),
        ]
        
        # Test each credential method
        for name, credential_class in credentials_to_test:
            try:
                console_info(f"Testing {name}...", "AUTH_TEST")
                
                # Create credential
                if name == "Default Azure Credential":
                    credential = credential_class(
                        exclude_interactive_browser_credential=True,
                        exclude_visual_studio_code_credential=True
                    )
                else:
                    credential = credential_class()
                
                # Test with different scopes
                scopes_to_test = [
                    ("Azure Resource Management", "https://management.azure.com/.default"),
                    ("Microsoft Graph", "https://graph.microsoft.com/.default"),
                    ("Azure CosmosDB", "https://cosmos.azure.com/.default"),
                ]
                
                credential_results = {}
                for scope_name, scope in scopes_to_test:
                    try:
                        token = credential.get_token(scope)
                        if token and token.token:
                            credential_results[scope_name] = "✅ Success"
                            console_success(f"  {scope_name}: Token acquired", "AUTH_TEST")
                        else:
                            credential_results[scope_name] = "❌ No token"
                            console_error(f"  {scope_name}: No token returned", "AUTH_TEST")
                    except Exception as e:
                        credential_results[scope_name] = f"❌ {str(e)[:50]}..."
                        console_error(f"  {scope_name}: {e}", "AUTH_TEST")
                
                self.test_results[name] = credential_results
                
                # If any scope worked, save this credential
                if any("✅" in result for result in credential_results.values()):
                    self.working_credentials[name] = credential
                    console_success(f"{name} has working scopes!", "AUTH_TEST")
                    
            except Exception as e:
                console_error(f"{name} initialization failed: {e}", "AUTH_TEST")
                self.test_results[name] = {"error": str(e)}
    
    async def test_cosmosdb_connection(self):
        """Test CosmosDB connection and RBAC permissions"""
        self.print_subheader("Testing CosmosDB Connection")
        
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        cosmos_database = os.getenv("COSMOS_DATABASE", "CalendarAssistant")
        cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
        
        if not cosmos_endpoint:
            console_warning("COSMOS_ENDPOINT not configured - skipping CosmosDB test", "AUTH_TEST")
            return
            
        console_info(f"Testing connection to: {cosmos_endpoint}", "AUTH_TEST")
        console_info(f"Database: {cosmos_database}, Container: {cosmos_container}", "AUTH_TEST")
        
        # Test with working credentials
        for cred_name, credential in self.working_credentials.items():
            if "Azure CosmosDB" in self.test_results.get(cred_name, {}) and "✅" in self.test_results[cred_name]["Azure CosmosDB"]:
                try:
                    console_info(f"Testing CosmosDB with {cred_name}...", "AUTH_TEST")
                    
                    # Create CosmosDB client
                    client = CosmosClient(cosmos_endpoint, credential=credential)
                    
                    # Test database operations
                    try:
                        databases = list(client.list_databases())
                        console_success(f"✅ Listed {len(databases)} databases", "AUTH_TEST")
                        
                        # Check if our database exists
                        db_names = [db['id'] for db in databases]
                        if cosmos_database in db_names:
                            console_success(f"✅ Found database '{cosmos_database}'", "AUTH_TEST")
                            
                            # Test container access
                            try:
                                database = client.get_database_client(cosmos_database)
                                containers = list(database.list_containers())
                                console_success(f"✅ Listed {len(containers)} containers", "AUTH_TEST")
                                
                                container_names = [c['id'] for c in containers]
                                if cosmos_container in container_names:
                                    console_success(f"✅ Found container '{cosmos_container}'", "AUTH_TEST")
                                    
                                    # Test read/write permissions
                                    try:
                                        container = database.get_container_client(cosmos_container)
                                        
                                        # Try to read (this tests read permissions)
                                        query = "SELECT TOP 1 * FROM c"
                                        items = list(container.query_items(query=query, enable_cross_partition_query=True))
                                        console_success(f"✅ Read permissions confirmed", "AUTH_TEST")
                                        
                                        # Try to write a test document (this tests write permissions)
                                        test_doc = {
                                            "id": f"auth-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                                            "session_id": "auth-test",
                                            "test": True,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        
                                        container.create_item(test_doc)
                                        console_success(f"✅ Write permissions confirmed", "AUTH_TEST")
                                        
                                        # Clean up test document
                                        container.delete_item(test_doc["id"], partition_key=test_doc["session_id"])
                                        console_success(f"✅ Delete permissions confirmed", "AUTH_TEST")
                                        
                                    except Exception as e:
                                        console_error(f"❌ Container operations failed: {e}", "AUTH_TEST")
                                else:
                                    console_warning(f"Container '{cosmos_container}' not found. Available: {container_names}", "AUTH_TEST")
                            except Exception as e:
                                console_error(f"❌ Container listing failed: {e}", "AUTH_TEST")
                        else:
                            console_warning(f"Database '{cosmos_database}' not found. Available: {db_names}", "AUTH_TEST")
                            
                    except Exception as e:
                        console_error(f"❌ Database operations failed: {e}", "AUTH_TEST")
                        
                except Exception as e:
                    console_error(f"❌ CosmosDB client creation failed: {e}", "AUTH_TEST")
                    
                break  # Only test with first working credential
            
    async def test_microsoft_graph_connection(self):
        """Test Microsoft Graph API connection"""
        self.print_subheader("Testing Microsoft Graph API Connection")
        
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        
        if not tenant_id or not client_id:
            console_warning("Microsoft Graph credentials not configured - skipping Graph test", "AUTH_TEST")
            return
            
        console_info(f"Tenant ID: {tenant_id}", "AUTH_TEST")
        console_info(f"Client ID: {client_id}", "AUTH_TEST")
        
        # Test with working credentials
        for cred_name, credential in self.working_credentials.items():
            if "Microsoft Graph" in self.test_results.get(cred_name, {}) and "✅" in self.test_results[cred_name]["Microsoft Graph"]:
                try:
                    console_info(f"Testing Microsoft Graph with {cred_name}...", "AUTH_TEST")
                    
                    # Get access token
                    token = credential.get_token("https://graph.microsoft.com/.default")
                    
                    # Test Graph API call
                    headers = {
                        "Authorization": f"Bearer {token.token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        # Test basic Graph endpoint
                        async with session.get("https://graph.microsoft.com/v1.0/me", headers=headers) as response:
                            if response.status == 200:
                                user_data = await response.json()
                                console_success(f"✅ User profile access: {user_data.get('displayName', 'Unknown')}", "AUTH_TEST")
                            else:
                                error_text = await response.text()
                                console_error(f"❌ User profile failed ({response.status}): {error_text}", "AUTH_TEST")
                        
                        # Test calendar access
                        async with session.get("https://graph.microsoft.com/v1.0/me/calendar", headers=headers) as response:
                            if response.status == 200:
                                console_success(f"✅ Calendar access confirmed", "AUTH_TEST")
                            else:
                                error_text = await response.text()
                                console_error(f"❌ Calendar access failed ({response.status}): {error_text}", "AUTH_TEST")
                                
                except Exception as e:
                    console_error(f"❌ Microsoft Graph test failed: {e}", "AUTH_TEST")
                    
                break  # Only test with first working credential
    
    async def test_azure_maps_connection(self):
        """Test Azure Maps API connection"""
        self.print_subheader("Testing Azure Maps API Connection")
        
        maps_subscription_key = os.getenv("AZURE_MAPS_SUBSCRIPTION_KEY")
        maps_client_id = os.getenv("AZURE_MAPS_CLIENT_ID")
        
        if not maps_subscription_key and not maps_client_id:
            console_warning("Azure Maps credentials not configured - skipping Maps test", "AUTH_TEST")
            return
            
        if maps_subscription_key:
            console_info("Testing with subscription key authentication", "AUTH_TEST")
            try:
                async with aiohttp.ClientSession() as session:
                    url = "https://atlas.microsoft.com/search/poi/json"
                    params = {
                        "api-version": "1.0",
                        "subscription-key": maps_subscription_key,
                        "query": "coffee",
                        "lat": 47.6062,
                        "lon": -122.3321,
                        "limit": 1
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            results_count = len(data.get("results", []))
                            console_success(f"✅ Azure Maps API working - found {results_count} POI results", "AUTH_TEST")
                        else:
                            error_text = await response.text()
                            console_error(f"❌ Azure Maps API failed ({response.status}): {error_text}", "AUTH_TEST")
                            
            except Exception as e:
                console_error(f"❌ Azure Maps test failed: {e}", "AUTH_TEST")
        
        if maps_client_id:
            console_info("Testing with managed identity authentication", "AUTH_TEST")
            # Test with working credentials that support Azure Resource Management
            for cred_name, credential in self.working_credentials.items():
                if "Azure Resource Management" in self.test_results.get(cred_name, {}) and "✅" in self.test_results[cred_name]["Azure Resource Management"]:
                    try:
                        token = credential.get_token("https://atlas.microsoft.com/.default")
                        console_success(f"✅ Azure Maps token acquired with {cred_name}", "AUTH_TEST")
                        break
                    except Exception as e:
                        console_error(f"❌ Azure Maps token failed with {cred_name}: {e}", "AUTH_TEST")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        self.print_header("🎯 AUTHENTICATION TEST SUMMARY")
        
        console_info("Credential Method Results:", "AUTH_TEST")
        for method, results in self.test_results.items():
            console_info(f"\n📋 {method}:", "AUTH_TEST")
            if isinstance(results, dict) and "error" not in results:
                for scope, result in results.items():
                    status_icon = "✅" if "✅" in result else "❌"
                    console_info(f"  {status_icon} {scope}: {result}", "AUTH_TEST")
            else:
                error_msg = results.get("error", str(results))
                console_error(f"  ❌ {error_msg}", "AUTH_TEST")
        
        # Recommendations
        console_info(f"\n🔧 RECOMMENDATIONS:", "AUTH_TEST")
        
        working_creds = len(self.working_credentials)
        if working_creds > 0:
            console_success(f"✅ Found {working_creds} working credential method(s)", "AUTH_TEST")
            console_info("Your authentication setup is working for:", "AUTH_TEST")
            for cred_name in self.working_credentials.keys():
                console_info(f"  • {cred_name}", "AUTH_TEST")
        else:
            console_error("❌ No working credential methods found", "AUTH_TEST")
            console_info("To fix AAD token issues:", "AUTH_TEST")
            console_info("1. Run 'az login' to authenticate with Azure CLI", "AUTH_TEST")
            console_info("2. Ensure you have appropriate permissions on Azure resources", "AUTH_TEST")
            console_info("3. For production: Enable managed identity on your App Service/Container App", "AUTH_TEST")
            console_info("4. For CI/CD: Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID", "AUTH_TEST")
        
        console_info(f"\n📝 Next Steps:", "AUTH_TEST")
        console_info("1. Address any ❌ failed authentication methods above", "AUTH_TEST")
        console_info("2. Verify Azure resource permissions match your app's needs", "AUTH_TEST") 
        console_info("3. Test your application's functionality with: python main.py", "AUTH_TEST")
        console_info("4. Check Azure portal RBAC assignments if issues persist", "AUTH_TEST")

async def main():
    """Main test function"""
    tester = AzureAuthenticationTester()
    
    tester.print_header("🔐 AI CALENDAR ASSISTANT - AZURE AUTHENTICATION TEST")
    console_info("Testing Azure authentication for all services used by the application...", "AUTH_TEST")
    console_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "AUTH_TEST")
    
    # Run all tests
    await tester.test_credential_methods()
    await tester.test_cosmosdb_connection()
    await tester.test_microsoft_graph_connection()
    await tester.test_azure_maps_connection()
    
    # Print summary
    tester.print_summary()
    
    # Final status
    working_count = len(tester.working_credentials)
    if working_count > 0:
        console_success(f"\n🎉 Authentication test completed! {working_count} method(s) working.", "AUTH_TEST")
    else:
        console_error(f"\n❌ Authentication test failed! No working methods found.", "AUTH_TEST")
        console_info("See recommendations above to resolve AAD token issues.", "AUTH_TEST")

if __name__ == "__main__":
    print("🚀 Starting comprehensive Azure authentication test...")
    asyncio.run(main())
