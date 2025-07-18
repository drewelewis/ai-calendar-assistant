# Azure Maps Connection Troubleshooting Guide

This guide helps you diagnose and resolve connection issues with Azure Maps Service using the enhanced diagnostics in `azure_maps_operations.py`.

## Quick Diagnostics Test

Run the diagnostics test script to get a comprehensive overview:

```bash
python test_azure_maps_diagnostics.py
```

## Enhanced Telemetry Events

The updated Azure Maps operations now emit detailed telemetry events for monitoring and debugging:

### Initialization Events
- `azure_maps_initialization` - Configuration and authentication setup details
- `azure_maps_session_created` - HTTP session configuration

### Authentication Events
- `azure_maps_auth_skip` - When managed identity auth is skipped
- `azure_maps_token_cache_hit` - When cached token is used
- `azure_maps_credential_init` - Credential initialization details
- `azure_maps_token_acquired` - Successful token acquisition
- `azure_maps_token_failed` - Token acquisition failures
- `azure_maps_auth_headers` - Authentication header creation

### Request/Response Events
- `azure_maps_request_start` - Detailed request initiation
- `azure_maps_auth_error` - Authentication failures (401)
- `azure_maps_permission_error` - Permission failures (403)
- `azure_maps_rate_limit` - Rate limiting (429)
- `azure_maps_http_error` - Other HTTP errors
- `azure_maps_connection_error` - Network connection issues
- `azure_maps_timeout_error` - Request timeouts
- `azure_maps_success` - Successful API calls

### Connection Test Events
- `azure_maps_connection_test` - Comprehensive connection test results
- `azure_maps_connection_test_failed` - Connection test failures

## Console Output Enhancements

### Detailed Authentication Logging
```
🔑 Both Managed Identity and Subscription Key available - will prefer Managed Identity
🔐 Using Managed Identity authentication
🕒 Token expires in 59 minutes
```

### Request/Response Details
```
🌐 Making request to: https://atlas.microsoft.com/search/nearby/json
📋 Request parameters: {'api-version': '1.0', 'lat': 47.6062, ...}
📡 HTTP 200 response received in 0.234s
📊 Response size: 1543 bytes
✅ Found 5 POIs in 23ms (total: 0.234s)
```

### Error Details
```
❌ HTTP 401 Error: {"error": {"code": "401", "message": "Access denied due to invalid subscription key..."}}
❌ Connection failed after 2.456s: Cannot connect to host atlas.microsoft.com:443
❌ Request timeout after 30.000s
```

## Common Issues and Solutions

### 1. Authentication Issues

#### No Credentials Available
```
⚠️ No authentication credentials found! Set AZURE_MAPS_CLIENT_ID or AZURE_MAPS_SUBSCRIPTION_KEY
```

**Solution**: Set one of these environment variables:
- `AZURE_MAPS_CLIENT_ID` for Managed Identity authentication
- `AZURE_MAPS_SUBSCRIPTION_KEY` for subscription key authentication

#### Authentication Failed (401)
```
❌ Authentication failed - check credentials
Error details: {"error": {"code": "401", "message": "Access denied due to invalid subscription key..."}}
```

**Solutions**:
- Verify your subscription key is correct and active
- For Managed Identity: ensure the identity has proper permissions
- Check if the key has expired or been revoked

#### Access Forbidden (403)
```
❌ Access forbidden - check permissions
```

**Solutions**:
- Verify your Azure Maps account has the required service tier
- Check that your subscription key has access to the Search API
- For Managed Identity: verify role assignments

### 2. Network Issues

#### Connection Timeout
```
❌ Request timeout after 30.000s
```

**Solutions**:
- Check your internet connection
- Verify firewall settings aren't blocking HTTPS traffic to atlas.microsoft.com
- Try increasing timeout values if on a slow connection

#### Connection Error
```
❌ Connection failed after 2.456s: Cannot connect to host atlas.microsoft.com:443
```

**Solutions**:
- Check DNS resolution for atlas.microsoft.com
- Verify proxy settings if behind a corporate proxy
- Check if port 443 (HTTPS) is accessible

### 3. Rate Limiting

#### Too Many Requests (429)
```
⚠️ Rate limit exceeded - retry after 60s
```

**Solutions**:
- Implement exponential backoff in your application
- Upgrade to a higher service tier for more requests per second
- Cache search results to reduce API calls

### 4. Service Issues

#### Invalid Parameters
```
❌ HTTP 400 Error: {"error": {"code": "400", "message": "Invalid latitude value..."}}
```

**Solutions**:
- Verify latitude is between -90 and 90
- Verify longitude is between -180 and 180
- Check radius is between 1 and 50000 meters
- Ensure limit is between 1 and 100

## Environment Variable Configuration

### For Development (Local)
Create a `.env` file:
```
AZURE_MAPS_SUBSCRIPTION_KEY=your_subscription_key_here
# OR
AZURE_MAPS_CLIENT_ID=your_managed_identity_client_id
```

### For Production (Azure-hosted)
Use Azure App Service configuration or Azure Key Vault:
```bash
# App Service
az webapp config appsettings set --resource-group myRG --name myApp --settings AZURE_MAPS_CLIENT_ID=your_client_id

# Key Vault reference
az webapp config appsettings set --resource-group myRG --name myApp --settings AZURE_MAPS_CLIENT_ID="@Microsoft.KeyVault(VaultName=myVault;SecretName=maps-client-id)"
```

## Using the Connection Test Method

The enhanced Azure Maps operations include a comprehensive connection test:

```python
from operations.azure_maps_operations import AzureMapsOperations

async def diagnose_connection():
    async with AzureMapsOperations() as maps_ops:
        diagnostics = await maps_ops.test_connection()
        
        if diagnostics["overall_status"] == "success":
            print("✅ Connection successful")
        else:
            print(f"❌ Connection failed: {diagnostics['error']['message']}")
            
        # Detailed diagnostics available in the returned dict
        print(f"Auth method: {diagnostics['authentication']['preferred_method']}")
        print(f"Total duration: {diagnostics['total_duration_seconds']:.3f}s")
```

## Monitoring in Production

### Key Metrics to Track
1. **Success Rate**: `azure_maps_success` vs `azure_maps_*_error` events
2. **Response Times**: Track `total_duration_ms` in success events
3. **Authentication Issues**: Monitor `azure_maps_auth_error` events
4. **Rate Limiting**: Track `azure_maps_rate_limit` events

### Azure Application Insights Queries
```kusto
// Success rate over time
customEvents
| where name in ("azure_maps_success", "azure_maps_client_error", "azure_maps_unexpected_error")
| summarize SuccessCount = countif(name == "azure_maps_success"),
           ErrorCount = countif(name != "azure_maps_success"),
           SuccessRate = 100.0 * countif(name == "azure_maps_success") / count()
    by bin(timestamp, 5m)

// Average response times
customEvents
| where name == "azure_maps_success"
| extend Duration = toreal(customDimensions["total_duration_ms"])
| summarize AvgDuration = avg(Duration), P95Duration = percentile(Duration, 95)
    by bin(timestamp, 5m)

// Authentication errors
customEvents
| where name in ("azure_maps_auth_error", "azure_maps_permission_error")
| summarize count() by name, tostring(customDimensions["error_details"])
```

## Getting Help

If you're still experiencing issues after trying these solutions:

1. Run the diagnostics test and collect the full output
2. Check Azure Service Health for any service outages
3. Verify your Azure Maps account status and billing
4. Review the telemetry events for patterns
5. Contact Azure Support with the diagnostics information

The enhanced logging and telemetry provide comprehensive information to help diagnose any connection issues quickly and effectively.
