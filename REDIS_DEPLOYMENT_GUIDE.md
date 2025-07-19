# Redis Cache Deployment Guide for AI Calendar Assistant

This guide explains how to set up Redis caching for the Microsoft Graph operations in the AI Calendar Assistant.

## 🚀 Quick Start

### Local Development

1. **Install Redis locally:**
   ```bash
   # Windows (using Chocolatey)
   choco install redis-64
   
   # macOS (using Homebrew)
   brew install redis
   
   # Ubuntu/Debian
   sudo apt install redis-server
   ```

2. **Start Redis:**
   ```bash
   redis-server
   ```

3. **Configure environment:**
   ```bash
   # Copy example configuration
   cp .env.redis.example .env.redis
   
   # Edit .env.redis for local development
   REDIS_URL=redis://localhost:6379
   REDIS_CACHE_ENABLED=true
   ```

4. **Install Python dependencies:**
   ```bash
   pip install redis aioredis
   ```

### Azure Production Deployment

## 📋 Azure Redis Cache Setup

### 1. Create Azure Redis Cache

```bash
# Create resource group (if not exists)
az group create --name rg-ai-calendar --location eastus

# Create Azure Redis Cache
az redis create \
  --name redis-ai-calendar-prod \
  --resource-group rg-ai-calendar \
  --location eastus \
  --sku Standard \
  --size C1 \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2
```

### 2. Get Redis Connection Details

```bash
# Get Redis hostname
az redis show --name redis-ai-calendar-prod --resource-group rg-ai-calendar --query hostName -o tsv

# Get Redis access keys
az redis list-keys --name redis-ai-calendar-prod --resource-group rg-ai-calendar
```

### 3. Configure Environment Variables

Set these in your Azure Container App or App Service:

```bash
REDIS_URL=rediss://redis-ai-calendar-prod.redis.cache.windows.net:6380
REDIS_CACHE_ENABLED=true
CACHE_TTL_USER_INFO=600
CACHE_TTL_DEPARTMENTS=3600
CACHE_TTL_CALENDAR=180
```

## 🔒 Security Configuration

### Using Azure Key Vault (Recommended)

1. **Store Redis credentials in Key Vault:**
   ```bash
   # Create Key Vault
   az keyvault create --name kv-ai-calendar --resource-group rg-ai-calendar --location eastus
   
   # Store Redis connection string
   az keyvault secret set --vault-name kv-ai-calendar --name redis-connection-string --value "rediss://username:password@redis-ai-calendar-prod.redis.cache.windows.net:6380"
   ```

2. **Configure Managed Identity:**
   ```bash
   # Enable managed identity for Container App
   az containerapp identity assign --name ai-calendar-app --resource-group rg-ai-calendar
   
   # Grant Key Vault access
   az keyvault set-policy --name kv-ai-calendar --object-id <managed-identity-id> --secret-permissions get
   ```

### Network Security

1. **Configure Redis firewall:**
   ```bash
   # Allow access from Container App subnet
   az redis firewall-rule create \
     --name allow-container-app \
     --resource-group rg-ai-calendar \
     --cache-name redis-ai-calendar-prod \
     --start-ip 10.0.0.0 \
     --end-ip 10.0.255.255
   ```

2. **Use Private Endpoints (Premium tier):**
   ```bash
   # Create private endpoint for Redis
   az network private-endpoint create \
     --name pe-redis-ai-calendar \
     --resource-group rg-ai-calendar \
     --vnet-name vnet-ai-calendar \
     --subnet snet-redis \
     --private-connection-resource-id /subscriptions/{subscription-id}/resourceGroups/rg-ai-calendar/providers/Microsoft.Cache/Redis/redis-ai-calendar-prod \
     --connection-name redis-connection
   ```

## ⚡ Performance Optimization

### Redis Configuration Tuning

```bash
# For high-throughput workloads
az redis patch-schedule create \
  --name redis-ai-calendar-prod \
  --resource-group rg-ai-calendar \
  --schedule-entries day_of_week=Sunday start_hour_utc=2 maintenance_window=PT5H

# Configure memory policy
az redis update \
  --name redis-ai-calendar-prod \
  --resource-group rg-ai-calendar \
  --set redisConfiguration.maxmemory-policy=allkeys-lru
```

### Connection Pool Optimization

Update your application configuration:

```python
# In graph_operations.py
REDIS_CONFIG = {
    'max_connections': 20,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30
}
```

## 📊 Monitoring and Alerting

### 1. Azure Monitor Setup

```bash
# Create action group for alerts
az monitor action-group create \
  --name ag-redis-alerts \
  --resource-group rg-ai-calendar \
  --short-name redis-alert

# Create metric alerts
az monitor metrics alert create \
  --name "Redis High Memory Usage" \
  --resource-group rg-ai-calendar \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-ai-calendar/providers/Microsoft.Cache/Redis/redis-ai-calendar-prod \
  --condition "avg usedmemorypercentage > 80" \
  --action ag-redis-alerts
```

### 2. Application Insights Integration

Add to your application startup:

```python
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

# Configure telemetry
configure_azure_monitor(
    connection_string="InstrumentationKey=your-app-insights-key"
)

# Add Redis performance counters
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log cache performance
logger.info(f"Redis cache hit ratio: {cache_hit_ratio}%")
```

## 🔄 Cache Strategies

### Cache Invalidation Patterns

```python
# Time-based invalidation (default)
cache_ttl = {
    'user_info': 600,      # 10 minutes
    'departments': 3600,   # 1 hour  
    'calendar': 180        # 3 minutes
}

# Event-based invalidation (advanced)
async def invalidate_user_cache(user_id: str):
    """Invalidate user-related cache entries when user data changes"""
    cache_keys = [
        f"graph:get_user_by_user_id:{user_id}",
        f"graph:validate_user_mailbox:{user_id}",
        f"graph:get_users_manager_by_user_id:{user_id}"
    ]
    
    redis_client = await get_redis_client()
    await redis_client.delete(*cache_keys)
```

## 🧪 Testing

### 1. Cache Performance Testing

```python
import asyncio
import time
from operations.graph_operations import GraphOperations

async def test_cache_performance():
    """Test cache hit/miss performance"""
    graph_ops = GraphOperations()
    
    # First call (cache miss)
    start_time = time.time()
    users = await graph_ops.get_all_users(100)
    miss_time = time.time() - start_time
    
    # Second call (cache hit)
    start_time = time.time()
    users_cached = await graph_ops.get_all_users(100)
    hit_time = time.time() - start_time
    
    print(f"Cache MISS: {miss_time:.3f}s")
    print(f"Cache HIT:  {hit_time:.3f}s")
    print(f"Performance improvement: {miss_time/hit_time:.1f}x")

# Run test
asyncio.run(test_cache_performance())
```

### 2. Redis Connection Testing

```bash
# Test Redis connectivity
redis-cli -h redis-ai-calendar-prod.redis.cache.windows.net -p 6380 -a <access-key> --tls ping

# Monitor Redis operations
redis-cli -h redis-ai-calendar-prod.redis.cache.windows.net -p 6380 -a <access-key> --tls monitor
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Timeouts:**
   ```bash
   # Check Redis status
   az redis show --name redis-ai-calendar-prod --resource-group rg-ai-calendar --query provisioningState
   
   # Check firewall rules
   az redis firewall-rule list --name redis-ai-calendar-prod --resource-group rg-ai-calendar
   ```

2. **Memory Issues:**
   ```bash
   # Check Redis memory usage
   az monitor metrics list --resource /subscriptions/{sub}/resourceGroups/rg-ai-calendar/providers/Microsoft.Cache/Redis/redis-ai-calendar-prod --metric usedmemorypercentage
   
   # Increase Redis size if needed
   az redis update --name redis-ai-calendar-prod --resource-group rg-ai-calendar --sku Standard --size C2
   ```

3. **Cache Miss Rate Too High:**
   ```python
   # Check cache key generation
   cache_key = graph_ops._generate_cache_key("get_all_users", 100, True)
   print(f"Cache key: {cache_key}")
   
   # Verify TTL settings
   redis_client = await graph_ops._get_redis_client()
   ttl = await redis_client.ttl(cache_key)
   print(f"TTL remaining: {ttl} seconds")
   ```

## 📈 Performance Benchmarks

Expected performance improvements with Redis caching:

| Operation | Without Cache | With Cache | Improvement |
|-----------|---------------|------------|-------------|
| get_all_users(100) | 2.5s | 0.05s | 50x |
| get_user_by_user_id | 0.8s | 0.02s | 40x |
| search_users | 1.2s | 0.03s | 40x |
| get_all_departments | 3.1s | 0.04s | 77x |
| get_calendar_events | 1.5s | 0.06s | 25x |

## 🔧 Maintenance

### Regular Maintenance Tasks

1. **Monitor cache hit ratios**
2. **Review TTL settings quarterly** 
3. **Update Redis to latest version**
4. **Rotate access keys monthly**
5. **Review cache key patterns**
6. **Monitor memory usage trends**

### Cache Cleanup

```python
# Clean up expired keys (runs automatically)
# Manual cleanup if needed:
async def cleanup_cache():
    redis_client = await get_redis_client()
    
    # Get all graph cache keys
    keys = await redis_client.keys("graph:*")
    
    # Remove expired keys
    pipeline = redis_client.pipeline()
    for key in keys:
        ttl = await redis_client.ttl(key)
        if ttl == -1:  # No expiration set
            pipeline.expire(key, 3600)  # Set 1 hour default
    
    await pipeline.execute()
```

This Redis caching implementation provides significant performance improvements for Microsoft Graph operations while maintaining data freshness and reliability.
