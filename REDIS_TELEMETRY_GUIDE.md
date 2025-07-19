# Redis Cache Telemetry & Logging Summary

## 🔍 What's Now Tracked

### 1. **Redis Connection Operations**
- **Telemetry**: `@trace_async_method("redis_connect")`
- **Operation Name**: `"redis_connect"`
- **Logs**: Connection timing, success/failure, error details

### 2. **Cache Retrieval Operations** 
- **Telemetry**: `@trace_async_method("cache_get")`
- **Operation Name**: `"cache_get"`
- **Logs**: 
  - Cache HIT: Key, data size, retrieval time
  - Cache MISS: Key, search time
  - Errors: Timing, error details

### 3. **Cache Storage Operations**
- **Telemetry**: `@trace_async_method("cache_set")`
- **Operation Name**: `"cache_set"`
- **Logs**: Key, data size, TTL, storage time, cache type

### 4. **Full Cache Wrapper Operations**
- **Telemetry**: `@trace_async_method("cache_wrapper")`
- **Operation Name**: `"cache_wrapper"`
- **Logs**: 
  - API call timing vs cache timing
  - Total operation duration
  - Method name and cache type

### 5. **Cache Connection Cleanup**
- **Telemetry**: `@trace_async_method("cache_close")`
- **Operation Name**: `"cache_close"`
- **Logs**: Connection close timing and status

## 📊 Application Insights Queries

### Find All Cache Operations
```kusto
traces
| where operation_Name contains "cache"
| order by timestamp desc
```

### Cache Performance Analysis
```kusto
traces
| where operation_Name in ("cache_get", "cache_set", "cache_wrapper")
| where cloud_RoleName == "ai-calendar-assistant"
| summarize 
    avg_duration = avg(duration),
    operation_count = count()
    by operation_Name, bin(timestamp, 1h)
```

### Cache Hit/Miss Ratio
```kusto
traces
| where message contains "Cache HIT" or message contains "Cache MISS"
| summarize 
    hits = countif(message contains "Cache HIT"),
    misses = countif(message contains "Cache MISS")
| extend hit_ratio = hits * 100.0 / (hits + misses)
```

### Redis Connection Issues
```kusto
traces
| where operation_Name == "redis_connect"
| where severityLevel > 2  // Warnings and errors
| order by timestamp desc
```

## 🎯 What You'll See in Logs

### Cache Hit Example:
```
🎯 Cache HIT for key: graph:get_all_users:a1b2c3... (size: 15420 bytes, time: 0.003s)
📋 Cache hit - get_all_users retrieved in 0.003s
🎯 Cache hit for get_all_users - returned in 0.004s
```

### Cache Miss Example:
```
❌ Cache MISS for key: graph:get_all_users:a1b2c3... (time: 0.002s)
🔍 Cache miss - get_all_users not found (checked in 0.002s)
🔄 Cache miss for get_all_users - calling Graph API
💾 Cache SET for key: graph:get_all_users:a1b2c3... (size: 15420 bytes, TTL: 600s, time: 0.008s)
🗂️  Cached user_info data (15420 bytes) with 600s TTL in 0.008s
✅ get_all_users completed: API=1.245s, Total=1.255s (cached for 600s)
```

### Redis Connection:
```
🔄 Establishing Redis connection...
✅ Redis cache connected successfully in 0.156s
```

## 🚀 Testing Your Setup

Run the telemetry test:
```bash
python test_cache_telemetry.py
```

This will generate sample telemetry data for all cache operations so you can see exactly what's being tracked in Application Insights.
