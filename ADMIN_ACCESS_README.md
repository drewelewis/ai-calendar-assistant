# AI Calendar Assistant - Admin Access Management

This directory contains PowerShell scripts to manage administrative access to your AI Calendar Assistant Azure resources. These scripts allow you to delegate administrative responsibilities to other users when you're away.

## 📋 Prerequisites

Before running these scripts, ensure you have:

1. **Azure PowerShell Modules** installed:
   ```powershell
   Install-Module -Name Az -Force -AllowClobber
   ```

2. **Required Permissions**: You must have `Owner` or `User Access Administrator` role on the subscription or resource group.

3. **Azure Authentication**: Login to Azure before running scripts:
   ```powershell
   Connect-AzAccount
   ```

## 🔧 Scripts Overview

### `Configure-AdminAccess.ps1`
Grants comprehensive administrative permissions to a specified user across all AI Calendar Assistant resources.

### `Remove-AdminAccess.ps1`
Removes administrative permissions from a specified user.

## 🚀 Quick Start

### Grant Admin Access
```powershell
# Basic usage - auto-discovers resources
.\Configure-AdminAccess.ps1 -UserPrincipalName "admin@yourcompany.com"

# Specify resource group explicitly
.\Configure-AdminAccess.ps1 -UserPrincipalName "admin@yourcompany.com" -ResourceGroupName "ai-calendar-rg"

# Preview changes without applying (recommended first run)
.\Configure-AdminAccess.ps1 -UserPrincipalName "admin@yourcompany.com" -WhatIf
```

### Remove Admin Access
```powershell
# Remove all admin permissions
.\Remove-AdminAccess.ps1 -UserPrincipalName "admin@yourcompany.com"

# Preview what would be removed
.\Remove-AdminAccess.ps1 -UserPrincipalName "admin@yourcompany.com" -WhatIf
```

## 🔐 Permissions Granted

The admin access configuration grants the following permissions based on your production resources:

### Resource Group Level
- **Contributor**: General resource management capabilities

### Individual Resources

| Resource Type | Roles Granted | Capabilities |
|---------------|---------------|--------------|
| **Container Apps Environment** | Contributor | Manage scaling, configuration, networking |
| **Container App (aiwrapper)** | ContainerApp Reader, Contributor | Monitor and manage the main application |
| **Cosmos DB** | DocumentDB Account Contributor, Cosmos DB Account Reader | Manage database, collections, and data |
| **Application Insights** | Application Insights Component Contributor, Monitoring Reader | View telemetry and configure monitoring |
| **Log Analytics Workspace** | Log Analytics Contributor, Log Analytics Reader | Access logs and create queries |
| **Azure OpenAI** | Cognitive Services OpenAI Contributor, Cognitive Services User | Manage AI models and deployments |
| **Azure Managed Redis** | Redis Cache Contributor | Configure caching settings |
| **Azure Maps** | Contributor | Manage location services |
| **Azure Bot Service** | Contributor | Configure bot channels and settings |
| **App Service & Plan** | Website Contributor, Web Plan Contributor | Manage web app hosting |
| **Managed Identity** | Managed Identity Contributor, Managed Identity Operator | Manage service authentication |

## 🎯 Admin User Capabilities

Once configured, the admin user can:

### 📊 Monitoring & Troubleshooting
- View application performance metrics in Application Insights
- Access and query logs in Log Analytics
- Monitor container app health and scaling
- Check bot service interaction logs

### ⚙️ Configuration Management
- Scale container apps up/down based on demand
- Update container app environment variables
- Modify Azure OpenAI model deployments
- Configure Redis cache settings
- Update bot service channels and messaging endpoint

### 🔧 Maintenance Operations
- Restart container applications
- View and manage Cosmos DB collections
- Update application configurations
- Manage Azure Maps API keys
- Configure monitoring alerts and dashboards

### 🚨 Incident Response
- Access real-time logs for troubleshooting
- Scale resources during high traffic
- Restart failed services
- Update configuration for emergency fixes

## 📚 Admin User Onboarding

After granting access, share these instructions with the new admin:

### 1. Install Required Tools
```powershell
# Install Azure CLI
winget install -e --id Microsoft.AzureCLI

# Install Azure PowerShell
Install-Module -Name Az -Force -AllowClobber

# Install Container Apps extension
az extension add --name containerapp
```

### 2. Login to Azure
```powershell
# PowerShell
Connect-AzAccount

# Azure CLI
az login
```

### 3. Key Resources to Monitor

**Primary Application:**
- Resource Group: `[Your Resource Group Name]`
- Container App: `aiwrapper` 
- Environment: `ai-aca-environment`

**Data & Storage:**
- Cosmos DB: `ai-calendar-assistant-cosmosdb`
- Redis Cache: `managed-managed-redis`

**AI Services:**
- Azure OpenAI: `devops-ai-openai-instance1`
- Bot Service: `botd8b23c`

**Monitoring:**
- Application Insights: `ai-calendar-assistant-insights`
- Log Analytics: `ai-calendar-assistant-workspace`

### 4. Common Administrative Tasks

**Check Application Health:**
```bash
az containerapp show --resource-group [RG_NAME] --name aiwrapper --query "properties.provisioningState"
```

**View Recent Logs:**
```bash
az containerapp logs show --resource-group [RG_NAME] --name aiwrapper --follow
```

**Scale Application:**
```bash
az containerapp update --resource-group [RG_NAME] --name aiwrapper --min-replicas 1 --max-replicas 5
```

## 🛡️ Security Considerations

### Best Practices
- **Principle of Least Privilege**: Only grant admin access when necessary
- **Time-Limited Access**: Remove access when no longer needed
- **Audit Trail**: All administrative actions are logged in Azure Activity Log
- **MFA Required**: Ensure admin users have multi-factor authentication enabled

### Monitoring Admin Activity
- Check Azure Activity Log for admin actions
- Set up alerts for critical resource changes
- Review access regularly and remove when not needed

### Emergency Access Removal
```powershell
# Quick removal of all permissions
.\Remove-AdminAccess.ps1 -UserPrincipalName "admin@yourcompany.com"
```

## 🔧 Troubleshooting

### Common Issues

**Error: "Insufficient privileges"**
- Ensure you have Owner or User Access Administrator role
- Check if you're in the correct subscription context

**Error: "User not found"**
- Verify the email address is correct
- Ensure the user exists in your Azure AD tenant
- Check for typos in the UserPrincipalName

**Error: "Resource group not found"**
- Verify the resource group name is correct
- Ensure you're in the right subscription
- Use auto-discovery by omitting the ResourceGroupName parameter

### Support Commands
```powershell
# Check current Azure context
Get-AzContext

# List available subscriptions
Get-AzSubscription

# Find AI Calendar Assistant resources
Get-AzResource | Where-Object { $_.Name -like "*calendar*" -or $_.Name -like "*wrapper*" }

# Check existing role assignments for a user
Get-AzRoleAssignment -UserPrincipalName "admin@yourcompany.com"
```

## 📞 Emergency Contacts

When configuring admin access, ensure your team knows:

1. **Primary Owner**: [Your Contact Information]
2. **Backup Admins**: [List of configured admin users]
3. **Azure Support**: Available through Azure Portal
4. **Documentation**: This README and Azure documentation

## 🔄 Regular Maintenance

### Monthly Review Checklist
- [ ] Review list of admin users
- [ ] Remove access for users no longer needing it
- [ ] Verify admin users still require access
- [ ] Check Azure Activity Log for unusual admin activity
- [ ] Update admin contact information if needed

### Access Rotation
Consider rotating admin access quarterly:
1. Document current admin users
2. Remove old access
3. Grant fresh access with new expiration dates
4. Update team contact lists

---

## 📖 Additional Resources

- [Azure RBAC Documentation](https://docs.microsoft.com/en-us/azure/role-based-access-control/)
- [Container Apps Management](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure OpenAI Service Management](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Cosmos DB Administration](https://docs.microsoft.com/en-us/azure/cosmos-db/)

---

**⚠️ Important**: Always test with `-WhatIf` parameter first to preview changes before applying them.
