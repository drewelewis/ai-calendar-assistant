# Azure Authentication Setup for CosmosDB

This application uses Azure Active Directory (AAD) authentication for CosmosDB instead of connection keys for enhanced security.

## Prerequisites

1. **Azure CLI**: Install and authenticate with Azure CLI
   ```bash
   az login
   ```

2. **CosmosDB Configuration**: Your CosmosDB account must have:
   - Local Authorization disabled (requires AAD tokens)
   - RBAC enabled for data plane operations

## Required Azure Permissions

Your user account or managed identity needs the following permissions on the CosmosDB account:

1. **Cosmos DB Built-in Data Contributor** role (87a39d53-fc1b-424a-814c-f7e04687dc9e)
   - Allows read/write access to CosmosDB data

## Authentication Methods (in order of preference)

### 1. For CI/CD Pipelines
Set these environment variables:
```bash
AZURE_CLIENT_ID=your-service-principal-client-id
AZURE_CLIENT_SECRET=your-service-principal-client-secret
AZURE_TENANT_ID=your-tenant-id
```

### 2. For Azure-hosted Applications
Use Managed Identity (automatically detected, no configuration needed)

### 3. For Local Development
Use Azure CLI authentication:
```bash
az login
```

## Setting Up CosmosDB RBAC

1. **Create a custom role definition** (if built-in roles aren't available):
   ```bash
   az cosmosdb sql role definition create \
     --account-name <cosmos-account-name> \
     --resource-group <resource-group> \
     --body @_cosmosdb_role-definition.json
   ```

2. **Get the role definition ID**:
   ```bash
   az cosmosdb sql role definition list \
     --account-name <cosmos-account-name> \
     --resource-group <resource-group> \
     --query "[0].id" --output tsv
   ```

3. **Assign permissions** to your user:
   ```bash
   # For your user account
   az cosmosdb sql role assignment create \
     --account-name <cosmos-account-name> \
     --resource-group <resource-group> \
     --scope "/" \
     --principal-id $(az ad signed-in-user show --query id -o tsv) \
     --role-definition-id <role-definition-id>

   # For a service principal
   az cosmosdb sql role assignment create \
     --account-name <cosmos-account-name> \
     --resource-group <resource-group> \
     --scope "/" \
     --principal-id <service-principal-object-id> \
     --role-definition-id <role-definition-id>
   ```

## Environment Variables

Update your `.env` file (no COSMOS_KEY needed):
```bash
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DATABASE=AIAssistant
COSMOS_CONTAINER=ChatHistory
```

## Troubleshooting

### "Unauthorized" Error
- Ensure you're logged in with `az login`
- Verify RBAC permissions are correctly assigned
- Check that local authorization is disabled on CosmosDB

### Authentication Not Working
- Try running `az account show` to verify your current login
- Clear Azure CLI cache: `az account clear` then `az login`
- For service principals, verify environment variables are set correctly

## Security Benefits

- **No hardcoded secrets**: Eliminates the risk of exposing CosmosDB keys
- **Centralized identity management**: Uses Azure AD for authentication
- **Fine-grained permissions**: RBAC allows precise control over data access
- **Audit trail**: All operations are logged through Azure AD
