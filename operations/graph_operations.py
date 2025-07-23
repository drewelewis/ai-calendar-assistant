import os

# CRITICAL: Check telemetry disable flag BEFORE any other imports
TELEMETRY_EXPLICITLY_DISABLED = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', '').lower() in ('true', '1', 'yes')

if TELEMETRY_EXPLICITLY_DISABLED:
    print("🚫 Telemetry explicitly disabled via environment variable")

from datetime import datetime
import traceback
import asyncio
import hashlib
import json
from typing import List, Dict, Optional, Any
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
import msgraph
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.user import User
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.online_meeting import OnlineMeeting
from msgraph.generated.models.chat_info import ChatInfo

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
        print(f"❌ Unexpected error importing telemetry: {e}")
        return False

# Attempt telemetry import with timeout protection ONLY if not disabled
if not TELEMETRY_EXPLICITLY_DISABLED:
    print("🔄 Initializing telemetry components...")
    TELEMETRY_AVAILABLE = _safe_import_telemetry()
else:
    print("⚡ Skipping telemetry initialization (disabled)")
    TELEMETRY_AVAILABLE = False

# Production-grade fallback implementations
if not TELEMETRY_AVAILABLE:
    print("🔄 Using production fallback implementations")
    
    def trace_async_method(name, include_args=False):
        """Production fallback decorator that preserves function behavior."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # In production, could log to standard logging system
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    if os.environ.get('DEBUG_GRAPH_OPERATIONS', '').lower() in ('true', '1'):
                        print(f"TRACE: {name} completed in {duration:.3f}s")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    print(f"TRACE: {name} failed after {duration:.3f}s - {e}")
                    raise
            return wrapper
        return decorator
    
    def measure_performance(name):
        """Production fallback decorator for performance measurement."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    if duration > 5.0:  # Log slow operations
                        print(f"PERF: {name} took {duration:.3f}s (slow operation)")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    print(f"PERF: {name} failed after {duration:.3f}s")
                    raise
            return wrapper
        return decorator
    
    def get_tracer():
        """Production fallback tracer."""
        return None
    
    def get_meter():
        """Production fallback meter."""
        return None
    
    def get_logger():
        """Production fallback logger."""
        import logging
        return logging.getLogger(__name__)
    
    # Production-grade console output with structured logging
    def console_info(message, module=None):
        """Production console info with structured output."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        print(f"{timestamp} INFO {prefix} {message}")
    
    def console_debug(message, module=None):
        """Production console debug (only in debug mode)."""
        if os.environ.get('DEBUG_GRAPH_OPERATIONS', '').lower() in ('true', '1'):
            timestamp = datetime.now().isoformat()
            prefix = f"[{module}]" if module else "[GraphOps]"
            print(f"{timestamp} DEBUG {prefix} {message}")
    
    def console_warning(message, module=None):
        """Production console warning."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        print(f"{timestamp} WARNING {prefix} {message}")
    
    def console_error(message, module=None):
        """Production console error."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        print(f"{timestamp} ERROR {prefix} {message}")
    
    def console_telemetry_event(event_name, properties=None, module=None):
        """Production telemetry event with structured logging."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        props_str = f" | {properties}" if properties else ""
        print(f"{timestamp} TELEMETRY {prefix} {event_name}{props_str}")

class GraphOperations:
    def __init__(self, user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"], calendar_response_fields=["subject", "start", "end", "location", "attendees"]):
        """
        Initialize the GraphOperations class.
        This class provides methods to interact with Microsoft Graph API.
        """
        self.user_response_fields = user_response_fields
        self.calendar_response_fields = calendar_response_fields

        # Replace with your values
        self.tenant_id = os.environ.get("ENTRA_GRAPH_APPLICATION_TENANT_ID")
        # Deferred validation - will check when client is actually needed
        # if self.tenant_id is None:
        #     raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_TENANT_ID' to your Azure tenant ID.")

        self.client_id = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_ID")
        # if self.client_id is None:
        #     raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_ID' to your Azure application client ID.")

        self.client_secret = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_SECRET")
        # if self.client_secret is None:
        #     raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_SECRET' to your Azure application client secret.")

        self.graph_client = None  # Lazy initialization
        
        # Redis Cache Configuration
        self.cache_enabled = REDIS_AVAILABLE and os.environ.get('REDIS_CACHE_ENABLED', 'true').lower() in ('true', '1', 'yes')
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.cache_ttl = int(os.environ.get('GRAPH_CACHE_TTL_SECONDS', '300'))  # 5 minutes default
        self.redis_client = None
        
        # Cache configuration for different types of data
        self.cache_ttl_config = {
            'user_info': int(os.environ.get('CACHE_TTL_USER_INFO', '600')),  # 10 minutes
            'departments': int(os.environ.get('CACHE_TTL_DEPARTMENTS', '3600')),  # 1 hour  
            'conference_rooms': int(os.environ.get('CACHE_TTL_ROOMS', '1800')),  # 30 minutes
            'calendar_events': int(os.environ.get('CACHE_TTL_CALENDAR', '180')),  # 3 minutes
            'mailbox_validation': int(os.environ.get('CACHE_TTL_MAILBOX', '1800')),  # 30 minutes
            'search_results': int(os.environ.get('CACHE_TTL_SEARCH', '300'))  # 5 minutes
        }
        
        console_info(f"Graph Operations initialized (telemetry: {'enabled' if TELEMETRY_AVAILABLE else 'disabled'}, cache: {'enabled' if self.cache_enabled else 'disabled'})", "GraphOps")
        
        # Log Redis status to telemetry
        console_telemetry_event("redis_status_initialized", {
            "redis_available": REDIS_AVAILABLE,
            "cache_enabled": self.cache_enabled,
            "redis_url": self.redis_url if self.cache_enabled else None,
            "cache_ttl_default": self.cache_ttl
        }, "GraphOps")

    @trace_async_method("redis_connect")
    async def _get_redis_client(self):
        """Get or create Redis client with connection pooling, error handling, and telemetry."""
        if not self.cache_enabled:
            return None
            
        if self.redis_client is None:
            start_time = time.time()
            try:
                console_info("🔄 Establishing Redis connection...", "GraphOps")
                console_telemetry_event("redis_connection_attempt", {
                    "redis_url": self.redis_url,
                    "cache_enabled": self.cache_enabled
                }, "GraphOps")
                
                # Use redis_client_class (either redis.asyncio.Redis or aioredis)
                if hasattr(redis_client_class, 'from_url'):
                    # redis.asyncio.Redis or aioredis
                    self.redis_client = redis_client_class.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                else:
                    # Fallback approach
                    self.redis_client = redis_client_class(
                        url=self.redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                
                # Test connection
                await self.redis_client.ping()
                connection_time = time.time() - start_time
                console_info(f"✅ Redis cache connected successfully in {connection_time:.3f}s", "GraphOps")
                console_telemetry_event("redis_connection_success", {
                    "connection_time_ms": round(connection_time * 1000, 2),
                    "redis_url": self.redis_url
                }, "GraphOps")
                
            except Exception as e:
                connection_time = time.time() - start_time
                console_warning(f"🚨 Redis connection failed after {connection_time:.3f}s: {e} - Caching disabled", "GraphOps")
                console_telemetry_event("redis_connection_failed", {
                    "connection_time_ms": round(connection_time * 1000, 2),
                    "error": str(e),
                    "redis_url": self.redis_url
                }, "GraphOps")
                self.cache_enabled = False
                self.redis_client = None
        return self.redis_client

    def _generate_cache_key(self, method_name: str, *args, **kwargs) -> str:
        """Generate a consistent cache key for method calls."""
        # Create a deterministic hash of the method name and parameters
        key_parts = [method_name]
        
        # Special handling for methods that need parameter normalization for consistent caching
        if method_name in ["get_all_users", "get_users_by_department", "search_users"]:
            # These methods have max_results and exclude_inactive_mailboxes parameters
            # Always normalize max_results to 100 for consistent caching
            normalized_args = list(args)
            if len(normalized_args) > 0:
                # For get_all_users: args[0] = max_results
                # For get_users_by_department: args[0] = department, args[1] = max_results  
                # For search_users: args[0] = filter, args[1] = max_results
                if method_name == "get_all_users":
                    normalized_args[0] = 100  # max_results
                elif method_name == "get_users_by_department" and len(normalized_args) > 1:
                    normalized_args[1] = 100  # max_results (department stays as-is)
                elif method_name == "search_users" and len(normalized_args) > 1:
                    normalized_args[1] = 100  # max_results (filter stays as-is)
            
            # Add normalized positional arguments
            for arg in normalized_args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                elif isinstance(arg, datetime):
                    key_parts.append(arg.isoformat())
                else:
                    key_parts.append(str(hash(str(arg))))
                    
        elif method_name in ["get_all_conference_rooms", "get_all_departments"]:
            # These methods only have max_results parameter
            # Always normalize max_results to 100 for consistent caching
            normalized_args = list(args)
            if len(normalized_args) > 0:
                normalized_args[0] = 100  # max_results
            
            # Add normalized positional arguments
            for arg in normalized_args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                elif isinstance(arg, datetime):
                    key_parts.append(arg.isoformat())
                else:
                    key_parts.append(str(hash(str(arg))))
        else:
            # Add positional arguments normally for other methods
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                elif isinstance(arg, datetime):
                    key_parts.append(arg.isoformat())
                else:
                    key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments in sorted order for consistency
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            elif isinstance(v, datetime):
                key_parts.append(f"{k}:{v.isoformat()}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        
        # Create hash to keep key length manageable
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"graph:{method_name}:{key_hash}"

    @trace_async_method("cache_get")
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from Redis cache with error handling and telemetry."""
        if not self.cache_enabled:
            console_debug("Cache disabled - skipping retrieval", "GraphOps")
            return None
            
        start_time = time.time()
        try:
            redis_client = await self._get_redis_client()
            if redis_client is None:
                console_warning("Redis client unavailable - cache retrieval failed", "GraphOps")
                return None
                
            cached_data = await redis_client.get(cache_key)
            retrieval_time = time.time() - start_time
            
            if cached_data:
                data_size = len(cached_data)
                console_debug(f"🎯 Cache HIT for key: {cache_key[:50]}... (size: {data_size} bytes, time: {retrieval_time:.3f}s)", "GraphOps")
                console_info(f"📋 Cache hit - {cache_key.split(':')[1]} retrieved in {retrieval_time:.3f}s", "GraphOps")
                return json.loads(cached_data)
            else:
                console_debug(f"❌ Cache MISS for key: {cache_key[:50]}... (time: {retrieval_time:.3f}s)", "GraphOps")
                console_info(f"🔍 Cache miss - {cache_key.split(':')[1]} not found (checked in {retrieval_time:.3f}s)", "GraphOps")
                return None
        except Exception as e:
            retrieval_time = time.time() - start_time
            console_warning(f"🚨 Cache retrieval error after {retrieval_time:.3f}s: {e}", "GraphOps")
            return None

    @trace_async_method("cache_set")
    async def _set_cache(self, cache_key: str, data: Any, ttl: int) -> None:
        """Store data in Redis cache with TTL, error handling, and telemetry."""
        if not self.cache_enabled:
            console_debug("Cache disabled - skipping storage", "GraphOps")
            return
            
        start_time = time.time()
        try:
            redis_client = await self._get_redis_client()
            if redis_client is None:
                console_warning("Redis client unavailable - cache storage failed", "GraphOps")
                return
                
            # Convert complex objects to JSON-serializable format
            serializable_data = self._make_serializable(data)
            json_data = json.dumps(serializable_data, default=str)
            data_size = len(json_data)
            
            await redis_client.setex(cache_key, ttl, json_data)
            storage_time = time.time() - start_time
            
            # Determine cache type for better logging
            cache_type = cache_key.split(':')[1] if ':' in cache_key else 'unknown'
            
            console_debug(f"💾 Cache SET for key: {cache_key[:50]}... (size: {data_size} bytes, TTL: {ttl}s, time: {storage_time:.3f}s)", "GraphOps")
            console_info(f"🗂️  Cached {cache_type} data ({data_size} bytes) with {ttl}s TTL in {storage_time:.3f}s", "GraphOps")
            
        except Exception as e:
            storage_time = time.time() - start_time
            console_warning(f"🚨 Cache storage error after {storage_time:.3f}s: {e}", "GraphOps")

    def _make_serializable(self, obj: Any) -> Any:
        """Convert Microsoft Graph objects to JSON-serializable format."""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif hasattr(obj, '__dict__'):
            # Handle Microsoft Graph objects
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    result[key] = self._make_serializable(value)
            return result
        else:
            return str(obj)

    @trace_async_method("cache_wrapper")
    async def _cache_wrapper(self, method_name: str, cache_type: str, method_func, *args, **kwargs):
        """Generic cache wrapper for Graph API methods with comprehensive telemetry."""
        # Generate cache key
        cache_key = self._generate_cache_key(method_name, *args, **kwargs)
        
        # Track overall operation timing
        operation_start = time.time()
        
        # Try to get from cache first
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            cache_time = time.time() - operation_start
            console_info(f"🎯 Cache hit for {method_name} - returned in {cache_time:.3f}s", "GraphOps")
            return cached_result
        
        # Cache miss - call the actual method
        console_debug(f"🔄 Cache miss for {method_name} - calling Graph API", "GraphOps")
        api_start_time = time.time()
        
        try:
            result = await method_func(*args, **kwargs)
            api_duration = time.time() - api_start_time
            
            # Cache the result
            ttl = self.cache_ttl_config.get(cache_type, self.cache_ttl)
            await self._set_cache(cache_key, result, ttl)
            
            total_duration = time.time() - operation_start
            console_info(f"✅ {method_name} completed: API={api_duration:.2f}s, Total={total_duration:.2f}s (cached for {ttl}s)", "GraphOps")
            return result
            
        except Exception as e:
            api_duration = time.time() - api_start_time
            total_duration = time.time() - operation_start
            console_error(f"❌ {method_name} failed: API={api_duration:.2f}s, Total={total_duration:.2f}s - {e}", "GraphOps")
            raise

    @trace_async_method("cache_close")
    async def close_cache(self):
        """Close Redis connection when done with telemetry."""
        if self.redis_client:
            start_time = time.time()
            try:
                console_telemetry_event("redis_connection_closing", {
                    "redis_url": self.redis_url
                }, "GraphOps")
                
                await self.redis_client.close()
                close_time = time.time() - start_time
                console_info(f"🔒 Redis connection closed successfully in {close_time:.3f}s", "GraphOps")
                console_telemetry_event("redis_connection_closed", {
                    "close_time_ms": round(close_time * 1000, 2),
                    "redis_url": self.redis_url
                }, "GraphOps")
                
            except Exception as e:
                close_time = time.time() - start_time
                console_warning(f"🚨 Error closing Redis connection after {close_time:.3f}s: {e}", "GraphOps")
                console_telemetry_event("redis_connection_close_failed", {
                    "close_time_ms": round(close_time * 1000, 2),
                    "error": str(e),
                    "redis_url": self.redis_url
                }, "GraphOps")

    def _get_client(self) -> GraphServiceClient:
        """Get or create the Graph client with lazy initialization."""
        if self.graph_client is None:
            try:
                # print("🔄 Initializing Microsoft Graph client...")
                
                # Validate credentials when actually needed
                if self.tenant_id is None:
                    raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_TENANT_ID' to your Azure tenant ID.")
                if self.client_id is None:
                    raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_ID' to your Azure application client ID.")
                if self.client_secret is None:
                    raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_SECRET' to your Azure application client secret.")
                
                credential = ClientSecretCredential(self.tenant_id, self.client_id, self.client_secret)
                # scopes = ["https://graph.microsoft.com/.default"] # Or specific scopes like "Chat.ReadWrite"
                # Add chat.readAll for read access to all chats to scope
                scope = ["https://graph.microsoft.com/.default"]
                self.graph_client = GraphServiceClient(credential, scope)
                # print("✓ Microsoft Graph client initialized successfully!")
            except Exception as e:
                print(f"❌ Failed to initialize Microsoft Graph client: {e}")
                # print("🔧 Please check your ENTRA_GRAPH_APPLICATION_* environment variables")
                raise
        return self.graph_client
    
    # Get Current Date and Time
    def get_current_datetime(self) -> str:
        return datetime.now().isoformat()
    
    async def debug_graph_connection(self) -> dict:
        """
        Debug method to test Graph API connection and basic functionality.
        Use this to troubleshoot when get_all_users returns empty results.
        """
        try:
            print("🔍 Testing Graph API connection...")
            
            # Test 1: Check client initialization
            client = self._get_client()
            print("✅ Graph client initialized successfully")
            
            # Test 2: Make a simple API call to get user count
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            query_params.select = ["id", "displayName", "mail"]
            query_params.top = 5  # Just get 5 users for testing
            
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            print("🌐 Making test Graph API call...")
            response = await client.users.get(request_configuration=request_configuration)
            
            if hasattr(response, 'value') and response.value:
                users = response.value
                print(f"✅ Successfully retrieved {len(users)} users")
                
                for i, user in enumerate(users[:3]):  # Show first 3 users
                    print(f"  👤 User {i+1}: {getattr(user, 'display_name', 'No name')} ({getattr(user, 'mail', 'No mail')})")
                
                return {
                    'success': True,
                    'user_count': len(users),
                    'message': f'Successfully retrieved {len(users)} users'
                }
            else:
                print("❌ Graph API response has no users")
                return {
                    'success': False,
                    'user_count': 0,
                    'message': 'Graph API response has no users'
                }
                
        except Exception as e:
            print(f"❌ Graph API test failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Graph API test failed: {e}'
            }
    
    def get_telemetry_status(self) -> Dict[str, Any]:
        """Get comprehensive telemetry status."""
        return {
            "telemetry_available": TELEMETRY_AVAILABLE,
            "telemetry_disabled": TELEMETRY_EXPLICITLY_DISABLED,
            "mode": "production_fast_load",
            "startup_time": "optimized",
            "hanging_prevention": "enabled"
        }
    
    def _has_valid_mailbox_properties(self, user: User) -> bool:
        """
        Quick client-side check for mailbox indicators.
        This is a preliminary check before making API calls for full validation.
        
        Args:
            user (User): User object to check
            
        Returns:
            bool: True if user appears to have mailbox properties, False otherwise
        """
        # Check if user has mail property (indicates Exchange mailbox assignment)
        if not hasattr(user, 'mail'):
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} has no 'mail' attribute")
            return False
            
        if not user.mail:
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} has empty mail property")
            return False
            
        # Additional validation - ensure it's a valid email format
        if '@' not in user.mail:
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} has invalid mail format: {user.mail}")
            return False
        
        # Additional checks for conference rooms and service accounts that might have slipped through
        display_name = getattr(user, 'display_name', '').lower()
        mail_lower = user.mail.lower()
        
        # Check for conference room indicators
        if ('conf_' in mail_lower or 
            'room_' in mail_lower or 
            'conference room' in display_name or
            mail_lower.startswith('conf') or
            mail_lower.startswith('room')):
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} appears to be a conference room")
            return False
            
        # Check for service account indicators  
        if ('service' in mail_lower or 
            'service account' in display_name or
            'system account' in display_name or
            'microsoft service' in display_name):
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} appears to be a service account")
            return False
            
        return True

    # Helper method to validate if a user has a valid mailbox for calendar operations
    @trace_async_method("validate_user_mailbox")
    async def validate_user_mailbox(self, user_id: str) -> dict:
        """
        Validate if a user has a valid mailbox for calendar operations.
        
        Args:
            user_id (str): The ID of the user to validate
            
        Returns:
            dict: Validation result with 'valid', 'message', and 'user_info' keys
        """
        return await self._cache_wrapper(
            "validate_user_mailbox", 
            "mailbox_validation", 
            self._validate_user_mailbox_impl, 
            user_id
        )
    
    async def _validate_user_mailbox_impl(self, user_id: str) -> dict:
        """Internal implementation of validate_user_mailbox."""
    async def _validate_user_mailbox_impl(self, user_id: str) -> dict:
        """Internal implementation of validate_user_mailbox."""
        try:
            # First check if user exists and get their properties
            user = await self.get_user_by_user_id(user_id)
            
            if not user:
                return {
                    'valid': False,
                    'message': f'User {user_id} not found in the directory',
                    'user_info': None
                }
            # Check for valid Exchange Online mailbox using Microsoft Graph API
            # A "valid mailbox" means the user has an Exchange Online mailbox provisioned
            # We'll test mailbox access using the recommended Graph API endpoints
            
            # Test for valid Exchange Online mailbox using Microsoft Graph API
            # Try multiple endpoints to determine if user has a valid mailbox
            try:
                # Method 1: Try to access mailbox settings (recommended approach)
                # If user doesn't have a mailbox, this will return ErrorMailboxNotEnabled
                mailbox_settings = await self._get_client().users.by_user_id(user_id).mailbox_settings.get()
                
                if mailbox_settings:
                    return {
                        'valid': True,
                        'message': f'User {user.display_name} ({user_id}) has a valid Exchange Online mailbox',
                        'user_info': user
                    }
                    
            except Exception as mailbox_error:
                error_message = str(mailbox_error)
                
                # Check for specific mailbox-related errors
                if "MailboxNotEnabledForRESTAPI" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {user.display_name} ({user_id}) mailbox is not enabled for REST API access (likely on-premise or inactive)',
                        'user_info': user
                    }
                elif "ErrorMailboxNotEnabled" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {user.display_name} ({user_id}) does not have an Exchange Online mailbox provisioned',
                        'user_info': user
                    }
                elif "Forbidden" in error_message or "403" in error_message:
                    return {
                        'valid': False,
                        'message': f'Access denied to mailbox for user {user.display_name} ({user_id}) - insufficient permissions',
                        'user_info': user
                    }
                elif "NotFound" in error_message or "404" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {user.display_name} ({user_id}) or mailbox not found',
                        'user_info': user
                    }
                else:
                    # Try fallback method: check messages endpoint
                    try:
                        # Method 2: Try to access messages (alternative approach)
                        # This is another way to test for valid mailbox
                        messages_response = await self._get_client().users.by_user_id(user_id).messages.get()
                        
                        # If we can access messages (even if empty), mailbox is valid
                        return {
                            'valid': True,
                            'message': f'User {user.display_name} ({user_id}) has a valid Exchange Online mailbox (verified via messages endpoint)',
                            'user_info': user
                        }
                        
                    except Exception as messages_error:
                        messages_error_str = str(messages_error)
                        
                        if "MailboxNotEnabledForRESTAPI" in messages_error_str or "ErrorMailboxNotEnabled" in messages_error_str:
                            return {
                                'valid': False,
                                'message': f'User {user.display_name} ({user_id}) does not have a valid Exchange Online mailbox',
                                'user_info': user
                            }
                        else:
                            # If both methods fail with non-mailbox errors, assume valid but with access issues
                            return {
                                'valid': False,
                                'message': f'Cannot verify mailbox for user {user.display_name} ({user_id}): {mailbox_error}',
                                'user_info': user
                            }
                    
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error validating user {user_id}: {e}',
                'user_info': None
            }

    # Get a user by user ID
    @trace_async_method("get_user_by_user_id")
    async def get_user_by_user_id(self, user_id: str) -> User | None:
        return await self._cache_wrapper(
            "get_user_by_user_id", 
            "user_info", 
            self._get_user_by_user_id_impl, 
            user_id
        )
    
    async def _get_user_by_user_id_impl(self, user_id: str) -> User | None:
        try:
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                    
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            query_params.filter = f"id eq '{user_id}'"
            # Limit results for testing
            query_params.top = 1
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value') and response.value:
                # response.value is a list, get the first (and should be only) user
                user = response.value[0]
                return user
            else:
                return None
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
            
    # Get a users manager by user ID
    @trace_async_method("get_users_manager_by_user_id")
    async def get_users_manager_by_user_id(self, user_id: str) -> DirectoryObject  | None:
        return await self._cache_wrapper(
            "get_users_manager_by_user_id", 
            "user_info", 
            self._get_users_manager_by_user_id_impl, 
            user_id
        )
    
    async def _get_users_manager_by_user_id_impl(self, user_id: str) -> DirectoryObject  | None:
        try:
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                        
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            query_params.filter = f"id eq '{user_id}'"
            # Limit results for testing
            query_params.top = 1
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value') and response.value:
                # response.value is a list, get the first (and should be only) user
                user = response.value[0]
                
                # Fetch manager details if available
                try:
                    manager = await self._get_client().users.by_user_id(user_id).manager.get()
                except Exception as manager_error:
                    print(f"Could not fetch manager for user {user_id}: {manager_error}")
                    manager = None
                    
                return manager
            else:
                return None
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Get direct reports for a user by user ID
    @trace_async_method("get_direct_reports_by_user_id")
    async def get_direct_reports_by_user_id(self, user_id: str) -> List[User]:
        """
        Get direct reports for a specific user.
        
        Args:
            user_id (str): The ID of the user to get direct reports for
            
        Returns:
            List[User]: List of User objects representing direct reports, empty list if none found
        """
        try:

            
            # Fetch direct reports details
            direct_reports_response = await self._get_client().users.by_user_id(user_id).direct_reports.get()

            if not direct_reports_response or not hasattr(direct_reports_response, 'value'):
                return []
            
            direct_reports = direct_reports_response.value
            if not direct_reports:
                return []
            
            return direct_reports
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_direct_reports_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
                
    # Get all users in the Microsoft 365 Tenant Entra Directory
    @trace_async_method("get_all_users")
    async def get_all_users(self, max_results=100, exclude_inactive_mailboxes: bool = True) -> List[User]:
        """
        Get all users from the Microsoft 365 tenant directory.
        
        Args:
            max_results (int): Maximum number of results to return (default: 100)
            exclude_inactive_mailboxes (bool): If True, filters out users without active mailboxes
            
        Returns:
            List[User]: List of User objects, optionally filtered to exclude users without mailboxes
        """
        return await self._cache_wrapper(
            "get_all_users", 
            "user_info", 
            self._get_all_users_impl, 
            max_results, 
            exclude_inactive_mailboxes
        )
    
    async def _get_all_users_impl(self, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        try:
            # Always use 100 as max_results for consistency - this ensures LLM behavior is predictable
            actual_max_results = 100
            print(f"🚀 Starting get_all_users with max_results={actual_max_results} (requested: {max_results}), exclude_inactive_mailboxes={exclude_inactive_mailboxes}")
            
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            print(f"🔧 Selected fields: {self.user_response_fields}")
            
            # No API-level filtering - rely on validate_user_mailbox for verification
            
            # Use normalized max_results for consistent behavior
            query_params.top = actual_max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            print("🌐 Making Graph API call...")
            response = await self._get_client().users.get(request_configuration=request_configuration)
            print(f"✅ Graph API call completed")


            if hasattr(response, 'value'):
                users = response.value
                print(f"🔍 Graph API returned {len(users) if users else 0} users")
                
                if exclude_inactive_mailboxes and users:
                    # Client-side filtering using mailbox property validation only
                    original_count = len(users)
                    
                    # Filter out conference rooms (safely handle None mail)
                    # Check both mail starting with 'conf' and display names containing 'Conference Room'
                    users_after_conf = [user for user in users if user.mail and 
                                       not user.mail.startswith('conf_') and 
                                       not user.mail.startswith('room_') and
                                       not (user.display_name and 'conference room' in user.display_name.lower())]
                    print(f"🔧 After conference room filter: {len(users_after_conf)} users (removed {original_count - len(users_after_conf)})")
                    
                    # Filter out service accounts (safely handle None mail and check for service account indicators)
                    users_after_service = [user for user in users_after_conf if 
                                         user.mail and  # Must have an email
                                         'service' not in user.mail.lower() and 
                                         'service' not in (user.display_name or '').lower() and
                                         not (user.display_name and 'service account' in user.display_name.lower())]
                    print(f"🔧 After service account filter: {len(users_after_service)} users (removed {len(users_after_conf) - len(users_after_service)})")
                    
                    # Filter users with valid mailbox properties
                    users_final = [user for user in users_after_service if self._has_valid_mailbox_properties(user)]
                    print(f"🔧 After mailbox validation filter: {len(users_final)} users (removed {len(users_after_service) - len(users_final)})")
                    
                    filtered_count = original_count - len(users_final)
                    print(f"📊 Retrieved {original_count} users, filtered out {filtered_count} users, {len(users_final)} users remaining")
                    users = users_final
                else:
                    print(f"📊 Retrieved {len(users)} users (no mailbox filtering applied)")
                
                return users
            else:
                print("❌ Graph API response has no 'value' attribute")
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Get all conference room resources 
    async def get_all_conference_rooms(self, max_results) -> List[User]:
        """
        Get all conference room resources in the Microsoft 365 tenant.
        
        Args:
            max_results (int): Maximum number of results to return
            
        Returns:
            List[User]: List of User objects representing conference rooms
        """
        return await self._cache_wrapper(
            "get_all_conference_rooms", 
            "conference_rooms", 
            self._get_all_conference_rooms_impl, 
            max_results
        )
    
    async def _get_all_conference_rooms_impl(self, max_results) -> List[User]:
        try:
            # Always use 100 as max_results for consistency - this ensures LLM behavior is predictable
            actual_max_results = 100
            print(f"🚀 Starting get_all_conference_rooms with max_results={actual_max_results} (requested: {max_results})")
            
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Filter for conference rooms (typically have a specific naming convention or email domain)
            query_params.filter = "startswith(mail, 'room') or startswith(mail, 'conf')"
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            
            # Use normalized max_results for consistent behavior
            query_params.top = actual_max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if not users:
                    print("No conference rooms found")
                    return []
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_all_conference_rooms: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []

    async def get_conference_room_availability(self, room_id: str, start_time: datetime, end_time: datetime) -> bool:
        try:
            # Call the Graph API to get the availability of the conference room
            response = await self._get_client().users[room_id].calendar.get_schedule(
                start_time=start_time,
                end_time=end_time
            )
            return response.value
        except Exception as e:
            print(f"Error in get_conference_room_availability: {e}")
            return False

    async def get_conference_room_details_by_id(self, room_id: str) -> dict:
        """
        Get detailed information about a specific conference room by its ID.
        
        Args:
            room_id (str): The unique ID of the conference room to retrieve details for
            
        Returns:
            dict: Detailed information about the specified conference room
        """
        try:
            # Fetch the conference room details
            room = await self._get_client().users.by_user_id(room_id).get()
            
            if not room:
                return {}
            
            # Convert to dict for easier handling, checking for attribute existence
            room_details = {
                'id': room.id,
                'displayName': room.display_name,
                'mail': room.mail,
                'userPrincipalName': getattr(room, 'user_principal_name', None),
                'jobTitle': getattr(room, 'job_title', None),
                'department': getattr(room, 'department', None)
            }
            
            # Check for capacity attribute (might not exist for User objects representing rooms)
            if hasattr(room, 'capacity'):
                room_details['capacity'] = room.capacity
            else:
                room_details['capacity'] = None
            
            # Check for location attribute and handle it safely
            if hasattr(room, 'location') and room.location:
                try:
                    room_details['location'] = room.location.__dict__
                except:
                    room_details['location'] = str(room.location) if room.location else None
            else:
                room_details['location'] = None
            
            return room_details
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_conference_room_details_by_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return {}
        
    # Get all departments
    async def get_all_departments(self, max_results) -> List[str]:
        return await self._cache_wrapper(
            "get_all_departments", 
            "departments", 
            self._get_all_departments_impl, 
            max_results
        )
    
    async def _get_all_departments_impl(self, max_results) -> List[str]:
        try:
            # Always use 100 as max_results for consistency - this ensures LLM behavior is predictable
            actual_max_results = 100
            print(f"🚀 Starting get_all_departments with max_results={actual_max_results} (requested: {max_results})")
            
            departments = set()  # Use a set to avoid duplicates

            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                        
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Use normalized max_results for consistent behavior
            query_params.top = actual_max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                for user in users:
                    department = user.department
                    if department:
                        departments.add(department)
                return list(departments)
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
        
    # Get all users by department
    async def get_users_by_department(self, department: str, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        """
        Get users by department with optional inactive mailbox filtering.
        
        Args:
            department (str): Department name to filter by
            max_results (int): Maximum number of results to return
            exclude_inactive_mailboxes (bool): If True, filters out users without active mailboxes
            
        Returns:
            List[User]: List of User objects in the specified department
        """
        return await self._cache_wrapper(
            "get_users_by_department", 
            "user_info", 
            self._get_users_by_department_impl, 
            department, 
            max_results, 
            exclude_inactive_mailboxes
        )
    
    async def _get_users_by_department_impl(self, department: str, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        if not department:
            return []
        try:
            # Always use 100 as max_results for consistency - this ensures LLM behavior is predictable  
            actual_max_results = 100
            print(f"🚀 Starting get_users_by_department with department='{department}', max_results={actual_max_results} (requested: {max_results}), exclude_inactive_mailboxes={exclude_inactive_mailboxes}")
            
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Build filter for department only
            query_params.filter = f"department eq '{department}'"
            print(f"Applied department filter: {query_params.filter}")
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Use normalized max_results for consistent behavior
            query_params.top = actual_max_results
            
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )

            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if exclude_inactive_mailboxes and users:
                    # Client-side filtering using mailbox property validation only
                    original_count = len(users)
                    users = [user for user in users if self._has_valid_mailbox_properties(user)]
                    filtered_count = original_count - len(users)
                    print(f"📊 Retrieved {original_count} users from {department}, filtered out {filtered_count} without mail addresses, {len(users)} users remaining")
                else:
                    print(f"📊 Retrieved {len(users)} users from {department} (no mailbox filtering applied)")
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_users_by_department: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
        
    async def search_users(self, filter, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        """
        Search for users with optional filtering to exclude users without active mailboxes.
        
        Args:
            filter (str): OData filter string for user search
            max_results (int): Maximum number of results to return
            exclude_inactive_mailboxes (bool): If True, filters out users without active mailboxes
            
        Returns:
            List[User]: List of User objects matching the filter criteria
        """
        return await self._cache_wrapper(
            "search_users", 
            "search_results", 
            self._search_users_impl, 
            filter, 
            max_results, 
            exclude_inactive_mailboxes
        )
    
    async def _search_users_impl(self, filter, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        try:
            # Always use 100 as max_results for consistency - this ensures LLM behavior is predictable
            actual_max_results = 100
            print(f"🚀 Starting search_users with filter='{filter}', max_results={actual_max_results} (requested: {max_results}), exclude_inactive_mailboxes={exclude_inactive_mailboxes}")
            
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Use only the provided filter - no additional accountEnabled filtering
            if filter:
                query_params.filter = filter
                print(f"Applied filter: {query_params.filter}")
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Use normalized max_results for consistent behavior
            query_params.top = actual_max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if exclude_inactive_mailboxes and users:
                    # Client-side filtering using mailbox property validation only
                    original_count = len(users)
                    users = [user for user in users if self._has_valid_mailbox_properties(user)]
                    filtered_count = original_count - len(users)
                    print(f"📊 Search returned {original_count} users, filtered out {filtered_count} without mail addresses, {len(users)} users remaining")
                else:
                    print(f"📊 Search returned {len(users)} users (no mailbox filtering applied)")
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.search_users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []

    # Get uses mailbox settings by user ID
    async def get_user_mailbox_settings_by_user_id(self, user_id: str) -> dict:
        """
        Get mailbox settings for a user by user ID.
        
        Args:
            user_id (str): The ID of the user to retrieve mailbox settings for
            
        Returns:
            dict: Mailbox settings as a dictionary, or None if not found
        """
        try:
            mailbox_settings = await self._get_client().users.by_user_id(user_id).mailbox_settings.get()
            if mailbox_settings:
                return mailbox_settings.__dict__  # Convert to dict for easier handling
            else:
                return None
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_user_mailbox_settings_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    async def get_users_city_state_zipcode_by_user_id(self, user_id: str) -> dict:
        """
        Get city, state, and zipcode for a user by user ID.
        
        Args:
            user_id (str): The ID of the user to retrieve location details for

        Returns:
            dict: Dictionary with city, state, and zipcode, or None if not found
        """
        try:
            from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
            
            # Configure the request with proper query parameters
            query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters()
            query_params.select = ["city", "state", "postalCode", "countryOrRegion"]
            
            request_configuration = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            user = await self._get_client().users.by_user_id(user_id).get(request_configuration=request_configuration)
            if not user:
                return None

            # Extract location details from the user object
            location = {
                'city': getattr(user, 'city', None),
                'state': getattr(user, 'state', None),
                'zipcode': getattr(user, 'postal_code', None)
            }

            return location

        except Exception as e:
            print(f"An error occurred with GraphOperations.get_users_city_state_zipcode_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None
            return None
        
    # Get user preferences by user ID
    async def get_user_preferences_by_user_id(self, user_id: str) -> User | None:
        """
        Get user preferences by user ID.
        
        Args:
            user_id (str): The ID of the user to retrieve preferences for
            
        Returns:
            User: User object with preferences, or None if not found
        """
        try:
            # Fetch user details
            user = await self.get_user_by_user_id(user_id)
            if not user:
                return None
            
            # Return the user object with preferences
            return user
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_user_preferences_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None
        
    # Calendar Operations
    # Get calendar events for a user by user ID with optional date range
    async def get_calendar_events_by_user_id(self, user_id: str, start_date: datetime = None, end_date: datetime = None) -> DirectoryObject  | None:
        return await self._cache_wrapper(
            "get_calendar_events_by_user_id", 
            "calendar_events", 
            self._get_calendar_events_by_user_id_impl, 
            user_id, 
            start_date, 
            end_date
        )
    
    async def _get_calendar_events_by_user_id_impl(self, user_id: str, start_date: datetime = None, end_date: datetime = None) -> DirectoryObject  | None:
        try:
            # First validate the user's mailbox
            validation_result = await self.validate_user_mailbox(user_id)
            
            if not validation_result['valid']:
                print(f"❌ Mailbox validation failed: {validation_result['message']}")
                return None
            
            print(f"✅ Mailbox validation passed: {validation_result['message']}")
            user = validation_result['user_info']
            
            # If we have a valid user, proceed with calendar access
            try:
                from msgraph.generated.users.item.calendar.events.events_request_builder import EventsRequestBuilder
                
                # Configure query parameters to order by start date
                events_query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters()
                events_query_params.orderby = ["start/dateTime"]
                events_query_params.select = self.calendar_response_fields
                
                # Add date range filter if provided
                filters = []
                if start_date:
                    filters.append(f"start/dateTime ge '{start_date.isoformat()}'")
                if end_date:
                    filters.append(f"end/dateTime le '{end_date.isoformat()}'")

                if filters:
                    events_query_params.filter = " and ".join(filters)
                
                events_request_config = EventsRequestBuilder.EventsRequestBuilderGetRequestConfiguration(
                    query_parameters=events_query_params
                )

                event_response = await self._get_client().users.by_user_id(user_id).calendar.events.get(request_configuration=events_request_config)
                if hasattr(event_response, 'value') and event_response.value:
                    events = event_response.value
                    print(f"📅 Retrieved {len(events)} calendar events for user {user.display_name}")
                else:
                    events = []
                    print(f"📅 No calendar events found for user {user.display_name}")
            except Exception as events_error:
                # Enhanced error handling for specific Graph API errors
                error_message = str(events_error)
                print(f"Could not fetch events for user {user_id}: ")
                print(f"        APIError")
                print(f"        Code: {getattr(events_error, 'code', 'Unknown')}")
                print(f"        message: {getattr(events_error, 'message', 'None')}")
                print(f"        error: {getattr(events_error, 'error', events_error)}")
                print(f"        ")
                
                # Provide specific guidance for common errors
                if "MailboxNotEnabledForRESTAPI" in error_message:
                    print("🔍 DIAGNOSIS: Mailbox Not Enabled for REST API")
                    print("   This indicates the user's mailbox is either:")
                    print("   • Inactive or disabled")
                    print("   • Soft-deleted (recently removed)")
                    print("   • Hosted on-premise (hybrid setup)")
                    print("   • Not licensed for Exchange Online")
                    print("")
                    print("💡 SOLUTIONS:")
                    print("   1. Verify the user exists and is active in Azure AD")
                    print("   2. Check if user has an Exchange Online license")
                    print("   3. Ensure mailbox is not soft-deleted")
                    print("   4. For hybrid environments, verify cloud mailbox setup")
                    print("   5. Contact admin to enable the mailbox for cloud access")
                elif "Forbidden" in error_message or "403" in error_message:
                    print("🔒 DIAGNOSIS: Permission Denied")
                    print("   The application lacks required permissions to access this user's calendar")
                    print("💡 SOLUTIONS:")
                    print("   1. Ensure app has 'Calendars.Read' or 'Calendars.ReadWrite' permissions")
                    print("   2. Admin consent may be required for application permissions")
                    print("   3. Check if user has restricted their calendar sharing")
                elif "NotFound" in error_message or "404" in error_message:
                    print("👤 DIAGNOSIS: User or Calendar Not Found")
                    print("   The user ID may be invalid or the user doesn't have a calendar")
                    print("💡 SOLUTIONS:")
                    print("   1. Verify the user ID is correct")
                    print("   2. Check if the user exists in the tenant")
                    print("   3. Ensure the user has an Exchange Online mailbox")
                
                events = None

            return events
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_calendar_events_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Create calendar event for a list of attendees and optional attendees
    async def create_calendar_event(self, user_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None) -> Event:
        try:
            
            # Create the event object with optional body content
            event = Event(
                subject=subject,
                start=DateTimeTimeZone(date_time=start, time_zone="UTC"),
                end=DateTimeTimeZone(date_time=end, time_zone="UTC"),
                location=Location(display_name=location) if location else None,
                body=ItemBody(content_type="html", content=body) if body else None,
                attendees=[]
            )
            
            # Add required attendees
            if attendees:
                for attendee in attendees:
                    email_address = EmailAddress(address=attendee)
                    attendee_obj = Attendee(email_address=email_address)
                    attendee_obj.type = "required"
                    event.attendees.append(attendee_obj)
            
            # Add optional attendees
            if optional_attendees:
                for attendee in optional_attendees:
                    email_address = EmailAddress(address=attendee)
                    attendee_obj = Attendee(email_address=email_address)
                    attendee_obj.type = "optional"
                    event.attendees.append(attendee_obj)
            
            # Create the event in the user's calendar
            created_event = await self._get_client().users.by_user_id(user_id).calendar.events.post(event)
            return created_event
            
        except Exception as e:
            print(f"An error occurred while creating calendar event: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    # Create Teams online meeting
    async def create_online_meeting(self, user_id: str, subject: str, start: str, end: str) -> dict:
        """
        Create a Microsoft Teams online meeting.
        
        Args:
            user_id (str): The ID of the user creating the meeting
            subject (str): The subject/title of the meeting
            start (str): Start date and time in ISO 8601 format
            end (str): End date and time in ISO 8601 format
            
        Returns:
            dict: Online meeting information including join URL and conference ID
        """
        try:
            # Create online meeting using the Graph API
            online_meeting = OnlineMeeting(
                subject=subject,
                start_date_time=start,
                end_date_time=end
            )
            
            # Create the online meeting
            created_meeting = await self._get_client().users.by_user_id(user_id).online_meetings.post(online_meeting)
            
            # Extract relevant information
            meeting_info = {
                'id': created_meeting.id,
                'join_url': created_meeting.join_web_url,
                'conference_id': created_meeting.audio_conferencing.conference_id if created_meeting.audio_conferencing else None,
                'dial_in_url': created_meeting.audio_conferencing.dial_in_url if created_meeting.audio_conferencing else None,
                'subject': created_meeting.subject,
                'chat_info': {
                    'thread_id': created_meeting.chat_info.thread_id if created_meeting.chat_info else None,
                    'message_id': created_meeting.chat_info.message_id if created_meeting.chat_info else None
                } if created_meeting.chat_info else None
            }
            
            return meeting_info
            
        except Exception as e:
            print(f"An error occurred while creating online meeting: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    # Enhanced create calendar event with Teams meeting option
    async def create_calendar_event_with_teams(self, user_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None, create_teams_meeting: bool = False) -> Event:
        """
        Create a calendar event with optional Microsoft Teams meeting integration.
        
        Args:
            user_id (str): The ID of the user creating the event
            subject (str): The subject/title of the event
            start (str): Start date and time in ISO 8601 format
            end (str): End date and time in ISO 8601 format
            location (str, optional): Location of the event
            body (str, optional): Body content of the event
            attendees (List[str], optional): Required attendee email addresses
            optional_attendees (List[str], optional): Optional attendee email addresses
            create_teams_meeting (bool): Whether to create a Teams meeting link
            
        Returns:
            Event: The created calendar event with Teams meeting info if requested
        """
        try:
            teams_meeting_info = None
            enhanced_body = body or ""
            enhanced_location = location
            
            # Create Teams meeting if requested
            if create_teams_meeting:
                teams_meeting_info = await self.create_online_meeting(user_id, subject, start, end)
                
                if teams_meeting_info:
                    # Update location to Teams
                    enhanced_location = "Microsoft Teams Meeting"
                    
                    # Enhance body with Teams meeting information
                    teams_info_html = f"""
                    <div style="background-color: #f3f2f1; padding: 15px; margin: 10px 0; border-left: 4px solid #6264a7;">
                        <h3 style="color: #6264a7; margin-top: 0;">📱 Microsoft Teams Meeting</h3>
                        <p><strong>Join the meeting:</strong></p>
                        <p><a href="{teams_meeting_info['join_url']}" style="color: #6264a7; text-decoration: none; font-weight: bold;">Click here to join the meeting</a></p>
                        {f'<p><strong>Conference ID:</strong> {teams_meeting_info["conference_id"]}</p>' if teams_meeting_info.get("conference_id") else ''}
                        {f'<p><a href="{teams_meeting_info["dial_in_url"]}">Find local dial-in numbers</a></p>' if teams_meeting_info.get("dial_in_url") else ''}
                        <p><em>By joining this meeting, you agree to not record or share content without consent.</em></p>
                    </div>
                    """
                    
                    # Prepend Teams info to existing body content
                    enhanced_body = teams_info_html + (f"<br/>{enhanced_body}" if enhanced_body else "")
                else:
                    print("⚠️ Failed to create Teams meeting, proceeding with regular calendar event")
            
            # Create the event object with enhanced content
            event = Event(
                subject=subject,
                start=DateTimeTimeZone(date_time=start, time_zone="UTC"),
                end=DateTimeTimeZone(date_time=end, time_zone="UTC"),
                location=Location(display_name=enhanced_location) if enhanced_location else None,
                body=ItemBody(content_type="html", content=enhanced_body) if enhanced_body else None,
                attendees=[]
            )
            
            # Add Teams meeting info to the event if available
            if teams_meeting_info and create_teams_meeting:
                # The online meeting information is automatically linked when using the same user context
                pass
            
            # Add required attendees
            if attendees:
                for attendee in attendees:
                    email_address = EmailAddress(address=attendee)
                    attendee_obj = Attendee(email_address=email_address)
                    attendee_obj.type = "required"
                    event.attendees.append(attendee_obj)
            
            # Add optional attendees
            if optional_attendees:
                for attendee in optional_attendees:
                    email_address = EmailAddress(address=attendee)
                    attendee_obj = Attendee(email_address=email_address)
                    attendee_obj.type = "optional"
                    event.attendees.append(attendee_obj)
            
            # Create the event in the user's calendar
            created_event = await self._get_client().users.by_user_id(user_id).calendar.events.post(event)
            
            # Store Teams meeting info for reference
            if teams_meeting_info:
                created_event._teams_meeting_info = teams_meeting_info
            
            return created_event
            
        except Exception as e:
            print(f"An error occurred while creating calendar event with Teams meeting: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    # Get and display conference room events
    async def get_conference_room_events(self, conference_rooms: List[User]) -> List[dict]:
        """
        Get and display calendar events for a list of conference rooms.
        
        Args:
            conference_rooms (List[User]): List of conference room User objects
            
        Returns:
            List[dict]: List of conference room objects with their events
        """
        try:
            conference_rooms_with_events = []
            
            for room in conference_rooms:
                print(60 * "=")
                print(f"ID: {room.id}")
                print(f"Display Name: {room.display_name}")
                print(f"User Principal Name: {room.user_principal_name}")
                print(f"Mail: {room.mail}")
                print(f"Job Title: {room.job_title}")
                print(f"Department: {room.department}")
                print(f"Manager: {room.manager}")

                # Get calendar events for this room
                get_calendar_events = await self.get_calendar_events_by_user_id(room.id)
                
                # Process events into a structured format
                events_list = []
                if get_calendar_events:
                    print(f"Found {len(get_calendar_events)} calendar events for room {room.display_name}")
                    for event in get_calendar_events:
                        # Print event details (keeping original console output)
                        print(f"Event Subject: {event.subject}")
                        print(f"Start: {event.start.date_time} {event.start.time_zone}")
                        print(f"End: {event.end.date_time} {event.end.time_zone}")
                        print(f"Location: {event.location.display_name if event.location else 'No location'}")
                        if hasattr(event, 'body') and event.body and event.body.content:
                            print(f"Description: {event.body.content}")
                        print("Attendees:")
                        for attendee in event.attendees:
                            print(f"  - {attendee.email_address.address} ({attendee.type})")
                        
                        # Create structured event data
                        attendees_list = []
                        if event.attendees:
                            for attendee in event.attendees:
                                attendees_list.append({
                                    "email": attendee.email_address.address,
                                    "type": attendee.type,
                                    "name": getattr(attendee.email_address, 'name', '') or attendee.email_address.address
                                })
                        
                        event_data = {
                            "id": getattr(event, 'id', ''),
                            "subject": event.subject or '',
                            "body": event.body.content if (hasattr(event, 'body') and event.body and event.body.content) else '',
                            "start": {
                                "date_time": event.start.date_time,
                                "time_zone": event.start.time_zone
                            },
                            "end": {
                                "date_time": event.end.date_time,
                                "time_zone": event.end.time_zone
                            },
                            "location": event.location.display_name if event.location else 'No location',
                            "attendees": attendees_list
                        }
                        events_list.append(event_data)
                else:
                    print(f"No calendar events found for room {room.display_name}")
                
                # Create structured room data with events
                room_data = {
                    "id": room.id,
                    "display_name": room.display_name,
                    "user_principal_name": room.user_principal_name,
                    "mail": room.mail,
                    "job_title": room.job_title,
                    "department": room.department,
                    "manager": room.manager,
                    "events": events_list,
                    "event_count": len(events_list)
                }
                conference_rooms_with_events.append(room_data)
            
            return conference_rooms_with_events
                            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_conference_room_events: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
      
# # Example usage:

async def main():
    ops = GraphOperations(
        user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
        calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
    )
    # get_all_conference_rooms
    print(60 * "=")
    print("Getting all conference rooms in the Microsoft 365 Tenant Entra Directory...")
    print(60 * "=")
    conference_rooms = await ops.get_all_conference_rooms(100)
    if conference_rooms:
        await ops.get_conference_room_events(conference_rooms)
    else:
        print("No conference rooms found.")




    # print("Get User Mailbox Settings by User ID")
    # mailbox_settings = await ops.get_user_mailbox_settings_by_user_id("12345678-1234-1234-1234-123456789abc")
    # if mailbox_settings:
    #     for key, value in mailbox_settings.items():
    #         print(f"{key}: {value}")
    # print(60 * "=")

    # print("Get User Preferences by User ID")
    # preferences = await ops.get_user_preferences_by_user_id("12345678-1234-1234-1234-123456789abc")
    # if preferences:
    #     for key, value in preferences.__dict__.items():
    #         print(f"{key}: {value}")


    # Example usage for other methods (uncomment as needed):
    
    # print(60 * "=")
    # print("Get User by User ID")
    # print(60 * "=")
    # user_id = "12345678-1234-1234-1234-123456789abc"  # Example user ID
    # user = await ops.get_user_by_user_id(user_id)
    # print(60 * "=")
    # print(f"ID: {user.id}")
    # print(f"Given Name: {user.given_name}")
    # print(f"Surname: {user.surname}")
    # print(f"Display Name: {user.display_name}")
    # print(f"User Principal Name: {user.user_principal_name}")
    # print(f"Mail: {user.mail}")
    # print(f"Job Title: {user.job_title}")
    # print(f"Department: {user.department}")
    # print(f"Manager: {user.manager}")
    
    # print(60 * "=")
    # print("Getting all users in the Microsoft 365 Tenant Entra Directory...")
    # print(60 * "=")
    # users = await ops.get_all_users(100, exclude_inactive_mailboxes=True)  # Filter out users without mailboxes
    # for user in users:
    #     print(60 * "=")
    #     print(f"ID: {user.id}")
    #     print(f"Given Name: {user.given_name}")
    #     print(f"Surname: {user.surname}")
    #     print(f"Display Name: {user.display_name}")
    #     print(f"User Principal Name: {user.user_principal_name}")
    #     print(f"Mail: {user.mail}")
    #     print(f"Job Title: {user.job_title}")
    #     print(f"Department: {user.department}")
    #     print(f"Manager: {user.manager}")
    
    
    # # Get the system administrators manager
    # print(60 * "=")
    # print("Getting the system administrator's manager...")
    # print(60 * "=")
    # user = await ops.get_users_manager_by_user_id("12345678-1234-1234-1234-123456789abc")
    # print(60 * "=")
    # print(f"ID: {user.id}")
    # print(f"Given Name: {user.given_name}")
    # print(f"Surname: {user.surname}")
    # print(f"Display Name: {user.display_name}")
    # print(f"User Principal Name: {user.user_principal_name}")
    # print(f"Mail: {user.mail}")
    # print(f"Job Title: {user.job_title}")
    # print(f"Department: {user.department}")
    # print(f"Manager: {user.manager}")

    # # Get Prita's Direct Reports
    # print(60 * "=")
    # print("Getting manager's direct reports...")
    # print(60 * "=")
    # direct_reports = await ops.get_direct_reports_by_user_id("87654321-4321-4321-4321-987654321def")
    # for user in direct_reports:
    #     print(60 * "=")
    #     print(f"ID: {user.id}")
    #     print(f"Given Name: {user.given_name}")
    #     print(f"Surname: {user.surname}")
    #     print(f"Display Name: {user.display_name}")
    #     print(f"User Principal Name: {user.user_principal_name}")
    #     print(f"Mail: {user.mail}")
    #     print(f"Job Title: {user.job_title}")
    #     print(f"Department: {user.department}")
    #     print(f"Manager: {user.manager}")

    # # Get all departments
    # print(60 * "=")
    # print("Getting all departments in the Microsoft 365 Tenant Entra Directory...")
    # print(60 * "=")
    # departments = await ops.get_all_departments(100)
    # print(f"Found {len(departments)} departments:")
    # for dept in departments:
    #     print(f"  - {dept}")

    # # Get all users by department
    # print(60 * "=")
    # print("Getting all users in the Information Technology department...")
    # print(60 * "=")
    # it_users = await ops.get_users_by_department("Information Technology", 100, exclude_inactive_mailboxes=True)
    # print(f"Found {len(it_users)} users in the Information Technology department:")
    # for user in it_users:
    #    print(f"  - {user.display_name} ({user.user_principal_name})")

    # Get user events by user ID
    # print(60 * "=")
    # print("Getting events for user by user ID...")
    # print(60 * "=")
    # user_id = "12345678-1234-1234-1234-123456789abc"  # Example user ID
    
    # # Example with date range (ISO 8601 format)
    # start_date = "2025-07-01T00:00:00Z"  # Start of July 2025
    # end_date = "2025-07-31T23:59:59Z"    # End of July 2025
    
    # events = await ops.get_calendar_events_by_user_id(user_id, start_date, end_date)
    # if events:
    #     for event in events:
    #         print(60 * "=")
    #         print(f"Subject: {event.subject}")
    #         print(f"Start: {event.start}")
    #         print(f"End: {event.end}")
    #         print(f"Location: {event.location}")
    #         print(f"Attendees: {event.attendees}")
    # else:
    #     print("No events found in the specified date range.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


