# Azure Infrastructure Deployment Guide

This guide walks you through deploying the AI Calendar Assistant infrastructure to Azure using the Azure Developer CLI (azd).

## 🎯 What Gets Deployed

The infrastructure includes:

- **Azure Container Apps** - Hosts the Python FastAPI application
- **Azure OpenAI Service** - Provides GPT-4o model for AI capabilities
- **Azure Cosmos DB** - Stores chat history and session data
- **Azure Key Vault** - Securely stores Microsoft Graph credentials
- **Azure Application Insights** - Monitors application performance and token usage
- **Azure Container Registry** - Stores Docker images
- **Log Analytics Workspace** - Centralized logging
- **Managed Identity** - Secure authentication between services

## 🛠️ Prerequisites

### 1. Install Azure Developer CLI
```bash
# Windows (PowerShell)
winget install microsoft.azd

# macOS
brew tap azure/azd && brew install azd

# Linux
curl -fsSL https://aka.ms/install-azd.sh | bash
```

### 2. Install Azure CLI
```bash
# Windows
winget install -e --id Microsoft.AzureCLI

# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLI | sudo bash
```

### 3. Install Docker (for local testing)
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)

### 4. Set Up Microsoft Graph Application

Before deployment, you need to register an application in Azure AD/Entra:

1. **Register Application**:
   ```bash
   az ad app create --display-name "AI Calendar Assistant" \
     --required-resource-accesses '[
       {
         "resourceAppId": "00000003-0000-0000-c000-000000000000",
         "resourceAccess": [
           {"id": "37f7f235-527c-4136-accd-4a02d197296e", "type": "Scope"},
           {"id": "14dad69e-099b-42c9-810b-d002981feec1", "type": "Scope"},
           {"id": "62a82d76-70ea-41e2-9197-370581804d09", "type": "Scope"},
           {"id": "5b567255-7703-4780-807c-7be8301ae99b", "type": "Scope"}
         ]
       }
     ]'
   ```

2. **Create Client Secret**:
   ```bash
   az ad app credential reset --id <APP_ID> --display-name "AI Calendar Assistant Secret"
   ```

3. **Note the values**:
   - Application (client) ID
   - Client secret
   - Directory (tenant) ID

## 🚀 Quick Deployment

### Option 1: Automated Script (Recommended)

**Windows:**
```cmd
.\deploy-infrastructure.bat
```

**Linux/macOS:**
```bash
./deploy-infrastructure.sh
```

### Option 2: Manual Steps

1. **Set Environment Variables**:
   ```bash
   # Set required Microsoft Graph credentials
   azd env set ENTRA_GRAPH_APPLICATION_CLIENT_ID "your-client-id"
   azd env set ENTRA_GRAPH_APPLICATION_CLIENT_SECRET "your-client-secret"
   azd env set ENTRA_GRAPH_APPLICATION_TENANT_ID "your-tenant-id"
   
   # Optional: Set custom values
   azd env set OPENAI_MODEL_DEPLOYMENT_NAME "gpt-4o"
   azd env set COSMOS_DATABASE "CalendarAssistant"
   azd env set COSMOS_CONTAINER "ChatHistory"
   ```

2. **Login to Azure**:
   ```bash
   az login
   azd auth login
   ```

3. **Initialize and Deploy**:
   ```bash
   # Initialize azd (if not done already)
   azd init --template .
   
   # Preview deployment
   azd provision --preview
   
   # Deploy everything
   azd up
   ```

## ⚙️ Configuration Options

### Environment Variables

You can customize the deployment by setting these environment variables:

```bash
# Azure OpenAI Configuration
azd env set OPENAI_MODEL_DEPLOYMENT_NAME "gpt-4o"        # Model deployment name
azd env set OPENAI_MODEL_NAME "gpt-4o"                   # Model name
azd env set OPENAI_MODEL_VERSION "2024-08-06"            # Model version

# Cosmos DB Configuration
azd env set COSMOS_DATABASE "CalendarAssistant"          # Database name
azd env set COSMOS_CONTAINER "ChatHistory"               # Container name

# Container Configuration
azd env set CONTAINER_IMAGE_TAG "latest"                 # Docker image tag

# Microsoft Graph (Required)
azd env set ENTRA_GRAPH_APPLICATION_CLIENT_ID "your-id"
azd env set ENTRA_GRAPH_APPLICATION_CLIENT_SECRET "your-secret"
azd env set ENTRA_GRAPH_APPLICATION_TENANT_ID "your-tenant"
```

### Deployment Regions

Choose a region that supports all required services:

```bash
# Set deployment location
azd env set AZURE_LOCATION "eastus"  # or westus2, westeurope, etc.
```

**Recommended regions**:
- `eastus` - US East (Virginia)
- `westus2` - US West 2 (Washington)
- `westeurope` - West Europe (Netherlands)
- `southeastasia` - Southeast Asia (Singapore)

## 📊 Post-Deployment

### 1. Verify Deployment

```bash
# Check deployment status
azd show

# View application logs
azd logs

# Get service endpoints
azd env get-values
```

### 2. Test the Application

```bash
# Get the application URL
export APP_URL=$(azd env get-value AZURE_CONTAINER_APP_ENDPOINT)

# Test health endpoint
curl $APP_URL/health

# Test API endpoint
curl -X POST $APP_URL/agent_chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "message": "Hello!"}'
```

### 3. Configure Microsoft Graph Permissions

Grant admin consent for the Graph API permissions:

```bash
# Get the application ID
APP_ID=$(azd env get-value ENTRA_GRAPH_APPLICATION_CLIENT_ID)

# Grant admin consent (requires Global Administrator)
az ad app permission admin-consent --id $APP_ID
```

### 4. Monitor the Application

- **Application Insights**: Monitor performance and view telemetry
- **Container App Logs**: Real-time application logs
- **Cosmos DB**: View stored chat histories
- **Key Vault**: Manage stored secrets

## 🔧 Troubleshooting

### Common Issues

**1. Deployment Fails with Resource Quota Exceeded**
```bash
# Check quotas in your subscription
az vm list-usage --location eastus

# Try a different region
azd env set AZURE_LOCATION "westus2"
azd up
```

**2. Azure OpenAI Service Not Available**
```bash
# Check service availability in region
az cognitiveservices account list-kinds --location eastus

# Request access if needed
# Visit: https://aka.ms/oai/access
```

**3. Container App Won't Start**
```bash
# Check container logs
azd logs

# Verify environment variables
azd env get-values

# Check container health
az containerapp show --name <APP_NAME> --resource-group <RG_NAME>
```

**4. Microsoft Graph Authentication Errors**
```bash
# Verify credentials are set
azd env get-value ENTRA_GRAPH_APPLICATION_CLIENT_ID

# Check application permissions
az ad app permission list --id <APP_ID>

# Grant admin consent
az ad app permission admin-consent --id <APP_ID>
```

### Debugging Commands

```bash
# View all environment variables
azd env get-values

# Show deployment status
azd show --output table

# Stream application logs
azd logs --follow

# Check resource group contents
az resource list --resource-group rg-<ENV_NAME> --output table

# Test container app directly
az containerapp show --name <APP_NAME> --resource-group <RG_NAME>
```

## 🧹 Cleanup

To remove all deployed resources:

```bash
# Delete all resources
azd down --force --purge

# Remove azd environment
azd env list
azd env select <env-name>
azd env delete
```

## 🔄 Updates and Redeployment

### Update Application Code

```bash
# Redeploy with code changes
azd deploy

# Or full redeploy
azd up
```

### Update Infrastructure

```bash
# Modify Bicep files in /infra folder
# Then redeploy
azd provision
```

### Update Environment Variables

```bash
# Set new values
azd env set VARIABLE_NAME "new-value"

# Redeploy to apply changes
azd deploy
```

## 📋 Deployment Checklist

- [ ] Azure CLI installed and logged in
- [ ] Azure Developer CLI installed
- [ ] Microsoft Graph application registered
- [ ] Required permissions granted to Graph application
- [ ] Environment variables set
- [ ] Deployment region supports all services
- [ ] Subscription has sufficient quota
- [ ] Deployment completed successfully
- [ ] Health endpoint responds
- [ ] Application Insights receiving telemetry
- [ ] Microsoft Graph integration working

## 🆘 Support

If you encounter issues:

1. **Check the logs**: `azd logs`
2. **Review the deployment**: `azd show`
3. **Verify environment**: `azd env get-values`
4. **Check Azure portal** for resource status
5. **Review this guide** for common solutions

For additional help, check the [Azure Developer CLI documentation](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/).

---

## 📝 Sample Deployment Output

A successful deployment will show:

```
🎉 Deployment completed successfully!

📊 Resource Information:
Service                       Status    Endpoint
ai-calendar-assistant        Running   https://cal-assist-app-abc123.region.azurecontainerapps.io

🌐 Application URLs:
AZURE_CONTAINER_APP_ENDPOINT=https://cal-assist-app-abc123.region.azurecontainerapps.io

📋 Next Steps:
  1. Test the application health endpoint
  2. Configure Microsoft Graph API permissions if needed
  3. Monitor the application in Azure Application Insights
  4. View logs with: azd logs
```
