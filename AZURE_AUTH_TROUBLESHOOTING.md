# Azure Authentication Troubleshooting Guide

## 🚨 "AAD token does not exist" Error - Troubleshooting Steps

### Immediate Fixes

1. **Azure CLI Login**
   ```cmd
   az login
   az account set --subscription "your-subscription-name"
   ```

2. **Check Current Authentication**
   ```cmd
   az account show
   az ad signed-in-user show
   ```

3. **Clear Cached Tokens**
   ```cmd
   az account clear
   az login
   ```

### Environment Setup

4. **Set Environment Variables** (if using service principal)
   ```cmd
   set AZURE_TENANT_ID=your-tenant-id
   set AZURE_CLIENT_ID=your-client-id
   set AZURE_CLIENT_SECRET=your-client-secret
   ```

5. **Check .env File** (create if missing)
   ```
   AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
   AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
   AZURE_CLIENT_SECRET=your-secret-here
   COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
   ```

### Permission Issues

6. **Common RBAC Roles Needed**
   - **CosmosDB**: `Cosmos DB Built-in Data Contributor`
   - **Microsoft Graph**: `Directory.Read.All`, `Calendars.ReadWrite`
   - **Azure Maps**: `Azure Maps Data Reader`

7. **Check Resource Permissions**
   ```cmd
   # List role assignments for current user
   az role assignment list --assignee $(az ad signed-in-user show --query id --output tsv)
   ```

### Portal-Specific Issues

8. **Azure Portal RBAC Page**
   - Go to resource → Access control (IAM)
   - Check if your user/app has required roles
   - Add role assignment if missing

9. **Tenant Context**
   - Ensure you're in the correct Azure AD tenant
   - Check if resource is in a different subscription

### Application-Specific Fixes

10. **App Registration (if using service principal)**
    - Azure AD → App registrations → Your app
    - API permissions → Grant admin consent
    - Certificates & secrets → Create new secret

11. **Managed Identity (for Azure deployment)**
    ```cmd
    # Enable system-assigned managed identity
    az webapp identity assign --name your-app --resource-group your-rg
    ```

### Testing Commands

Run these to verify your setup:

```cmd
# Test basic authentication
.\test_azure_auth.bat

# Test Python authentication
python quick_auth_test.py

# Test comprehensive services
python test_azure_auth.py
```

### Most Common Causes

1. **Not logged in**: Run `az login`
2. **Wrong tenant**: Switch with `az account set --subscription`
3. **Missing permissions**: Add RBAC roles in Azure portal
4. **Expired tokens**: Clear cache with `az account clear` then `az login`
5. **Wrong environment**: Check AZURE_TENANT_ID matches your tenant

### Next Steps

1. Run `.\test_azure_auth.bat` to diagnose the issue
2. Fix any ❌ items shown in the diagnostic
3. Test your application with `python main.py`
4. If still failing, check Azure portal → Azure AD → Sign-in logs for errors

### Emergency Reset

If nothing works:
```cmd
az logout
az account clear
az login --tenant your-tenant-id
az account set --subscription "your-subscription"
```

Then verify with:
```cmd
az account show
az ad signed-in-user show
```
