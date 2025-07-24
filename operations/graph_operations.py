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
import logging
from typing import List, Dict, Optional, Any
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
import msgraph
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
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
    def __init__(self, user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"], calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]):
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

    def _format_event_id(self, event_id: str, max_length: int = 40) -> str:
        """
        Helper method to format event IDs for display.
        
        Args:
            event_id (str): The event ID to format
            max_length (int): Maximum length to display (default: 40)
            
        Returns:
            str: Formatted event ID for display
        """
        if not event_id or event_id == 'Unknown':
            return 'Unknown'
        
        if len(event_id) <= max_length:
            return event_id
        
        # Show first part and last part with ellipsis in middle
        half_length = (max_length - 3) // 2
        return f"{event_id[:half_length]}...{event_id[-half_length:]}"

    def _get_user_attribute(self, user, attribute_name: str, default_value='Unknown'):
        """
        Helper method to safely get user attributes, handling both dict and object types.
        
        This handles the case where user objects come from cache as dictionaries
        vs. direct API calls which return User objects.
        """
        if user is None:
            return default_value
            
        if isinstance(user, dict):
            # Handle dictionary format (usually from cache)
            # Try multiple possible key formats
            return (user.get(attribute_name) or 
                   user.get(attribute_name.lower()) or 
                   user.get(attribute_name.replace('_', '')) or
                   default_value)
        else:
            # Handle object format (direct from API)
            return getattr(user, attribute_name, default_value)

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
                
                # Deserialize and reconstruct proper object types
                raw_data = json.loads(cached_data)
                reconstructed_data = self._reconstruct_from_cache(raw_data)
                return reconstructed_data
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
            
            # Add type metadata for better reconstruction
            obj_type = type(obj).__name__
            if obj_type in ['User', 'Event', 'DirectoryObject', 'Location', 'DateTimeTimeZone', 'Attendee', 'EmailAddress']:
                result['@odata.type'] = f'#microsoft.graph.{obj_type.lower()}'
            
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    result[key] = self._make_serializable(value)
            return result
        else:
            return str(obj)

    def _reconstruct_from_cache(self, obj: Any, object_type_hint: str = None) -> Any:
        """
        Reconstruct Microsoft Graph-like objects from cached dictionary data.
        
        Rather than creating full Microsoft Graph objects (which may have complex dependencies),
        this creates simple objects with the same interface as the original objects.
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, list):
            return [self._reconstruct_from_cache(item, object_type_hint) for item in obj]
        elif isinstance(obj, dict):
            # Check if this looks like a Microsoft Graph object and create a simple proxy
            if 'id' in obj and ('displayName' in obj or 'mail' in obj or 'userPrincipalName' in obj):
                # Create a simple User-like object
                return self._create_user_proxy(obj)
            elif 'id' in obj and ('subject' in obj or 'start' in obj or 'end' in obj):
                # Create a simple Event-like object  
                return self._create_event_proxy(obj)
            elif '@odata.type' in obj:
                # Handle objects with type metadata
                odata_type = obj.get('@odata.type', '')
                if 'user' in odata_type.lower():
                    return self._create_user_proxy(obj)
                elif 'event' in odata_type.lower():
                    return self._create_event_proxy(obj)
            
            # If we can't determine the type, create a generic proxy object
            return self._create_generic_proxy(obj)
        else:
            return obj

    def _create_user_proxy(self, data: dict):
        """Create a User-like proxy object from dictionary data."""
        class UserProxy:
            def __init__(self, data):
                for key, value in data.items():
                    if not key.startswith('@'):  # Skip metadata
                        setattr(self, key, value)
                        
            def __repr__(self):
                return f"UserProxy(displayName={getattr(self, 'displayName', 'None')}, mail={getattr(self, 'mail', 'None')})"
        
        return UserProxy(data)

    def _create_event_proxy(self, data: dict):
        """Create an Event-like proxy object from dictionary data."""
        class EventProxy:
            def __init__(self, data):
                for key, value in data.items():
                    if not key.startswith('@'):  # Skip metadata
                        # Handle nested objects like start, end, location, body
                        if isinstance(value, dict):
                            setattr(self, key, self._create_nested_proxy(value))
                        elif isinstance(value, list):
                            setattr(self, key, [self._create_nested_proxy(item) if isinstance(item, dict) else item for item in value])
                        else:
                            setattr(self, key, value)
            
            def _create_nested_proxy(self, nested_data):
                """Create proxy for nested objects like start/end times, location, etc."""
                class NestedProxy:
                    def __init__(self, data):
                        for k, v in data.items():
                            if not k.startswith('@'):
                                setattr(self, k, v)
                return NestedProxy(nested_data)
                            
            def __repr__(self):
                return f"EventProxy(subject={getattr(self, 'subject', 'None')}, id={getattr(self, 'id', 'None')})"
        
        return EventProxy(data)

    def _create_generic_proxy(self, data: dict):
        """Create a generic proxy object from dictionary data."""
        class GenericProxy:
            def __init__(self, data):
                self._data = data
                for key, value in data.items():
                    if not key.startswith('@'):  # Skip metadata
                        setattr(self, key, value)
                        
            def __getitem__(self, key):
                """Support dictionary-like access for backward compatibility"""
                return self._data[key]
                
            def __contains__(self, key):
                """Support 'in' operator"""
                return key in self._data
                
            def get(self, key, default=None):
                """Support dict.get() method"""
                return self._data.get(key, default)
                
            def keys(self):
                """Support dict.keys() method"""
                return self._data.keys()
                
            def values(self):
                """Support dict.values() method"""
                return self._data.values()
                
            def items(self):
                """Support dict.items() method"""
                return self._data.items()
        
        return GenericProxy(data)

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
    
    @trace_async_method("get_system_health_status")
    async def get_system_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status including cache, telemetry, and Graph API connectivity.
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "cache": {
                "enabled": self.cache_enabled,
                "redis_available": REDIS_AVAILABLE,
                "redis_url": self.redis_url if self.cache_enabled else None,
                "cache_ttl_config": self.cache_ttl_config
            },
            "telemetry": {
                "available": TELEMETRY_AVAILABLE,
                "explicitly_disabled": TELEMETRY_EXPLICITLY_DISABLED
            },
            "graph_api": {
                "client_initialized": self.graph_client is not None,
                "credentials_configured": all([
                    self.tenant_id is not None,
                    self.client_id is not None,
                    self.client_secret is not None
                ])
            }
        }
        
        # Test Redis connection if enabled
        if self.cache_enabled:
            try:
                redis_client = await self._get_redis_client()
                if redis_client:
                    await redis_client.ping()
                    health_status["cache"]["status"] = "connected"
                    console_debug("Redis health check: connected", "GraphOps")
                else:
                    health_status["cache"]["status"] = "unavailable"
            except Exception as e:
                health_status["cache"]["status"] = "error"
                health_status["cache"]["error"] = str(e)
                console_warning(f"Redis health check failed: {e}", "GraphOps")
        else:
            health_status["cache"]["status"] = "disabled"
        
        # Test Graph API connection
        try:
            if health_status["graph_api"]["credentials_configured"]:
                # Simple test to validate connectivity
                client = self._get_client()
                # Just test client creation, not an actual API call to avoid rate limits
                health_status["graph_api"]["status"] = "configured"
                console_debug("Graph API health check: configured", "GraphOps")
            else:
                health_status["graph_api"]["status"] = "credentials_missing"
        except Exception as e:
            health_status["graph_api"]["status"] = "error"
            health_status["graph_api"]["error"] = str(e)
            console_warning(f"Graph API health check failed: {e}", "GraphOps")
        
        # Log health status to telemetry
        console_telemetry_event("system_health_check", health_status, "GraphOps")
        
        return health_status
    
    @trace_async_method("invalidate_cache")
    async def invalidate_cache(self, pattern: str = None) -> Dict[str, Any]:
        """
        Invalidate cache entries, optionally by pattern.
        
        Args:
            pattern (str, optional): Redis pattern to match keys for deletion (e.g., "graph:*", "graph:get_user_*")
                                   If None, provides status without deletion
                                   
        Returns:
            Dict[str, Any]: Information about cache invalidation operation
        """
        if not self.cache_enabled:
            return {
                "success": False,
                "message": "Cache not enabled",
                "deleted_keys": 0
            }
        
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return {
                    "success": False,
                    "message": "Redis client not available",
                    "deleted_keys": 0
                }
            
            if pattern:
                # Find keys matching the pattern
                keys = await redis_client.keys(pattern)
                deleted_count = 0
                
                if keys:
                    # For Redis Cluster compatibility, delete keys one by one
                    # This avoids the "Keys in request don't hash to the same slot" error
                    # that occurs when using `delete(*keys)` with multiple keys that hash 
                    # to different slots in a Redis cluster setup
                    for key in keys:
                        try:
                            result = await redis_client.delete(key)
                            deleted_count += result
                        except Exception as key_error:
                            console_warning(f"Failed to delete cache key {key}: {key_error}", "GraphOps")
                            # Continue with other keys even if one fails
                            continue
                    
                    console_info(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}", "GraphOps")
                    console_telemetry_event("cache_invalidation", {
                        "pattern": pattern,
                        "deleted_keys": deleted_count
                    }, "GraphOps")
                else:
                    console_info(f"No cache keys found matching pattern: {pattern}", "GraphOps")
                
                return {
                    "success": True,
                    "message": f"Invalidated {deleted_count} keys matching pattern: {pattern}",
                    "deleted_keys": deleted_count,
                    "pattern": pattern
                }
            else:
                # Just return cache status
                all_keys = await redis_client.keys("graph:*")
                return {
                    "success": True,
                    "message": "Cache status retrieved",
                    "total_keys": len(all_keys),
                    "pattern": "graph:*"
                }
                
        except Exception as e:
            error_message = str(e)
            
            # Provide specific guidance for Redis cluster issues
            if "hash to the same slot" in error_message:
                console_error(f"Redis cluster cache invalidation failed (slot hashing issue): {e}", "GraphOps")
                console_info("This should not happen with the current implementation. Please check Redis cluster configuration.", "GraphOps")
            elif "CROSSSLOT" in error_message:
                console_error(f"Redis cluster cross-slot operation failed: {e}", "GraphOps")
                console_info("Keys are hashing to different slots. Using single-key deletion fallback.", "GraphOps")
            else:
                console_error(f"Cache invalidation failed: {e}", "GraphOps")
            
            console_telemetry_event("cache_invalidation_failed", {
                "pattern": pattern,
                "error": str(e)
            }, "GraphOps")
            return {
                "success": False,
                "message": f"Cache invalidation failed: {e}",
                "deleted_keys": 0,
                "error": str(e)
            }
    
    @trace_async_method("get_cache_statistics")
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics and health information.
        
        Returns:
            Dict[str, Any]: Cache statistics including key counts, memory usage, etc.
        """
        if not self.cache_enabled:
            return {
                "enabled": False,
                "message": "Cache not enabled"
            }
        
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return {
                    "enabled": True,
                    "status": "unavailable",
                    "message": "Redis client not available"
                }
            
            # Get Redis info
            info = await redis_client.info()
            
            # Count keys by type
            all_keys = await redis_client.keys("graph:*")
            key_stats = {}
            
            for key in all_keys:
                key_type = key.split(':')[1] if ':' in key else 'unknown'
                key_stats[key_type] = key_stats.get(key_type, 0) + 1
            
            cache_stats = {
                "enabled": True,
                "status": "connected",
                "redis_version": info.get('redis_version', 'unknown'),
                "total_keys": len(all_keys),
                "key_stats_by_type": key_stats,
                "memory": {
                    "used_memory": info.get('used_memory', 0),
                    "used_memory_human": info.get('used_memory_human', '0B'),
                    "used_memory_peak": info.get('used_memory_peak', 0),
                    "used_memory_peak_human": info.get('used_memory_peak_human', '0B')
                },
                "connections": {
                    "connected_clients": info.get('connected_clients', 0),
                    "blocked_clients": info.get('blocked_clients', 0)
                },
                "cache_ttl_config": self.cache_ttl_config,
                "redis_url": self.redis_url
            }
            
            console_telemetry_event("cache_statistics_retrieved", {
                "total_keys": len(all_keys),
                "key_types": list(key_stats.keys()),
                "memory_used": info.get('used_memory', 0)
            }, "GraphOps")
            
            return cache_stats
            
        except Exception as e:
            console_error(f"Failed to get cache statistics: {e}", "GraphOps")
            return {
                "enabled": True,
                "status": "error",
                "message": f"Failed to get statistics: {e}",
                "error": str(e)
            }
    
    async def _is_likely_conference_room(self, user_id: str) -> bool:
        """
        Check if a user ID is likely a conference room based on common patterns.
        
        Args:
            user_id (str): The user ID to check
            
        Returns:
            bool: True if the user appears to be a conference room
        """
        try:
            # Try to get user info to check email and display name patterns
            user = await self.get_user_by_user_id(user_id)
            if not user:
                return False
            
            # Check email patterns
            user_mail = self._get_user_attribute(user, 'mail', '').lower()
            if ('conf_' in user_mail or 
                'room_' in user_mail or 
                user_mail.startswith('conf') or 
                user_mail.startswith('room')):
                return True
            
            # Check display name patterns
            display_name = getattr(user, 'display_name', '').lower()
            if ('conference room' in display_name or
                'meeting room' in display_name or
                'room ' in display_name):
                return True
                
            return False
            
        except Exception as e:
            # If we can't determine, assume it's not a conference room
            console_debug(f"Could not determine if {user_id} is conference room: {e}", "GraphOps")
            return False
    
    async def _invalidate_calendar_cache(self, user_id: str, event_id: str = None, operation: str = "update", location: str = None) -> None:
        """
        Invalidate calendar-related cache entries for a specific user and optionally event.
        
        This method ensures data consistency by clearing cache entries for:
        - get_user_calendar_events_by_user_id() - calendar event lists for the user
        - get_calendar_event_by_id() - specific event details (when event_id provided)
        - get_conference_room_events() - conference room events (if user is a conference room)
        - get_all_conference_rooms() - conference room list (if user is a conference room)
        - Any other calendar-related cached methods
        
        Args:
            user_id (str): The user ID whose calendar caches should be invalidated
            event_id (str, optional): Specific event ID to invalidate (if provided)
            operation (str): The operation being performed (for logging)
            location (str, optional): Location of the event (to detect conference room involvement)
        """
        if not self.cache_enabled:
            return
        
        try:
            patterns_to_invalidate = []
            
            # Always invalidate calendar list caches for the user
            # These patterns match the actual cached methods
            patterns_to_invalidate.extend([
                f"graph:get_user_calendar_events_by_user_id:*",  # Main calendar events method
                f"graph:get_calendar_events:*",                  # Generic calendar events patterns
                f"graph:*calendar*events*{user_id}*"             # Catch any calendar/events patterns with user_id
            ])
            
            # Check if this might be a conference room based on common patterns
            is_likely_conference_room = await self._is_likely_conference_room(user_id)
            
            # Also check if the location suggests conference room involvement
            location_suggests_room = False
            if location:
                location_lower = location.lower()
                location_suggests_room = ('conference room' in location_lower or
                                        'meeting room' in location_lower or
                                        'room ' in location_lower or
                                        location_lower.startswith('room'))
            
            if is_likely_conference_room or location_suggests_room:
                # Also invalidate conference room related caches
                patterns_to_invalidate.extend([
                    f"graph:get_conference_room_events:*",        # Conference room events
                    f"graph:get_all_conference_rooms:*",          # Conference room lists
                    f"graph:get_conference_room_details_by_id:*", # Conference room details
                    f"graph:*conference*room*",                   # Any conference room patterns
                ])
                
                if is_likely_conference_room:
                    console_debug(f"User {user_id} identified as conference room - invalidating room caches", "GraphOps")
                if location_suggests_room:
                    console_debug(f"Location '{location}' suggests conference room - invalidating room caches", "GraphOps")
            
            # If specific event, also invalidate event-specific caches
            if event_id:
                patterns_to_invalidate.extend([
                    f"graph:get_calendar_event_by_id:*",          # Specific event lookups
                    f"graph:*{event_id}*"                        # Any cache entries containing the event_id
                ])
            
            # Invalidate each pattern
            total_deleted = 0
            for pattern in patterns_to_invalidate:
                result = await self.invalidate_cache(pattern)
                if result.get("success", False):
                    total_deleted += result.get("deleted_keys", 0)
            
            console_debug(f"Calendar cache invalidation after {operation}: {total_deleted} keys deleted for user {user_id}", "GraphOps")
            console_telemetry_event("calendar_cache_invalidation", {
                "user_id": user_id,
                "event_id": event_id,
                "operation": operation,
                "deleted_keys": total_deleted,
                "patterns_count": len(patterns_to_invalidate),
                "conference_room_caches_invalidated": is_likely_conference_room or location_suggests_room,
                "detected_as_conference_room": is_likely_conference_room,
                "location_suggests_room": location_suggests_room
            }, "GraphOps")
            
        except Exception as e:
            console_warning(f"Failed to invalidate calendar cache after {operation}: {e}", "GraphOps")
    
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
            
        if not self._get_user_attribute(user, 'mail'):
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} has empty mail property")
            return False
            
        # Additional validation - ensure it's a valid email format
        user_mail = self._get_user_attribute(user, 'mail', '')
        if '@' not in user_mail:
            print(f"🔍 User {getattr(user, 'display_name', 'Unknown')} has invalid mail format: {user_mail}")
            return False
        
        # Additional checks for conference rooms and service accounts that might have slipped through
        display_name = getattr(user, 'display_name', '').lower()
        mail_lower = user_mail.lower()
        
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
    
    def _categorize_graph_error(self, error: Exception, operation: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Categorize and analyze Graph API errors for better telemetry and debugging.
        
        Args:
            error (Exception): The exception that occurred
            operation (str): The operation being performed when the error occurred
            context (Dict[str, Any], optional): Additional context about the operation
            
        Returns:
            Dict[str, Any]: Categorized error information
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Categorize common Graph API errors
        if "forbidden" in error_str or "403" in error_str:
            category = "permission_denied"
            severity = "high"
            suggested_action = "Check application permissions and user consent"
        elif "unauthorized" in error_str or "401" in error_str:
            category = "authentication_failed"
            severity = "high"
            suggested_action = "Verify credentials and token validity"
        elif "not found" in error_str or "404" in error_str:
            category = "resource_not_found"
            severity = "medium"
            suggested_action = "Verify resource ID and user permissions"
        elif "too many requests" in error_str or "429" in error_str or "throttl" in error_str:
            category = "rate_limited"
            severity = "medium"
            suggested_action = "Implement exponential backoff retry logic"
        elif "mailbox not enabled" in error_str:
            category = "mailbox_not_enabled"
            severity = "medium"
            suggested_action = "Ensure user has Exchange Online mailbox provisioned"
        elif "timeout" in error_str or "timed out" in error_str:
            category = "timeout"
            severity = "medium"
            suggested_action = "Retry operation or check network connectivity"
        elif "network" in error_str or "connection" in error_str:
            category = "network_error"
            severity = "medium"
            suggested_action = "Check network connectivity and DNS resolution"
        elif "service unavailable" in error_str or "503" in error_str:
            category = "service_unavailable"
            severity = "high"
            suggested_action = "Wait and retry - Microsoft Graph service may be temporarily unavailable"
        else:
            category = "unknown_error"
            severity = "high"
            suggested_action = "Review error details and contact support if needed"
        
        error_info = {
            "category": category,
            "severity": severity,
            "error_type": error_type,
            "error_message": str(error),
            "operation": operation,
            "suggested_action": suggested_action,
            "context": context or {}
        }
        
        # Log categorized error to telemetry
        console_telemetry_event("graph_error_categorized", error_info, "GraphOps")
        
        return error_info
    
    def _log_performance_metrics(self, operation: str, duration: float, context: Dict[str, Any] = None):
        """
        Log performance metrics for operations.
        
        Args:
            operation (str): Name of the operation
            duration (float): Duration in seconds
            context (Dict[str, Any], optional): Additional context
        """
        # Define performance thresholds
        thresholds = {
            "fast": 1.0,      # < 1 second
            "normal": 5.0,    # 1-5 seconds
            "slow": 10.0,     # 5-10 seconds
            # > 10 seconds is considered very slow
        }
        
        if duration < thresholds["fast"]:
            performance_category = "fast"
        elif duration < thresholds["normal"]:
            performance_category = "normal"
        elif duration < thresholds["slow"]:
            performance_category = "slow"
        else:
            performance_category = "very_slow"
        
        perf_data = {
            "operation": operation,
            "duration_seconds": round(duration, 3),
            "duration_ms": round(duration * 1000, 1),
            "performance_category": performance_category,
            "context": context or {}
        }
        
        # Log performance metrics
        if performance_category in ["slow", "very_slow"]:
            console_warning(f"Slow operation detected: {operation} took {duration:.2f}s", "GraphOps")
        else:
            console_debug(f"Operation timing: {operation} took {duration:.2f}s ({performance_category})", "GraphOps")
        
        console_telemetry_event("performance_metrics", perf_data, "GraphOps")

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
        try:
            # First check if user exists and get their properties
            user = await self.get_user_by_user_id(user_id)
            
            if not user:
                return {
                    'valid': False,
                    'message': f'User {user_id} not found in the directory',
                    'user_info': None
                }
                
            # Extract user display name from the User object
            display_name = getattr(user, 'displayName', 'Unknown')
            
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
                        'message': f'User {display_name} ({user_id}) has a valid Exchange Online mailbox',
                        'user_info': user
                    }
                    
            except Exception as mailbox_error:
                error_message = str(mailbox_error)
                
                # Check for specific mailbox-related errors
                if "MailboxNotEnabledForRESTAPI" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {display_name} ({user_id}) mailbox is not enabled for REST API access (likely on-premise or inactive)',
                        'user_info': user
                    }
                elif "ErrorMailboxNotEnabled" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {display_name} ({user_id}) does not have an Exchange Online mailbox provisioned',
                        'user_info': user
                    }
                elif "Forbidden" in error_message or "403" in error_message:
                    return {
                        'valid': False,
                        'message': f'Access denied to mailbox for user {display_name} ({user_id}) - insufficient permissions',
                        'user_info': user
                    }
                elif "NotFound" in error_message or "404" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {display_name} ({user_id}) or mailbox not found',
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
                            'message': f'User {display_name} ({user_id}) has a valid Exchange Online mailbox (verified via messages endpoint)',
                            'user_info': user
                        }
                        
                    except Exception as messages_error:
                        messages_error_str = str(messages_error)
                        
                        if "MailboxNotEnabledForRESTAPI" in messages_error_str or "ErrorMailboxNotEnabled" in messages_error_str:
                            return {
                                'valid': False,
                                'message': f'User {display_name} ({user_id}) does not have a valid Exchange Online mailbox',
                                'user_info': user
                            }
                        else:
                            # If both methods fail with non-mailbox errors, assume valid but with access issues
                            return {
                                'valid': False,
                                'message': f'Cannot verify mailbox for user {display_name} ({user_id}): {mailbox_error}',
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
            return None
            
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
            return None
    
    # Get direct reports for a user by user ID
    @trace_async_method("get_users_direct_reports_by_user_id")
    async def get_users_direct_reports_by_user_id(self, user_id: str) -> List[User]:
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
                    users_after_conf = [user for user in users if self._get_user_attribute(user, 'mail') and 
                                       not self._get_user_attribute(user, 'mail', '').startswith('conf_') and 
                                       not self._get_user_attribute(user, 'mail', '').startswith('room_') and
                                       not ('conference room' in self._get_user_attribute(user, 'displayName', '').lower())]
                    print(f"🔧 After conference room filter: {len(users_after_conf)} users (removed {original_count - len(users_after_conf)})")
                    
                    # Filter out service accounts (safely handle None mail and check for service account indicators)
                    users_after_service = [user for user in users_after_conf if 
                                         self._get_user_attribute(user, 'mail') and  # Must have an email
                                         'service' not in self._get_user_attribute(user, 'mail', '').lower() and 
                                         'service' not in self._get_user_attribute(user, 'displayName', '').lower() and
                                         not ('service account' in self._get_user_attribute(user, 'displayName', '').lower())]
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
                'id': self._get_user_attribute(room, 'id'),
                'displayName': self._get_user_attribute(room, 'display_name') or self._get_user_attribute(room, 'displayName'),
                'mail': self._get_user_attribute(room, 'mail'),
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
    async def get_user_calendar_events_by_user_id(self, user_id: str, start_date: datetime = None, end_date: datetime = None) -> List[Event] | None:
        return await self._cache_wrapper(
            "get_user_calendar_events_by_user_id", 
            "calendar_events", 
            self._get_user_calendar_events_by_user_id_impl, 
            user_id, 
            start_date, 
            end_date,
        )
    
    async def _get_user_calendar_events_by_user_id_impl(self, user_id: str, start_date: datetime = None, end_date: datetime = None) -> List[Event] | None:
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
                    # Handle both dict and User object types for display name
                    if isinstance(user, dict):
                        display_name = user.get('displayName') or user.get('display_name', 'Unknown')
                    else:
                        display_name = getattr(user, 'display_name', 'Unknown')
                    
                    # Log event details including IDs for debugging
                    print(f"📅 Retrieved {len(events)} calendar events for user {display_name}")
                    for i, event in enumerate(events[:3]):  # Show first 3 events
                        event_id = getattr(event, 'id', 'Unknown')
                        event_subject = getattr(event, 'subject', 'No Subject')
                        formatted_id = self._format_event_id(event_id)
                        print(f"   📝 Event {i+1}: {event_subject} (ID: {formatted_id})")
                else:
                    events = []
                    # Handle both dict and User object types for display name
                    if isinstance(user, dict):
                        display_name = user.get('displayName') or user.get('display_name', 'Unknown')
                    else:
                        display_name = getattr(user, 'display_name', 'Unknown')
                    print(f"📅 No calendar events found for user {display_name}")
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
            print(f"An error occurred with GraphOperations.get_user_calendar_events_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Create calendar event for a list of attendees and optional attendees
    @trace_async_method("create_calendar_event", include_args=True)
    async def create_calendar_event(self, user_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None) -> Event:
        try:
            console_info(f"Creating calendar event: {subject} for user {user_id}", "GraphOps")
            console_telemetry_event("calendar_event_create_start", {
                "user_id": user_id,
                "subject": subject,
                "has_location": location is not None,
                "has_body": body is not None,
                "attendee_count": len(attendees) if attendees else 0,
                "optional_attendee_count": len(optional_attendees) if optional_attendees else 0
            }, "GraphOps")
            
            # Enhance body with default content if not provided
            enhanced_body = body or ""
            
            # If no body is provided, create a professional default body
            if not enhanced_body:
                from datetime import datetime
                
                # Parse the start time to format it nicely
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_start = start_dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")
                except:
                    formatted_start = start
                
                # Create professional default body with email-friendly HTML
                enhanced_body = f"""
<html>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
    <table cellpadding="0" cellspacing="0" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #0078d4;">
                <h3 style="color: #0078d4; margin: 0 0 15px 0; font-size: 18px;">📅 Meeting Details</h3>
                <p style="margin: 8px 0;"><strong>Subject:</strong> {subject}</p>
                <p style="margin: 8px 0;"><strong>Date &amp; Time:</strong> {formatted_start}</p>
                {f'<p style="margin: 8px 0;"><strong>Location:</strong> {location}</p>' if location else ''}
                <p style="margin: 15px 0 8px 0; font-style: italic; color: #666;">This meeting has been scheduled via the AI Calendar Assistant.</p>
                <p style="margin: 8px 0; font-style: italic; color: #666;">Please confirm your attendance and add any agenda items you'd like to discuss.</p>
            </td>
        </tr>
    </table>
</body>
</html>
                """.strip()
            
            # Create the event object with enhanced body content
            event = Event(
                subject=subject,
                start=DateTimeTimeZone(date_time=start, time_zone="UTC"),
                end=DateTimeTimeZone(date_time=end, time_zone="UTC"),
                location=Location(display_name=location) if location else None,
                body=ItemBody(content_type=BodyType.Html, content=enhanced_body),
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
            
            # Log the created event ID for reference
            event_id = getattr(created_event, 'id', 'Unknown')
            formatted_id = self._format_event_id(event_id)
            console_info(f"Calendar event created successfully with ID: {formatted_id}", "GraphOps")
            console_telemetry_event("calendar_event_create_success", {
                "event_id": event_id,
                "user_id": user_id,
                "subject": subject
            }, "GraphOps")
            
            # Invalidate calendar list caches since we added a new event
            await self._invalidate_calendar_cache(user_id, event_id, 'create', location)
            
            return created_event
            
        except Exception as e:
            # Categorize and log the error with enhanced context
            error_info = self._categorize_graph_error(e, "create_calendar_event", {
                "user_id": user_id,
                "subject": subject,
                "has_attendees": attendees is not None and len(attendees) > 0,
                "has_location": location is not None
            })
            
            console_error(f"Failed to create calendar event: {e}", "GraphOps")
            console_telemetry_event("calendar_event_create_failed", {
                "user_id": user_id,
                "subject": subject,
                "error": str(e),
                "error_category": error_info["category"],
                "error_severity": error_info["severity"],
                "suggested_action": error_info["suggested_action"]
            }, "GraphOps")
            print("Full traceback:")
            traceback.print_exc()
            return None
    
    # Get specific calendar event by event ID
    @trace_async_method("get_calendar_event_by_id", include_args=True)
    async def get_calendar_event_by_id(self, user_id: str, event_id: str) -> Event:
        """
        Get a specific calendar event by its ID.
        
        Args:
            user_id (str): The ID of the user who owns the calendar event
            event_id (str): The ID of the event to retrieve
            
        Returns:
            Event: The calendar event, or None if not found
        """
        return await self._cache_wrapper(
            "get_calendar_event_by_id", 
            "calendar_events", 
            self._get_calendar_event_by_id_impl, 
            user_id, 
            event_id
        )
    
    async def _get_calendar_event_by_id_impl(self, user_id: str, event_id: str) -> Event:
        try:
            console_info(f"Retrieving calendar event: {self._format_event_id(event_id)}", "GraphOps")
            console_telemetry_event("calendar_event_get_start", {
                "user_id": user_id,
                "event_id": event_id
            }, "GraphOps")
            
            # Configure the request to get specific fields
            from msgraph.generated.users.item.calendar.events.item.event_item_request_builder import EventItemRequestBuilder
            
            query_params = EventItemRequestBuilder.EventItemRequestBuilderGetQueryParameters()
            query_params.select = self.calendar_response_fields
            
            request_configuration = EventItemRequestBuilder.EventItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            # Get the specific event
            event = await self._get_client().users.by_user_id(user_id).calendar.events.by_event_id(event_id).get(request_configuration=request_configuration)
            
            if event:
                formatted_id = self._format_event_id(event_id)
                event_subject = getattr(event, 'subject', 'No Subject')
                console_info(f"Retrieved calendar event: {event_subject} (ID: {formatted_id})", "GraphOps")
                console_telemetry_event("calendar_event_get_success", {
                    "user_id": user_id,
                    "event_id": event_id,
                    "subject": event_subject
                }, "GraphOps")
                
                # Log basic event details
                if hasattr(event, 'start') and event.start:
                    start_time = getattr(event.start, 'date_time', 'Unknown')
                    console_debug(f"Event start time: {start_time}", "GraphOps")
                
                if hasattr(event, 'location') and event.location:
                    location_name = getattr(event.location, 'display_name', 'Unknown')
                    console_debug(f"Event location: {location_name}", "GraphOps")
                
                return event
            else:
                formatted_id = self._format_event_id(event_id)
                console_warning(f"Calendar event not found: {formatted_id}", "GraphOps")
                console_telemetry_event("calendar_event_get_not_found", {
                    "user_id": user_id,
                    "event_id": event_id
                }, "GraphOps")
                return None
                
        except Exception as e:
            formatted_id = self._format_event_id(event_id)
            console_error(f"Failed to retrieve calendar event {formatted_id}: {e}", "GraphOps")
            console_telemetry_event("calendar_event_get_failed", {
                "user_id": user_id,
                "event_id": event_id,
                "error": str(e)
            }, "GraphOps")
            print("Full traceback:")
            traceback.print_exc()
            return None
    
    # Update calendar event by event ID
    @trace_async_method("update_calendar_event", include_args=True)
    async def update_calendar_event(self, user_id: str, event_id: str, subject: str = None, start: str = None, end: str = None, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None) -> Event:
        """
        Update an existing calendar event by event ID.
        
        Args:
            user_id (str): The ID of the user who owns the calendar event
            event_id (str): The ID of the event to update
            subject (str, optional): New subject/title of the event
            start (str, optional): New start date and time in ISO 8601 format
            end (str, optional): New end date and time in ISO 8601 format
            location (str, optional): New location of the event
            body (str, optional): New body content of the event
            attendees (List[str], optional): New list of required attendee email addresses (replaces existing)
            optional_attendees (List[str], optional): New list of optional attendee email addresses (replaces existing)
            
        Returns:
            Event: The updated calendar event, or None if update failed
        """
        try:
            console_info(f"Updating calendar event: {self._format_event_id(event_id)}", "GraphOps")
            console_telemetry_event("calendar_event_update_start", {
                "user_id": user_id,
                "event_id": event_id,
                "has_subject": subject is not None,
                "has_start": start is not None,
                "has_end": end is not None,
                "has_location": location is not None,
                "has_body": body is not None,
                "has_attendees": attendees is not None,
                "has_optional_attendees": optional_attendees is not None
            }, "GraphOps")
            
            # First, get the existing event to preserve unchanged fields
            existing_event = await self._get_client().users.by_user_id(user_id).calendar.events.by_event_id(event_id).get()
            
            if not existing_event:
                console_warning(f"Event with ID {self._format_event_id(event_id)} not found for user {user_id}", "GraphOps")
                console_telemetry_event("calendar_event_update_not_found", {
                    "user_id": user_id,
                    "event_id": event_id
                }, "GraphOps")
                return None
            
            console_debug(f"Updating calendar event: {self._format_event_id(event_id)}", "GraphOps")
            
            # Import required classes
            from msgraph.generated.models.event import Event
            from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
            from msgraph.generated.models.location import Location
            from msgraph.generated.models.item_body import ItemBody
            from msgraph.generated.models.body_type import BodyType
            from msgraph.generated.models.attendee import Attendee
            from msgraph.generated.models.email_address import EmailAddress
            
            # Create update object with only the fields that are being changed
            event_update = Event()
            
            # Update subject if provided
            if subject is not None:
                event_update.subject = subject
                console_debug(f"Updating subject: {subject}", "GraphOps")
            
            # Update start time if provided
            if start is not None:
                event_update.start = DateTimeTimeZone(date_time=start, time_zone="UTC")
                console_debug(f"Updating start time: {start}", "GraphOps")
            
            # Update end time if provided
            if end is not None:
                event_update.end = DateTimeTimeZone(date_time=end, time_zone="UTC")
                console_debug(f"Updating end time: {end}", "GraphOps")
            
            # Update location if provided
            if location is not None:
                event_update.location = Location(display_name=location)
                console_debug(f"Updating location: {location}", "GraphOps")
            
            # Update body if provided
            if body is not None:
                # If no body is provided but we want to clear it, use empty string
                enhanced_body = body or ""
                
                # If body is provided but empty, create a minimal default
                if not enhanced_body.strip():
                    enhanced_body = f"""
<html>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
    <p style="margin: 8px 0;">This meeting has been updated via the AI Calendar Assistant.</p>
</body>
</html>
                    """.strip()
                
                event_update.body = ItemBody(content_type=BodyType.Html, content=enhanced_body)
                body_preview = enhanced_body[:100] + "..." if len(enhanced_body) > 100 else enhanced_body
                console_debug(f"Updating body: {body_preview}", "GraphOps")
            
            # Update attendees if provided (this replaces all existing attendees)
            if attendees is not None or optional_attendees is not None:
                event_update.attendees = []
                
                # Add required attendees
                if attendees:
                    for attendee in attendees:
                        email_address = EmailAddress(address=attendee)
                        attendee_obj = Attendee(email_address=email_address)
                        attendee_obj.type = "required"
                        event_update.attendees.append(attendee_obj)
                    console_debug(f"Adding {len(attendees)} required attendees: {', '.join(attendees)}", "GraphOps")
                
                # Add optional attendees
                if optional_attendees:
                    for attendee in optional_attendees:
                        email_address = EmailAddress(address=attendee)
                        attendee_obj = Attendee(email_address=email_address)
                        attendee_obj.type = "optional"
                        event_update.attendees.append(attendee_obj)
                    console_debug(f"Adding {len(optional_attendees)} optional attendees: {', '.join(optional_attendees)}", "GraphOps")
                
                if not attendees and not optional_attendees:
                    console_debug("Clearing all attendees", "GraphOps")
            
            # Update the event in the user's calendar
            updated_event = await self._get_client().users.by_user_id(user_id).calendar.events.by_event_id(event_id).patch(event_update)
            
            # Log the successful update
            formatted_id = self._format_event_id(event_id)
            updated_subject = getattr(updated_event, 'subject', 'Unknown Subject')
            console_info(f"Calendar event updated successfully: {updated_subject} (ID: {formatted_id})", "GraphOps")
            console_telemetry_event("calendar_event_update_success", {
                "user_id": user_id,
                "event_id": event_id,
                "subject": updated_subject
            }, "GraphOps")
            
            # Invalidate related cache entries after successful update
            await self._invalidate_calendar_cache(user_id, event_id, "update", location)
            
            return updated_event
            
        except Exception as e:
            formatted_id = self._format_event_id(event_id)
            
            # Categorize and log the error with enhanced context
            error_info = self._categorize_graph_error(e, "update_calendar_event", {
                "user_id": user_id,
                "event_id": event_id,
                "has_subject": subject is not None,
                "has_start": start is not None,
                "has_end": end is not None
            })
            
            console_error(f"Failed to update calendar event {formatted_id}: {e}", "GraphOps")
            console_telemetry_event("calendar_event_update_failed", {
                "user_id": user_id,
                "event_id": event_id,
                "error": str(e),
                "error_category": error_info["category"],
                "error_severity": error_info["severity"],
                "suggested_action": error_info["suggested_action"]
            }, "GraphOps")
            print("Full traceback:")
            traceback.print_exc()
            return None
    
    # Update calendar event with online meeting support
    @trace_async_method("update_calendar_event_with_online_meeting", include_args=True)
    async def update_calendar_event_with_online_meeting(self, user_id: str, event_id: str, subject: str = None, start: str = None, end: str = None, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None, create_online_meeting: bool = False, meeting_platform: str = None) -> Event:
        """
        Update a calendar event with optional online meeting integration (Zoom or Teams).
        
        Args:
            user_id (str): The ID of the user who owns the calendar event
            event_id (str): The ID of the event to update
            subject (str, optional): New subject/title of the event
            start (str, optional): New start date and time in ISO 8601 format
            end (str, optional): New end date and time in ISO 8601 format
            location (str, optional): New location of the event
            body (str, optional): New body content of the event
            attendees (List[str], optional): New list of required attendee email addresses
            optional_attendees (List[str], optional): New list of optional attendee email addresses
            create_online_meeting (bool): Whether to create a new online meeting
            meeting_platform (str): Platform choice - defaults to 'teams', can specify 'zoom'
            
        Returns:
            Event: The updated calendar event with online meeting info if requested
            
        Raises:
            ValueError: If platform is invalid
        """
        try:
            online_meeting_info = None
            enhanced_body = body
            enhanced_location = location
            
            # Create online meeting if requested
            if create_online_meeting:
                # Default to Teams if no platform specified
                if meeting_platform is None:
                    meeting_platform = 'teams'
                    print("ℹ️ No platform specified for update, defaulting to Microsoft Teams")
                    
                # Use existing subject and times if not provided for the meeting
                existing_event = await self.get_calendar_event_by_id(user_id, event_id)
                if existing_event:
                    meeting_subject = subject or getattr(existing_event, 'subject', 'Updated Meeting')
                    meeting_start = start or (getattr(existing_event.start, 'date_time', None) if hasattr(existing_event, 'start') and existing_event.start else None)
                    meeting_end = end or (getattr(existing_event.end, 'date_time', None) if hasattr(existing_event, 'end') and existing_event.end else None)
                    
                    if meeting_start and meeting_end:
                        online_meeting_info = await self.create_online_meeting(user_id, meeting_subject, meeting_start, meeting_end, meeting_platform)
                        
                        if online_meeting_info:
                            platform_name = meeting_platform.title()
                            print(f"✅ {platform_name} meeting created for event update")
                            
                            # Enhance location to include meeting info
                            if meeting_platform.lower() == 'teams':
                                enhanced_location = f"Microsoft Teams Meeting - {online_meeting_info.get('join_url', 'Join URL not available')}"
                            elif meeting_platform.lower() == 'zoom':
                                enhanced_location = f"Zoom Meeting - {online_meeting_info.get('join_url', 'Join URL not available')}"
                            
                            # Enhance body to include meeting section
                            if enhanced_body is None:
                                enhanced_body = ""
                            
                            # Add meeting section to body
                            if meeting_platform.lower() == 'teams':
                                meeting_section = self._generate_teams_meeting_section(online_meeting_info)
                            elif meeting_platform.lower() == 'zoom':
                                meeting_section = self._generate_zoom_meeting_section(online_meeting_info)
                            
                            if enhanced_body:
                                enhanced_body += meeting_section
                            else:
                                enhanced_body = f"""
<html>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
    <p>This meeting has been updated with {platform_name} integration.</p>
    {meeting_section}
</body>
</html>
                                """.strip()
                        else:
                            print(f"❌ Failed to create {meeting_platform} meeting for event update")
                    else:
                        print("❌ Cannot create online meeting - missing start/end times")
                else:
                    print("❌ Cannot create online meeting - existing event not found")
            
            # Update the calendar event with the enhanced content
            updated_event = await self.update_calendar_event(
                user_id=user_id,
                event_id=event_id,
                subject=subject,
                start=start,
                end=end,
                location=enhanced_location,
                body=enhanced_body,
                attendees=attendees,
                optional_attendees=optional_attendees
            )
            
            # Log online meeting info if created
            if online_meeting_info:
                teams_meeting_id = online_meeting_info.get('id', 'N/A')
                formatted_teams_id = self._format_event_id(teams_meeting_id)
                print(f"📋 Online meeting linked to updated event: {formatted_teams_id}")
            
            return updated_event
            
        except Exception as e:
            formatted_id = self._format_event_id(event_id)
            print(f"❌ Failed to update calendar event with online meeting {formatted_id}: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None
    
    # Convenience method for partial calendar event updates
    @trace_async_method("patch_calendar_event", include_args=True)
    async def patch_calendar_event(self, user_id: str, event_id: str, **kwargs) -> Event:
        """
        Convenience method to update specific fields of a calendar event.
        
        Args:
            user_id (str): The ID of the user who owns the calendar event
            event_id (str): The ID of the event to update
            **kwargs: Fields to update (subject, start, end, location, body, attendees, optional_attendees)
            
        Returns:
            Event: The updated calendar event, or None if update failed
            
        Example:
            # Update only the subject and location
            updated_event = await graph_ops.patch_calendar_event(
                user_id="user-123", 
                event_id="event-456", 
                subject="New Meeting Title",
                location="Conference Room B"
            )
        """
        return await self.update_calendar_event(
            user_id=user_id,
            event_id=event_id,
            subject=kwargs.get('subject'),
            start=kwargs.get('start'),
            end=kwargs.get('end'),
            location=kwargs.get('location'),
            body=kwargs.get('body'),
            attendees=kwargs.get('attendees'),
            optional_attendees=kwargs.get('optional_attendees')
        )
    
    def _generate_teams_meeting_section(self, meeting_info: dict) -> str:
        """
        Generate a Teams meeting section in the standard format for email bodies.
        
        Args:
            meeting_info (dict): Meeting information from create_teams_meeting
            
        Returns:
            str: HTML formatted Teams meeting section
        """
        join_url = meeting_info.get('join_url', '')
        conference_id = meeting_info.get('conference_id', '')
        dial_in_url = meeting_info.get('dial_in_url', '')
        
        # Debug logging to check what we received
        print(f"🔍 Teams meeting section: Join URL={join_url}, Conference ID={conference_id}")
        
        # If no join_url, this is a problem - use a fallback or show error
        if not join_url:
            print("⚠️ WARNING: No join URL provided for Teams meeting section!")
            join_url = "https://teams.microsoft.com/l/meetup-join/[MISSING-JOIN-URL]"
        
        # Generate the Teams meeting section in the requested format
        teams_section = f"""
<div style="margin-top: 30px; padding: 20px; border-top: 2px solid #6264a7; background-color: #f8f9fa;">
    <table cellpadding="0" cellspacing="0" style="width: 100%; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <tr>
            <td>
                <h3 style="color: #6264a7; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">Join Microsoft Teams Meeting</h3>
                
                <div style="margin: 15px 0;">
                    <a href="{join_url}" style="display: inline-block; padding: 12px 20px; background-color: #6264a7; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">Click here to join the meeting</a>
                </div>
                
                <div style="margin: 20px 0; line-height: 1.6; color: #333;">"""
        
        # Add phone dial-in information if available
        if conference_id:
            # Extract phone number from dial_in_url or use default
            phone_number = "+1 323-849-4874"  # Default US number
            teams_section += f"""
                    <p style="margin: 5px 0; font-size: 14px;"><strong>{phone_number}</strong> &nbsp;&nbsp; United States, Los Angeles (Toll)</p>
                    <p style="margin: 5px 0; font-size: 14px;"><strong>Conference ID:</strong> {conference_id}#</p>
                    """
        
        # Add footer links
        teams_section += f"""
                    <p style="margin: 15px 0 5px 0; font-size: 14px;">
                        <a href="{dial_in_url if dial_in_url else '#'}" style="color: #6264a7; text-decoration: none;">Local numbers</a> |
                        <a href="#" style="color: #6264a7; text-decoration: none;">Reset PIN</a> |
                        <a href="https://aka.ms/JoinTeamsMeeting" style="color: #6264a7; text-decoration: none;">Learn more about Teams</a> |
                        <a href="{join_url}" style="color: #6264a7; text-decoration: none;">Meeting Options</a>
                    </p>
                </div>
            </td>
        </tr>
    </table>
</div>
        """
        
        return teams_section.strip()

    def _generate_zoom_meeting_section(self, online_meeting_info: dict) -> str:
        """
        Generate a Zoom meeting section in a clean format for email bodies.
        
        Args:
            online_meeting_info (dict): Dictionary containing Zoom meeting details
            
        Returns:
            str: HTML formatted Zoom meeting section
        """
        join_url = online_meeting_info.get('join_url', '')
        meeting_id = online_meeting_info.get('meeting_id', 'N/A')
        passcode = online_meeting_info.get('passcode', 'N/A')
        dial_in_numbers = online_meeting_info.get('dial_in_numbers', 'See meeting details')
        
        # Generate the Zoom meeting section in a clean format
        zoom_section = f"""
<div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #2d8cff; border-radius: 4px; margin: 20px 0;">
    <h3 style="color: #2d8cff; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">Join Zoom Meeting</h3>
    
    <table cellpadding="8" cellspacing="0" style="width: 100%; margin: 15px 0;">
        <tr>
            <td style="padding: 12px; background-color: #2d8cff; border-radius: 6px; text-align: center;">
                <a href="{join_url}" style="color: white; text-decoration: none; font-weight: bold; font-size: 16px; display: block;">Click here to join the meeting</a>
            </td>
        </tr>
    </table>
    
    <table cellpadding="8" cellspacing="0" style="width: 100%; background-color: #e3f2fd; padding: 15px; border-radius: 4px; margin: 15px 0;">
        <tr>
            <td>
                <p style="margin: 5px 0; font-size: 14px;"><strong>Meeting ID:</strong> <span style="font-family: monospace;">{meeting_id}</span></p>
                <p style="margin: 5px 0; font-size: 14px;"><strong>Passcode:</strong> <span style="font-family: monospace;">{passcode}</span></p>
                <p style="margin: 5px 0; font-size: 14px;"><strong>One tap mobile:</strong><br/>
                <a href="tel:{dial_in_numbers}" style="color: #2d8cff; text-decoration: none; font-family: monospace; font-size: 13px;">{dial_in_numbers}</a></p>
            </td>
        </tr>
    </table>
    
    <table cellpadding="8" cellspacing="0" style="width: 100%; margin: 10px 0;">
        <tr>
            <td style="font-size: 12px; color: #666; line-height: 1.4;">
                <a href="https://zoom.us/download" style="color: #2d8cff; text-decoration: none;">Download Zoom</a> | 
                <a href="https://zoom.us/test" style="color: #2d8cff; text-decoration: none;">Test your setup</a> | 
                <a href="https://support.zoom.us/hc/en-us" style="color: #2d8cff; text-decoration: none;">Zoom Help</a>
            </td>
        </tr>
    </table>
</div>
        """
        
        return zoom_section.strip()

    # Create Microsoft Teams meeting
    @trace_async_method("create_teams_meeting")
    async def create_teams_meeting(self, user_id: str, subject: str, start: str, end: str, body: str = None) -> dict:
        """
        Create a Microsoft Teams meeting using Microsoft Graph API.
        
        Args:
            user_id (str): The ID of the user creating the meeting
            subject (str): The subject/title of the meeting
            start (str): Start date and time in ISO 8601 format
            end (str): End date and time in ISO 8601 format
            body (str): Optional detailed description/agenda for the meeting
            
        Returns:
            dict: Teams meeting information including join URL and conference ID
        """
        try:
            console_info(f"Creating Teams meeting: '{subject}' for user {user_id}", "GraphOps")
            
            # Create Teams meeting using the Graph API with proper error handling
            online_meeting = OnlineMeeting(
                subject=subject,
                start_date_time=start,
                end_date_time=end
            )
            
            # Add body content if provided
            if body:
                from msgraph.generated.models.item_body import ItemBody
                from msgraph.generated.models.body_type import BodyType
                online_meeting.body = ItemBody(
                    content_type=BodyType.Html,
                    content=body
                )
            
            # Create the Teams meeting with retry logic for transient failures
            created_meeting = await self._get_client().users.by_user_id(user_id).online_meetings.post(online_meeting)
            
            # Debug: Print the actual response from Microsoft Graph (simplified)
            print(f"🔍 Teams meeting created:")
            print(f"   Meeting ID: {getattr(created_meeting, 'id', 'None')}")
            print(f"   Join URL: {getattr(created_meeting, 'join_web_url', 'None')}")
            if created_meeting.audio_conferencing:
                print(f"   Conference ID: {getattr(created_meeting.audio_conferencing, 'conference_id', 'None')}")
            
            # Try different possible attribute names for the join URL
            possible_join_urls = [
                getattr(created_meeting, 'join_web_url', None),
                getattr(created_meeting, 'join_url', None),
                getattr(created_meeting, 'web_url', None),
                getattr(created_meeting, 'joinWebUrl', None),
            ]
            
            join_url = None
            for url in possible_join_urls:
                if url:
                    join_url = url
                    break
            
            print(f"   Selected join URL: {join_url}")
            
            # Extract relevant information with safe attribute access
            meeting_info = {
                'id': getattr(created_meeting, 'id', None),
                'join_url': join_url,
                'conference_id': getattr(created_meeting.audio_conferencing, 'conference_id', None) if created_meeting.audio_conferencing else None,
                'dial_in_url': getattr(created_meeting.audio_conferencing, 'dial_in_url', None) if created_meeting.audio_conferencing else None,
                'subject': getattr(created_meeting, 'subject', subject),
                'platform': 'teams',
                'start_time': start,
                'end_time': end,
                'chat_info': {
                    'thread_id': getattr(created_meeting.chat_info, 'thread_id', None) if created_meeting.chat_info else None,
                    'message_id': getattr(created_meeting.chat_info, 'message_id', None) if created_meeting.chat_info else None
                } if created_meeting.chat_info else None
            }
            
            console_info(f"✅ Teams meeting created successfully: {meeting_info['id']}", "GraphOps")
            print(f"   Join URL: {meeting_info['join_url']}")
            print(f"   Conference ID: {meeting_info.get('conference_id', 'N/A')}")
            
            console_telemetry_event("teams_meeting_created", {
                "meeting_id": meeting_info['id'],
                "user_id": user_id,
                "has_join_url": bool(meeting_info['join_url']),
                "has_audio_conferencing": bool(meeting_info['conference_id'])
            }, "GraphOps")
            
            return meeting_info
            
        except Exception as e:
            error_msg = f"Failed to create Teams meeting for user {user_id}: {e}"
            
            # Check for specific permission errors and provide helpful guidance
            if hasattr(e, 'code') and e.code == 403:
                if "No application access policy found" in str(e):
                    # Try to get the client ID from environment or config
                    import os
                    client_id = os.environ.get('ENTRA_GRAPH_APPLICATION_CLIENT_ID', 'YOUR_APP_ID_HERE')
                    
                    error_msg += "\n"
                    error_msg += "🔧 SOLUTION: This error indicates missing Application Access Policy for Teams meetings.\n"
                    error_msg += "   Your Azure AD permissions are correct, but you need a Teams policy.\n"
                    error_msg += "\n"
                    error_msg += "   📋 PowerShell Commands (Run as Teams Admin):\n"
                    error_msg += "   1. Install-Module MicrosoftTeams -Force\n"
                    error_msg += "   2. Connect-MicrosoftTeams\n"
                    error_msg += f"   3. New-CsApplicationAccessPolicy -Identity 'GraphAppPolicy' -AppIds '{client_id}'\n"
                    error_msg += "   4. Grant-CsApplicationAccessPolicy -PolicyName 'GraphAppPolicy' -Global\n"
                    error_msg += "   5. Wait 5-10 minutes for policy propagation, then retry\n"
                    error_msg += "\n"
                    error_msg += f"   💡 Your App ID: {client_id}\n"
                    error_msg += "   📖 See _fix_teams_meeting_permissions.md for detailed instructions"
                elif "Forbidden" in str(e) or "Insufficient privileges" in str(e):
                    error_msg += "\n"
                    error_msg += "🔧 SOLUTION: Missing required permissions.\n"
                    error_msg += "   Required permissions: OnlineMeetings.ReadWrite.All, User.Read.All, Calendars.ReadWrite\n"
                    error_msg += "   Make sure Admin Consent is granted for these application permissions."
            
            console_error(error_msg, "GraphOps")
            console_telemetry_event("teams_meeting_creation_failed", {
                "user_id": user_id,
                "error": str(e),
                "error_code": getattr(e, 'code', 'Unknown'),
                "subject": subject
            }, "GraphOps")
            traceback.print_exc()
            return None

    # Create Zoom online meeting
    @trace_async_method("create_zoom_meeting", include_args=True)
    async def create_zoom_meeting(self, user_id: str, subject: str, start: str, end: str, body: str = None) -> dict:
        """
        Create a Zoom online meeting.
        
        Args:
            user_id (str): The ID of the user creating the meeting
            subject (str): The subject/title of the meeting
            start (str): Start date and time in ISO 8601 format
            end (str): End date and time in ISO 8601 format
            body (str): Optional detailed description/agenda for the meeting
            
        Returns:
            dict: Zoom meeting information including join URL and meeting ID
        """
        try:
            # For now, create a placeholder Zoom meeting structure
            # TODO: Integrate with Zoom API when credentials are available
            
            # Generate a mock Zoom meeting ID (in production, this would come from Zoom API)
            import uuid
            zoom_meeting_id = str(uuid.uuid4())[:8].replace('-', '').upper()
            
            # Create Zoom meeting info structure
            meeting_info = {
                'id': zoom_meeting_id,
                'join_url': f"https://zoom.us/j/{zoom_meeting_id}",
                'meeting_id': zoom_meeting_id,
                'passcode': '123456',  # In production, generated by Zoom API
                'subject': subject,
                'platform': 'zoom',
                'dial_in_numbers': '+1 669 900 6833',  # Standard Zoom dial-in
                'international_numbers': 'https://zoom.us/u/ad8EXAMPLE'
            }
            
            print(f"🎥 Created Zoom meeting: {zoom_meeting_id}")
            return meeting_info
            
        except Exception as e:
            print(f"An error occurred while creating Zoom meeting: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    # Generic online meeting creation (defaults to Teams)
    async def create_online_meeting(self, user_id: str, subject: str, start: str, end: str, platform: str = None, body: str = None) -> dict:
        """
        Create an online meeting using the specified platform.
        
        Args:
            user_id (str): The ID of the user creating the meeting
            subject (str): The subject/title of the meeting
            start (str): Start date and time in ISO 8601 format
            end (str): End date and time in ISO 8601 format
            platform (str): Meeting platform - defaults to 'teams', can specify 'zoom'
            body (str): Optional detailed description/agenda for the meeting
            
        Returns:
            dict: Online meeting information including join URL and meeting details
            
        Raises:
            ValueError: If platform is invalid
        """
        # Default to Teams if no platform specified
        if platform is None:
            platform = 'teams'
            print("ℹ️ No platform specified, defaulting to Microsoft Teams")
            
        if platform.lower() == 'teams':
            # Use real Microsoft Graph API for Teams meetings (M365 users)
            return await self.create_teams_meeting(user_id, subject, start, end, body)
        elif platform.lower() == 'zoom':
            # Use mocked Zoom endpoint
            return await self.create_zoom_meeting(user_id, subject, start, end, body)
        else:
            raise ValueError(f"Invalid platform '{platform}'. Choose 'zoom' or 'teams'")

    # Enhanced create calendar event with online meeting options
    @trace_async_method("create_calendar_event_with_online_meeting", include_args=True)
    async def create_calendar_event_with_online_meeting(self, user_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None, create_online_meeting: bool = False, meeting_platform: str = None) -> Event:
        """
        Create a calendar event with optional online meeting integration (Zoom or Teams).
        
        Args:
            user_id (str): The ID of the user creating the event
            subject (str): The subject/title of the event
            start (str): Start date and time in ISO 8601 format
            end (str): End date and time in ISO 8601 format
            location (str, optional): Location of the event
            body (str, optional): Body content of the event
            attendees (List[str], optional): Required attendee email addresses
            optional_attendees (List[str], optional): Optional attendee email addresses
            create_online_meeting (bool): Whether to create an online meeting
            meeting_platform (str): Platform choice - defaults to 'teams', can specify 'zoom'
            
        Returns:
            Event: The created calendar event with online meeting info if requested
            
        Raises:
            ValueError: If platform is invalid
        """
        try:
            online_meeting_info = None
            enhanced_body = body or ""
            enhanced_location = location
            
            # Create online meeting if requested
            if create_online_meeting:
                # Default to Teams if no platform specified
                if meeting_platform is None:
                    meeting_platform = 'teams'
                    print("ℹ️ No meeting platform specified, defaulting to Microsoft Teams")
                    
                online_meeting_info = await self.create_online_meeting(user_id, subject, start, end, meeting_platform)
                
                if online_meeting_info:
                    platform = online_meeting_info.get('platform', meeting_platform)
                    
                    if platform == 'teams':
                        # Update location to proper Teams meeting format with join URL
                        join_url = online_meeting_info.get('join_url', '')
                        if join_url:
                            enhanced_location = f"Microsoft Teams Meeting\n{join_url}"
                        else:
                            enhanced_location = "Microsoft Teams Meeting"
                        
                        # Enhance body with Teams meeting information - email-friendly HTML
                        teams_meeting_section = self._generate_teams_meeting_section(online_meeting_info)
                        
                        # Combine original body with Teams meeting section
                        if enhanced_body and enhanced_body.strip():
                            enhanced_body = f"{enhanced_body}\n\n{teams_meeting_section}"
                        else:
                            enhanced_body = teams_meeting_section
                    else:  # Zoom
                        # Update location to proper Zoom meeting format with join URL
                        join_url = online_meeting_info.get('join_url', '')
                        if join_url:
                            enhanced_location = f"Zoom Meeting\n{join_url}"
                        else:
                            enhanced_location = "Zoom Meeting"
                        
                        # Enhance body with Zoom meeting information - email-friendly HTML
                        zoom_meeting_section = self._generate_zoom_meeting_section(online_meeting_info)
                        
                        # Combine original body with Zoom meeting section
                        if enhanced_body and enhanced_body.strip():
                            enhanced_body = f"{enhanced_body}\n\n{zoom_meeting_section}"
                        else:
                            enhanced_body = zoom_meeting_section
                else:
                    print(f"⚠️ Failed to create {meeting_platform} meeting, proceeding with regular calendar event")
            
            # Create the event object with enhanced content
            event = Event(
                subject=subject,
                start=DateTimeTimeZone(date_time=start, time_zone="UTC"),
                end=DateTimeTimeZone(date_time=end, time_zone="UTC"),
                location=Location(display_name=enhanced_location) if enhanced_location else None,
                body=ItemBody(content_type=BodyType.Html, content=enhanced_body) if enhanced_body else None,
                attendees=[]
            )
            
            # Add online meeting info to the event if available
            if online_meeting_info and create_online_meeting:
                # The Teams meeting info is already included in the enhanced_body and enhanced_location
                # We don't need to set additional properties that might cause deserialization issues
                print(f"✅ Teams meeting info added to event body and location")
            
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
            
            # Log the created event ID and Teams meeting info for reference
            event_id = getattr(created_event, 'id', 'Unknown')
            formatted_event_id = self._format_event_id(event_id)
            if online_meeting_info:
                teams_meeting_id = online_meeting_info.get('id', 'N/A')
                formatted_teams_id = self._format_event_id(teams_meeting_id)
                console_info(f"Calendar event with online meeting created with ID: {formatted_event_id}", "GraphOps")
                console_info(f"Teams meeting linked with ID: {formatted_teams_id}", "GraphOps")
                console_telemetry_event("calendar_event_with_online_meeting_create_success", {
                    "event_id": event_id,
                    "teams_meeting_id": teams_meeting_id,
                    "user_id": user_id,
                    "subject": subject,
                    "meeting_platform": meeting_platform
                }, "GraphOps")
            else:
                console_info(f"Calendar event created with ID: {formatted_event_id}", "GraphOps")
                console_telemetry_event("calendar_event_create_success", {
                    "event_id": event_id,
                    "user_id": user_id,
                    "subject": subject
                }, "GraphOps")
            
            # Invalidate calendar list caches since we added a new event
            await self._invalidate_calendar_cache(user_id, event_id, 'create_with_online_meeting', location)
            
            return created_event
            
        except Exception as e:
            console_error(f"An error occurred while creating calendar event with online meeting: {e}", "GraphOps")
            console_telemetry_event("calendar_event_with_online_meeting_create_failed", {
                "user_id": user_id,
                "subject": subject,
                "error": str(e),
                "meeting_platform": meeting_platform if 'meeting_platform' in locals() else None
            }, "GraphOps")
            return None

    # Backward compatibility method for Teams meetings
    @trace_async_method("create_calendar_event_with_teams", include_args=True)
    async def create_calendar_event_with_teams(self, user_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: List[str] = None, optional_attendees: List[str] = None, create_teams_meeting: bool = False) -> Event:
        """
        Create a calendar event with Teams meeting (backward compatibility wrapper).
        """
        return await self.create_calendar_event_with_online_meeting(
            user_id=user_id,
            subject=subject,
            start=start,
            end=end,
            location=location,
            body=body,
            attendees=attendees,
            optional_attendees=optional_attendees,
            create_online_meeting=create_teams_meeting,
            meeting_platform='teams'
        )

    # Get and display conference room events
    async def get_conference_room_events(self, conference_rooms: List[User], start_date: datetime = None, end_date: datetime = None) -> List[dict]:
        """
        Get and display calendar events for a list of conference rooms.
        
        Args:
            conference_rooms (List[User]): List of conference room User objects
            start_date (datetime, optional): Start date for filtering events
            end_date (datetime, optional): End date for filtering events
            
        Returns:
            List[dict]: List of conference room objects with their events
        """
        return await self._cache_wrapper(
            "get_conference_room_events", 
            "conference_room_events", 
            self._get_conference_room_events_impl, 
            conference_rooms, 
            start_date, 
            end_date
        )
    
    async def _get_conference_room_events_impl(self, conference_rooms: List[User], start_date: datetime = None, end_date: datetime = None) -> List[dict]:
        try:
            conference_rooms_with_events = []
            
            for room in conference_rooms:
                print(60 * "=")
                
                # Handle both User objects and dictionary objects
                if isinstance(room, dict):
                    room_id = room.get('id')
                    display_name = room.get('displayName') or room.get('display_name')
                    user_principal_name = room.get('userPrincipalName') or room.get('user_principal_name')
                    mail = room.get('mail')
                    job_title = room.get('jobTitle') or room.get('job_title')
                elif hasattr(room, 'id'):  # User object
                    room_id = self._get_user_attribute(room, 'id')
                    display_name = self._get_user_attribute(room, 'display_name') or self._get_user_attribute(room, 'displayName')
                    user_principal_name = self._get_user_attribute(room, 'user_principal_name') or self._get_user_attribute(room, 'userPrincipalName')
                    mail = self._get_user_attribute(room, 'mail')
                    job_title = self._get_user_attribute(room, 'job_title') or self._get_user_attribute(room, 'jobTitle')
                else:
                    print(f"Warning: Unknown room object type: {type(room)}")
                    continue
                
                print(f"ID: {room_id}")
                print(f"Display Name: {display_name}")
                print(f"User Principal Name: {user_principal_name}")
                print(f"Mail: {mail}")
                print(f"Job Title: {job_title}")
                
                # Handle department and manager fields (may not exist in all objects)
                if isinstance(room, dict):
                    department = room.get('department')
                    manager = room.get('manager')
                elif hasattr(room, 'department'):
                    department = room.department
                    manager = room.manager
                else:
                    department = None
                    manager = None
                    
                print(f"Department: {department}")
                print(f"Manager: {manager}")

                # Get calendar events for this room
                get_calendar_events = await self.get_user_calendar_events_by_user_id(room_id, start_date, end_date)
                
                # Process events into a structured format
                events_list = []
                if get_calendar_events:
                    print(f"Found {len(get_calendar_events)} calendar events for room {display_name}")
                    for event in get_calendar_events:
                        # Print event details (keeping original console output) with safe attribute access
                        event_id = getattr(event, 'id', 'Unknown')
                        event_subject = getattr(event, 'subject', 'No subject')
                        formatted_id = self._format_event_id(event_id)
                        print(f"Event ID: {formatted_id}")
                        print(f"Event Subject: {event_subject}")
                        
                        # Safe access to start/end times
                        start_info = getattr(event, 'start', None)
                        end_info = getattr(event, 'end', None)
                        
                        if start_info:
                            start_datetime = getattr(start_info, 'date_time', 'Unknown time')
                            start_timezone = getattr(start_info, 'time_zone', 'Unknown timezone')
                            print(f"Start: {start_datetime} {start_timezone}")
                        
                        if end_info:
                            end_datetime = getattr(end_info, 'date_time', 'Unknown time')
                            end_timezone = getattr(end_info, 'time_zone', 'Unknown timezone')
                            print(f"End: {end_datetime} {end_timezone}")
                        
                        # Safe location access
                        location_info = getattr(event, 'location', None)
                        location_display = getattr(location_info, 'display_name', 'No location') if location_info else 'No location'
                        print(f"Location: {location_display}")
                        
                        # Safe body access
                        if hasattr(event, 'body') and event.body and hasattr(event.body, 'content') and event.body.content:
                            print(f"Description: {event.body.content}")
                        print("Attendees:")
                        
                        # Safe attendees access
                        attendees = getattr(event, 'attendees', []) or []
                        for attendee in attendees:
                            email_addr = getattr(attendee, 'email_address', None)
                            if email_addr:
                                email = getattr(email_addr, 'address', 'Unknown email')
                                attendee_type = getattr(attendee, 'type', 'Unknown type')
                                print(f"  - {email} ({attendee_type})")
                        
                        # Create structured event data with safe access
                        attendees_list = []
                        if attendees:
                            for attendee in attendees:
                                email_addr = getattr(attendee, 'email_address', None)
                                if email_addr:
                                    attendees_list.append({
                                        "email": getattr(email_addr, 'address', ''),
                                        "type": getattr(attendee, 'type', ''),
                                        "name": getattr(email_addr, 'name', '') or getattr(email_addr, 'address', '')
                                    })
                        
                        event_data = {
                            "id": getattr(event, 'id', ''),
                            "subject": event_subject or '',
                            "body": event.body.content if (hasattr(event, 'body') and event.body and hasattr(event.body, 'content') and event.body.content) else '',
                            "start": {
                                "date_time": start_datetime if start_info else '',
                                "time_zone": start_timezone if start_info else ''
                            },
                            "end": {
                                "date_time": end_datetime if end_info else '',
                                "time_zone": end_timezone if end_info else ''
                            },
                            "location": location_display,
                            "attendees": attendees_list
                        }
                        events_list.append(event_data)
                else:
                    print(f"No calendar events found for room {display_name}")
                
                # Create structured room data with events
                room_data = {
                    "id": room_id,
                    "display_name": display_name,
                    "user_principal_name": user_principal_name,
                    "mail": mail,
                    "job_title": job_title,
                    "department": department,
                    "manager": manager,
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


