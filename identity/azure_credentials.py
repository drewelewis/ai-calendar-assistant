from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential
from azure.core.exceptions import ClientAuthenticationError

class AzureCredentials(Exception):
    """Custom exception for client authentication errors."""

    @staticmethod
    def get_credential():
        """
        Get Azure credentials with fallback options.
        Tries multiple authentication methods in order of preference:
        1. Environment variables (for CI/CD)
        2. Managed Identity (for Azure-hosted applications)
        3. DefaultAzureCredential (interactive/local development)
        """
        try:
            # Try environment credential first (good for CI/CD)
            credential = EnvironmentCredential()
            # Test the credential
            credential.get_token("https://cosmos.azure.com/.default")
            return credential
        except Exception:
            pass
        
        try:
            # Try managed identity (good for Azure-hosted apps)
            credential = ManagedIdentityCredential()
            # Test the credential
            credential.get_token("https://cosmos.azure.com/.default")
            return credential
        except Exception:
            pass
        
        try:
            # Fall back to DefaultAzureCredential (includes interactive auth)
            credential = DefaultAzureCredential(exclude_visual_studio_code_credential=False)
            # Test the credential
            credential.get_token("https://cosmos.azure.com/.default")
            return credential
        except Exception as e:
            raise ClientAuthenticationError(
                f"Failed to authenticate with Azure. Please ensure you are logged in via Azure CLI "
                f"or have appropriate credentials configured. Error: {e}"
            )
