import os
import json
from datetime import datetime
from typing import Dict, Optional, Any
import asyncio

# CRITICAL: Check telemetry disable flag BEFORE any other imports
TELEMETRY_EXPLICITLY_DISABLED = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', '').lower() in ('true', '1', 'yes')

if TELEMETRY_EXPLICITLY_DISABLED:
    print("🚫 Telemetry explicitly disabled via environment variable")

# Redis Cache Support - Using redis package with asyncio for Python 3.13 compatibility
REDIS_AVAILABLE = False
redis_client_class = None

try:
    # Use redis package instead of aioredis for Python 3.13 compatibility
    import redis.asyncio as redis_async
    redis_client_class = redis_async.Redis
    REDIS_AVAILABLE = True
    print("✅ Redis support enabled (redis.asyncio)")
except ImportError as e:
    try:
        # Fallback: try aioredis if redis.asyncio not available
        import aioredis
        redis_client_class = aioredis
        REDIS_AVAILABLE = True
        print("✅ Redis support enabled (aioredis fallback)")
    except Exception as aioredis_error:
        print(f"⚠️  Redis not available - caching disabled")
        print(f"     redis.asyncio error: {e}")
        print(f"     aioredis error: {aioredis_error}")
        REDIS_AVAILABLE = False
        redis_client_class = None
except Exception as e:
    print(f"⚠️  Redis import error - caching disabled: {e}")
    print(f"     Error type: {type(e).__name__}")
    REDIS_AVAILABLE = False
    redis_client_class = None

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without loading .env file
    pass

# Production-grade telemetry import with timeout and graceful fallback
import threading
import time
import concurrent.futures

TELEMETRY_AVAILABLE = False
TELEMETRY_IMPORT_TIMEOUT = 5  # Reduced timeout for faster feedback

def _safe_import_telemetry():
    """
    Safely import telemetry components with timeout to prevent hanging.
    Uses threading to avoid blocking the main application.
    """
    global TELEMETRY_AVAILABLE
    
    try:
        # Check if telemetry is explicitly disabled FIRST
        if TELEMETRY_EXPLICITLY_DISABLED:
            print("🚫 Telemetry disabled - skipping import")
            return False
            
        print(f"🔄 Attempting telemetry import with {TELEMETRY_IMPORT_TIMEOUT}s timeout...")
        
        # Use ThreadPoolExecutor to import with timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_import_telemetry_modules)
            try:
                # Wait for import with timeout
                return future.result(timeout=TELEMETRY_IMPORT_TIMEOUT)
            except concurrent.futures.TimeoutError:
                print(f"⏰ Telemetry import timed out after {TELEMETRY_IMPORT_TIMEOUT} seconds")
                print("🔄 Continuing with fallback implementations")
                return False
            except Exception as e:
                print(f"⚠️  Telemetry import failed: {e}")
                print("🔄 Using fallback implementations")
                return False
                
    except Exception as e:
        print(f"⚠️  Error during telemetry import process: {e}")
        return False

def _import_telemetry_modules():
    """
    Internal function to import telemetry modules.
    This runs in a separate thread to enable timeout handling.
    """
    try:
        print("📦 Importing telemetry modules...")
        
        from telemetry import (
            trace_async_method,
            measure_performance,
            get_tracer,
            get_meter,
            get_logger
        )
        
        from telemetry.console_output import (
            console_info,
            console_debug,
            console_warning,
            console_error,
            console_telemetry_event
        )
        
        # Store in global namespace for main thread access
        globals().update({
            'trace_async_method': trace_async_method,
            'measure_performance': measure_performance,
            'get_tracer': get_tracer,
            'get_meter': get_meter,
            'get_logger': get_logger,
            'console_info': console_info,
            'console_debug': console_debug,
            'console_warning': console_warning,
            'console_error': console_error,
            'console_telemetry_event': console_telemetry_event
        })
        
        print("✅ Telemetry components loaded successfully")
        return True
        
    except ImportError as e:
        print(f"📦 Telemetry modules not available: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Unexpected error importing telemetry: {e}")
        return False

# Perform telemetry import with timeout
TELEMETRY_AVAILABLE = _safe_import_telemetry()

# Fallback implementations if telemetry import fails
if not TELEMETRY_AVAILABLE:
    print("🔄 Using fallback telemetry implementations")
    
    def trace_async_method(name, include_args=False):
        """Fallback decorator that does nothing"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def measure_performance(name):
        """Fallback decorator that does nothing"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_tracer():
        """Fallback tracer"""
        return None
    
    def get_meter():
        """Fallback meter"""
        return None
    
    def get_logger():
        """Fallback logger"""
        return None
    
    def console_info(message, service="RiskOps"):
        print(f"ℹ️  [{service}] {message}")
    
    def console_debug(message, service="RiskOps"):
        print(f"🐛 [{service}] {message}")
    
    def console_warning(message, service="RiskOps"):
        print(f"⚠️  [{service}] {message}")
    
    def console_error(message, service="RiskOps"):
        print(f"❌ [{service}] {message}")
    
    def console_telemetry_event(event_name, properties, service="RiskOps"):
        print(f"📊 [{service}] {event_name}: {properties}")

class RiskOperations:
    def __init__(self):
        """
        Initialize the RiskOperations class.
        This class provides methods to interact with risk management data via mocked API.
        """
        
        # Redis Cache Configuration
        self.cache_enabled = REDIS_AVAILABLE and os.environ.get('REDIS_CACHE_ENABLED', 'true').lower() in ('true', '1', 'yes')
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.cache_ttl = int(os.environ.get('RISK_CACHE_TTL_SECONDS', '300'))  # 5 minutes default
        self.redis_client = None
        
        # Cache configuration for different types of risk data
        self.cache_ttl_config = {
            'client_summary': int(os.environ.get('CACHE_TTL_CLIENT_SUMMARY', '600')),  # 10 minutes
            'risk_metrics': int(os.environ.get('CACHE_TTL_RISK_METRICS', '300')),  # 5 minutes
            'exposure_data': int(os.environ.get('CACHE_TTL_EXPOSURE', '180'))  # 3 minutes
        }
        
        # Mock data store - in a real implementation, this would connect to actual risk management systems
        self._mock_client_data = {
            "5008373037": {
                "client_id": "5008373037",
                "client_name": "LCOLE",
                "parent_client_relationship": {
                    "name": "JAMES FINANCIAL",
                    "id": "7000380807"
                },
                "country": "US",
                "industry_fund_type": "Open ended funds",
                "region": "NORTH AMERICA",
                "exposure_type": "Global Rates Up",
                "exposure_amounts": [38633400, 2147195, 172363],
                "adjustments_changes": -1847.97,
                "large_commitment_amount": 500000000,
                "additional_credit_risk_metrics": [4385955.42, 142181.36, 1140581.76],
                "description": "This client, LCOLE, operates under the parent JAMES FINANCIAL and is part of the open-ended funds sector in North America. The profile reflects significant financial exposures, including a large commitment amount and metrics relevant for credit risk assessment.",
                "last_updated": datetime.now().isoformat(),
                "risk_rating": "Medium-High",
                "compliance_status": "Active"
            },
            "8009547821": {
                "client_id": "8009547821",
                "client_name": "MERIDIAN CAPITAL INVESTMENTS",
                "parent_client_relationship": {
                    "name": "MERIDIAN HOLDINGS GROUP",
                    "id": "8000123456"
                },
                "country": "GB",
                "industry_fund_type": "Investment Banking",
                "region": "EUROPE",
                "exposure_type": "Fixed Income Derivatives",
                "exposure_amounts": [125750000, 67890123, 8947562],
                "adjustments_changes": 15432.88,
                "large_commitment_amount": 1250000000,
                "additional_credit_risk_metrics": [18750423.67, 892341.55, 3456789.12],
                "description": "MERIDIAN CAPITAL INVESTMENTS is a leading European investment bank specializing in fixed income derivatives and structured products. Operating under MERIDIAN HOLDINGS GROUP, they maintain substantial exposure to European sovereign debt markets and provide prime brokerage services to institutional clients across the EU.",
                "last_updated": datetime.now().isoformat(),
                "risk_rating": "High",
                "compliance_status": "Active"
            },
            "6007892341": {
                "client_id": "6007892341",
                "client_name": "QUANTUM HEDGE STRATEGIES",
                "parent_client_relationship": {
                    "name": "QUANTUM FINANCIAL GROUP",
                    "id": "6000567890"
                },
                "country": "US",
                "industry_fund_type": "Hedge Fund - Quantitative",
                "region": "NORTH AMERICA",
                "exposure_type": "Equity Long/Short",
                "exposure_amounts": [89456700, 23847291, 5672834],
                "adjustments_changes": -7234.56,
                "large_commitment_amount": 750000000,
                "additional_credit_risk_metrics": [12847592.33, 567823.91, 2890456.78],
                "description": "QUANTUM HEDGE STRATEGIES is a sophisticated quantitative hedge fund under QUANTUM FINANCIAL GROUP, employing algorithmic trading strategies across global equity markets. The fund specializes in market-neutral strategies with significant exposure to technology and financial sector equities, utilizing advanced machine learning models for alpha generation.",
                "last_updated": datetime.now().isoformat(),
                "risk_rating": "Medium",
                "compliance_status": "Active"
            }
        }
        
        console_info(f"Risk Operations initialized (telemetry: {'enabled' if TELEMETRY_AVAILABLE else 'disabled'}, cache: {'enabled' if self.cache_enabled else 'disabled'})", "RiskOps")
        
        # Log Redis status to telemetry
        console_telemetry_event("redis_status_initialized", {
            "redis_available": REDIS_AVAILABLE,
            "cache_enabled": self.cache_enabled,
            "redis_url": self.redis_url if self.cache_enabled else None,
            "cache_ttl_default": self.cache_ttl
        }, "RiskOps")

    async def _get_redis_client(self):
        """
        Get or create Redis client with proper error handling.
        """
        if not self.cache_enabled or not redis_client_class:
            return None
            
        if self.redis_client is None:
            try:
                if hasattr(redis_client_class, 'from_url'):
                    # For redis.asyncio.Redis
                    self.redis_client = redis_client_class.from_url(self.redis_url, decode_responses=True)
                else:
                    # For aioredis fallback
                    self.redis_client = await redis_client_class.from_url(self.redis_url)
                
                # Test connection
                await self.redis_client.ping()
                console_info("Redis connection established successfully", "RiskOps")
                
            except Exception as e:
                console_warning(f"Redis connection failed: {e}", "RiskOps")
                self.cache_enabled = False
                self.redis_client = None
                
        return self.redis_client

    async def _get_from_cache(self, key: str) -> Optional[str]:
        """
        Get data from Redis cache.
        """
        if not self.cache_enabled:
            return None
            
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                return await redis_client.get(key)
        except Exception as e:
            console_warning(f"Cache get error for key {key}: {e}", "RiskOps")
            
        return None

    async def _set_cache(self, key: str, value: str, ttl: int = None) -> None:
        """
        Set data in Redis cache.
        """
        if not self.cache_enabled:
            return
            
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                ttl = ttl or self.cache_ttl
                await redis_client.setex(key, ttl, value)
        except Exception as e:
            console_warning(f"Cache set error for key {key}: {e}", "RiskOps")

    def _generate_cache_key(self, prefix: str, *args) -> str:
        """
        Generate a consistent cache key.
        """
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

    @trace_async_method("get_client_summary_by_id", include_args=True)
    @measure_performance("risk_client_summary_lookup")
    async def get_client_summary_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get client summary by client ID.
        
        Args:
            client_id (str): The client ID to lookup
            
        Returns:
            Optional[Dict[str, Any]]: Client summary data or None if not found
        """
        try:
            console_info(f"Looking up client summary for ID: {client_id}", "RiskOps")
            
            # Check cache first
            cache_key = self._generate_cache_key("client_summary", client_id)
            cached_result = await self._get_from_cache(cache_key)
            
            if cached_result:
                console_debug(f"Cache hit for client summary: {client_id}", "RiskOps")
                console_telemetry_event("cache_hit", {
                    "operation": "get_client_summary_by_id",
                    "client_id": client_id
                }, "RiskOps")
                return json.loads(cached_result)
            
            # Simulate API call delay (remove in real implementation)
            await asyncio.sleep(0.1)
            
            # Mock API lookup
            if client_id in self._mock_client_data:
                client_data = self._mock_client_data[client_id].copy()
                
                console_info(f"Client summary found for {client_id}: {client_data['client_name']}", "RiskOps")
                
                # Cache the result
                await self._set_cache(
                    cache_key, 
                    json.dumps(client_data), 
                    self.cache_ttl_config['client_summary']
                )
                
                console_telemetry_event("client_summary_retrieved", {
                    "client_id": client_id,
                    "client_name": client_data['client_name'],
                    "parent_client": client_data['parent_client_relationship']['name'],
                    "country": client_data['country'],
                    "region": client_data['region']
                }, "RiskOps")
                
                return client_data
            else:
                console_warning(f"Client not found for ID: {client_id}", "RiskOps")
                console_telemetry_event("client_not_found", {
                    "client_id": client_id
                }, "RiskOps")
                return None
                
        except Exception as e:
            console_error(f"Error retrieving client summary for {client_id}: {str(e)}", "RiskOps")
            console_telemetry_event("client_summary_error", {
                "client_id": client_id,
                "error": str(e)
            }, "RiskOps")
            return None

    @trace_async_method("get_client_risk_metrics", include_args=True)
    @measure_performance("risk_metrics_lookup")
    async def get_client_risk_metrics(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed risk metrics for a client.
        
        Args:
            client_id (str): The client ID to lookup
            
        Returns:
            Optional[Dict[str, Any]]: Risk metrics data or None if not found
        """
        try:
            console_info(f"Looking up risk metrics for client ID: {client_id}", "RiskOps")
            
            # Check cache first
            cache_key = self._generate_cache_key("risk_metrics", client_id)
            cached_result = await self._get_from_cache(cache_key)
            
            if cached_result:
                console_debug(f"Cache hit for risk metrics: {client_id}", "RiskOps")
                return json.loads(cached_result)
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Mock API lookup
            if client_id in self._mock_client_data:
                client_data = self._mock_client_data[client_id]
                
                risk_metrics = {
                    "client_id": client_id,
                    "exposure_amounts": client_data['exposure_amounts'],
                    "adjustments_changes": client_data['adjustments_changes'],
                    "large_commitment_amount": client_data['large_commitment_amount'],
                    "additional_credit_risk_metrics": client_data['additional_credit_risk_metrics'],
                    "exposure_type": client_data['exposure_type'],
                    "risk_rating": client_data.get('risk_rating', 'Not Rated'),
                    "last_updated": client_data['last_updated']
                }
                
                console_info(f"Risk metrics found for {client_id}", "RiskOps")
                
                # Cache the result
                await self._set_cache(
                    cache_key, 
                    json.dumps(risk_metrics), 
                    self.cache_ttl_config['risk_metrics']
                )
                
                return risk_metrics
            else:
                console_warning(f"Risk metrics not found for ID: {client_id}", "RiskOps")
                return None
                
        except Exception as e:
            console_error(f"Error retrieving risk metrics for {client_id}: {str(e)}", "RiskOps")
            return None

    @trace_async_method("add_mock_client", include_args=True)
    async def add_mock_client(self, client_data: Dict[str, Any]) -> bool:
        """
        Add a new mock client to the data store (for testing purposes).
        
        Args:
            client_data (Dict[str, Any]): Client data to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if 'client_id' not in client_data:
                console_error("Client data missing required 'client_id' field", "RiskOps")
                return False
                
            client_id = client_data['client_id']
            client_data['last_updated'] = datetime.now().isoformat()
            
            self._mock_client_data[client_id] = client_data
            
            console_info(f"Mock client added: {client_id}", "RiskOps")
            console_telemetry_event("mock_client_added", {
                "client_id": client_id,
                "client_name": client_data.get('client_name', 'Unknown')
            }, "RiskOps")
            
            return True
            
        except Exception as e:
            console_error(f"Error adding mock client: {str(e)}", "RiskOps")
            return False

    @trace_async_method("list_all_clients")
    async def list_all_clients(self) -> Dict[str, str]:
        """
        List all available clients in the mock data store.
        
        Returns:
            Dict[str, str]: Dictionary mapping client IDs to client names
        """
        try:
            console_info("Listing all available clients", "RiskOps")
            
            clients = {
                client_id: data['client_name'] 
                for client_id, data in self._mock_client_data.items()
            }
            
            console_info(f"Found {len(clients)} clients", "RiskOps")
            return clients
            
        except Exception as e:
            console_error(f"Error listing clients: {str(e)}", "RiskOps")
            return {}

    async def close(self):
        """
        Clean up resources.
        """
        if self.redis_client:
            try:
                await self.redis_client.close()
                console_info("Redis connection closed", "RiskOps")
            except Exception as e:
                console_warning(f"Error closing Redis connection: {e}", "RiskOps")
