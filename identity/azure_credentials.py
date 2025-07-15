from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential
from azure.core.exceptions import ClientAuthenticationError
import re

class AzureCredentials(Exception):
    """Custom exception for client authentication errors."""

    @staticmethod
    def validate_cosmos_endpoint(endpoint):
        """Validate CosmosDB endpoint URL format"""
        if not endpoint:
            return False, "CosmosDB endpoint is empty"
            
        # Remove any trailing/leading whitespace
        endpoint = endpoint.strip()
        
        # Check basic URL format
        cosmos_pattern = r'^https://[a-zA-Z0-9-]+\.documents\.azure\.com:443/?$'
        if not re.match(cosmos_pattern, endpoint):
            return False, f"Invalid CosmosDB URL format. Expected: https://account-name.documents.azure.com:443/"
            
        return True, endpoint

    @staticmethod
    def get_credential():
        """
        Get Azure credentials with fallback options optimized for production.
        Tries multiple authentication methods in order of preference:
        1. Managed Identity (for Azure-hosted applications - production)
        2. Environment variables (for CI/CD and explicit service principal auth)
        3. DefaultAzureCredential (includes Azure CLI, VS Code, etc. - development)
        """
        import logging
        import os
        logger = logging.getLogger(__name__)
        
        # Validate CosmosDB endpoint if provided
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        if cosmos_endpoint:
            is_valid, result = AzureCredentials.validate_cosmos_endpoint(cosmos_endpoint)
            if not is_valid:
                logger.error(f"❌ CosmosDB URL validation failed: {result}")
                logger.error(f"   Current value: '{cosmos_endpoint}'")
                logger.error(f"   Please fix your COSMOS_ENDPOINT in .env file")
                raise ClientAuthenticationError(f"Invalid CosmosDB endpoint: {result}")
            else:
                logger.info(f"✅ CosmosDB endpoint validation passed: {result}")
        
        # First, try Managed Identity (best for production Azure environments)
        try:
            credential = ManagedIdentityCredential()
            # Test the credential with a shorter timeout for faster fallback
            token = credential.get_token("https://cosmos.azure.com/.default", timeout=10)
            logger.info("✅ Successfully authenticated using Managed Identity")
            return credential
        except Exception as e:
            logger.warning(f"⚠ ManagedIdentityCredential failed: {e}")
        
        # Second, try Environment Variables (for explicit service principal configuration)
        try:
            credential = EnvironmentCredential()
            # Test the credential
            token = credential.get_token("https://cosmos.azure.com/.default", timeout=10)
            logger.info("✅ Successfully authenticated using Environment Credential")
            return credential
        except Exception as e:
            logger.warning(f"⚠ EnvironmentCredential failed: {e}")
        
        # Third, try DefaultAzureCredential (includes CLI, VS Code, etc.)
        try:
            # Exclude managed identity here since we already tried it explicitly above
            credential = DefaultAzureCredential(
                exclude_managed_identity_credential=True,  # Already tried above
                exclude_visual_studio_code_credential=False,
                exclude_environment_credential=True,  # Already tried above
                exclude_azure_cli_credential=False,
                exclude_interactive_browser_credential=True  # Not suitable for production
            )
            # Test the credential
            token = credential.get_token("https://cosmos.azure.com/.default", timeout=15)
            logger.info("✅ Successfully authenticated using DefaultAzureCredential")
            return credential
        except Exception as e:
            logger.warning(f"⚠ DefaultAzureCredential failed: {e}")
            
        # Provide detailed troubleshooting information
        error_msg = """
❌ All Azure authentication methods failed. Troubleshooting steps:

For PRODUCTION (Azure-hosted apps):
1. Ensure your App Service/Container App has a System-assigned or User-assigned Managed Identity enabled
2. Grant the Managed Identity 'Cosmos DB Built-in Data Contributor' role on your CosmosDB account
3. Verify local authentication is disabled on CosmosDB (required for RBAC)

For CI/CD:
1. Set environment variables: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
2. Ensure the Service Principal has appropriate CosmosDB permissions

For DEVELOPMENT:
1. Run: az login
2. Ensure your account has access to the CosmosDB resource

Connection string fallback is available via COSMOS_KEY environment variable.
See _cosmosdb_auth_setup.md for detailed setup instructions.
        """
        
        raise ClientAuthenticationError(error_msg.strip())
