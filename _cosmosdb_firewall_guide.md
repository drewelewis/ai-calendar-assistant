# CosmosDB Firewall Configuration Guide

Your CosmosDB account is blocking connections from your public IP address. Here are several ways to fix this:

## Option 1: Add Your Current IP (Recommended for Development)
```bash
# Get your current IP
curl https://api.ipify.org

# Add it to CosmosDB firewall
az cosmosdb update \
  --name ai-calendar-assistant-cosmosdb \
  --resource-group devops-ai-rg \
  --ip-range-filter "69.123.143.84"
```

## Option 2: Enable Azure Portal Access
```bash
az cosmosdb update \
  --name ai-calendar-assistant-cosmosdb \
  --resource-group devops-ai-rg \
  --ip-range-filter "0.0.0.0"
```

## Option 3: Allow Multiple IPs or IP Ranges
```bash
# Allow multiple IPs (comma-separated)
az cosmosdb update \
  --name ai-calendar-assistant-cosmosdb \
  --resource-group devops-ai-rg \
  --ip-range-filter "69.123.143.84,192.168.1.0/24"
```

## Option 4: Enable Access from Azure Services
```bash
az cosmosdb update \
  --name ai-calendar-assistant-cosmosdb \
  --resource-group devops-ai-rg \
  --enable-virtual-network true
```

## Option 5: Disable Firewall (Not Recommended for Production)
```bash
# Remove all IP restrictions (allows access from anywhere)
az cosmosdb update \
  --name ai-calendar-assistant-cosmosdb \
  --resource-group devops-ai-rg \
  --ip-range-filter ""
```

## Checking Current Firewall Rules
```bash
az cosmosdb show \
  --name ai-calendar-assistant-cosmosdb \
  --resource-group devops-ai-rg \
  --query "{ipRules: ipRules, virtualNetworkEnabled: isVirtualNetworkFilterEnabled}"
```

## Important Notes

1. **IP Changes**: Your public IP may change if you're on a dynamic IP connection
2. **Propagation Time**: Firewall changes can take 1-5 minutes to take effect
3. **Security**: For production, use Virtual Networks instead of public IP allowlists
4. **Azure Portal**: IP `0.0.0.0` allows access from Azure Portal and Azure services

## Troubleshooting

If you continue to get firewall errors:
1. Wait 2-3 minutes for changes to propagate
2. Verify your current IP hasn't changed: `curl https://api.ipify.org`
3. Check firewall rules are applied correctly
4. Try the management script: `_cosmosdb_manage_firewall.bat`
