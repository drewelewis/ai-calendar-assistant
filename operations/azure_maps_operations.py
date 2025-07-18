import os

# CRITICAL: Check telemetry disable flag BEFORE any other imports
TELEMETRY_EXPLICITLY_DISABLED = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', '').lower() in ('true', '1', 'yes')

if TELEMETRY_EXPLICITLY_DISABLED:
    print("🚫 Telemetry explicitly disabled via environment variable")

import traceback
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional, Any
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.core.exceptions import ClientAuthenticationError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without loading .env file
    pass

# Production-grade telemetry import with timeout and graceful fallback
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
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_import_telemetry_modules)
            try:
                # Wait for import with timeout
                return future.result(timeout=TELEMETRY_IMPORT_TIMEOUT)
            except FutureTimeoutError:
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
                    if os.environ.get('DEBUG_AZURE_MAPS', '').lower() in ('true', '1'):
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
        prefix = f"[{module}]" if module else "[AzureMaps]"
        print(f"{timestamp} INFO {prefix} {message}")
    
    def console_debug(message, module=None):
        """Production console debug (only in debug mode)."""
        if os.environ.get('DEBUG_AZURE_MAPS', '').lower() in ('true', '1'):
            timestamp = datetime.now().isoformat()
            prefix = f"[{module}]" if module else "[AzureMaps]"
            print(f"{timestamp} DEBUG {prefix} {message}")
    
    def console_warning(message, module=None):
        """Production console warning."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[AzureMaps]"
        print(f"{timestamp} WARNING {prefix} {message}")
    
    def console_error(message, module=None):
        """Production console error."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[AzureMaps]"
        print(f"{timestamp} ERROR {prefix} {message}")
    
    def console_telemetry_event(event_name, properties=None, module=None):
        """Production telemetry event with structured logging."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[AzureMaps]"
        props_str = f" | {properties}" if properties else ""
        print(f"{timestamp} TELEMETRY {prefix} {event_name}{props_str}")

class AzureMapsOperations:
    """
    Production Azure Maps Search Operations Client - Fast Loading Version
    
    This version prioritizes fast startup and never hangs on telemetry imports.
    Perfect for local development, testing, and production deployments.
    """
    
    def __init__(self, 
                 subscription_key: Optional[str] = None,
                 client_id: Optional[str] = None,
                 base_url: str = "https://atlas.microsoft.com",
                 timeout: int = 30,
                 max_retries: int = 3):
        """Initialize the fast-loading Azure Maps client."""
        self.base_url = base_url.rstrip('/')
        self.subscription_key = subscription_key or os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
        self.client_id = client_id or os.environ.get("AZURE_MAPS_CLIENT_ID")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        
        console_info(f"Azure Maps Operations initialized (telemetry: {'enabled' if TELEMETRY_AVAILABLE else 'disabled'})", "AzureMaps")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    def get_telemetry_status(self) -> Dict[str, Any]:
        """Get comprehensive telemetry status."""
        return {
            "telemetry_available": TELEMETRY_AVAILABLE,
            "telemetry_disabled": TELEMETRY_EXPLICITLY_DISABLED,
            "mode": "production_fast_load",
            "startup_time": "optimized",
            "hanging_prevention": "enabled"
        }
        
    @trace_async_method("azure_maps_test_connection")
    async def test_connection(self) -> Dict[str, Any]:
        """Fast connection test for production validation."""
        console_info("Starting fast connection test", "AzureMaps")
        start_time = datetime.now()
        
        try:
            # Quick session check
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Fast auth setup - use URL parameter method
            params = {"api-version": "1.0"}
            headers = {}
            
            if self.subscription_key:
                # Use subscription key as URL parameter (like working curl command)
                params["subscription-key"] = self.subscription_key
                auth_method = "subscription_key"
            else:
                # Use managed identity with Authorization header
                credential = DefaultAzureCredential()
                token = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: credential.get_token("https://atlas.microsoft.com/.default")
                )
                headers["Authorization"] = f"Bearer {token.token}"
                auth_method = "managed_identity"
            
            # Quick API test - use nearby search instead of categories
            url = f"{self.base_url}/search/nearby/json"
            # Add default coordinates for test (Seattle)
            params["lat"] = 47.6062
            params["lon"] = -122.3321
            
            async with self.session.get(url, headers=headers, params=params) as response:
                duration = (datetime.now() - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    results_count = len(result.get("results", []))
                    
                    console_info(f"Connection test successful: {results_count} nearby results in {duration:.3f}s", "AzureMaps")
                    
                    return {
                        "overall_status": "success",
                        "duration_seconds": duration,
                        "auth_method": auth_method,
                        "results_found": results_count,
                        "telemetry_mode": "enabled" if TELEMETRY_AVAILABLE else "disabled"
                    }
                else:
                    console_error(f"Connection test failed: {response.status}", "AzureMaps")
                    return {
                        "overall_status": "failed",
                        "status_code": response.status,
                        "duration_seconds": duration
                    }
                    
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            console_error(f"Connection test error: {e}", "AzureMaps")
            return {
                "overall_status": "error",
                "error": str(e),
                "duration_seconds": duration
            }
            
    async def get_poi_categories(self) -> List[Dict[str, Any]]:
        """Get POI categories with fast execution (using POI search)."""
        console_info("Fetching POI data using search", "AzureMaps")
        
        # Setup authentication - use URL parameter method
        params = {
            "api-version": "1.0",
            "query": "restaurant",  # Use a common category for demonstration
            "lat": 47.6062,         # Seattle coordinates
            "lon": -122.3321
        }
        headers = {}
        
        if self.subscription_key:
            # Use subscription key as URL parameter
            params["subscription-key"] = self.subscription_key
        else:
            # Use managed identity with Authorization header
            credential = DefaultAzureCredential()
            token = await asyncio.get_event_loop().run_in_executor(
                None, lambda: credential.get_token("https://atlas.microsoft.com/.default")
            )
            headers["Authorization"] = f"Bearer {token.token}"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.base_url}/search/poi/json"
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                result = await response.json()
                results = result.get("results", [])
                console_info(f"Retrieved {len(results)} POI results", "AzureMaps")
                
                # Extract unique categories from results
                categories = []
                seen_categories = set()
                for poi_result in results:
                    poi_info = poi_result.get("poi", {})
                    poi_categories = poi_info.get("categories", [])
                    for category in poi_categories:
                        if category not in seen_categories:
                            categories.append({
                                "id": category,
                                "name": category.replace("_", " ").title(),
                                "description": f"POI category: {category}"
                            })
                            seen_categories.add(category)
                
                return categories
            else:
                console_error(f"Failed to get POI data: {response.status}", "AzureMaps")
                raise Exception(f"POI search request failed: {response.status}")
                
    async def search_nearby(self, latitude: float, longitude: float, radius: int = 10, limit: int = 20) -> Dict[str, Any]:
        """Search nearby POIs with fast execution."""
        console_info(f"Searching near {latitude}, {longitude} within {radius}m", "AzureMaps")
        
        # Setup authentication and parameters
        params = {
            "api-version": "1.0",
            "lat": latitude,
            "lon": longitude,
            "radius": radius,
            "limit": limit
        }
        headers = {}
        
        if self.subscription_key:
            # Use subscription key as URL parameter
            params["subscription-key"] = self.subscription_key
        else:
            # Use managed identity with Authorization header
            credential = DefaultAzureCredential()
            token = await asyncio.get_event_loop().run_in_executor(
                None, lambda: credential.get_token("https://atlas.microsoft.com/.default")
            )
            headers["Authorization"] = f"Bearer {token.token}"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.base_url}/search/nearby/json"
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                result = await response.json()
                num_results = len(result.get("results", []))
                console_info(f"Found {num_results} nearby POIs", "AzureMaps")
                return result
            else:
                console_error(f"Nearby search failed: {response.status}", "AzureMaps")
                raise Exception(f"Nearby search failed: {response.status}")
            
    @trace_async_method("geolocate_city_state")
    async def geolocate_city_state(self, city: str, state: str) -> Optional[Dict[str, Any]]:
        """
        Geolocate a city and state to get coordinates and location details.
        
        Args:
            city (str): The city name to geolocate
            state (str): The state name to geolocate
            
        Returns:
            Optional[Dict[str, Any]]: Geolocation result with coordinates and details, or None if failed
        """
        console_info(f"🗺️ Looking up coordinates for {city}, {state}...", "AzureMaps")

        # Setup authentication and parameters
        params = {
            "api-version": "1.0",
            "city": city,
            "state": state
        }
        headers = {}

        if self.subscription_key:
            # Use subscription key as URL parameter
            params["subscription-key"] = self.subscription_key
        else:
            # Use managed identity with Authorization header
            credential = DefaultAzureCredential()
            token = await asyncio.get_event_loop().run_in_executor(
                None, lambda: credential.get_token("https://atlas.microsoft.com/.default")
            )
            headers["Authorization"] = f"Bearer {token.token}"

        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/search/geocode/json"

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                result = await response.json()
                console_info(f"Geolocation result: {result}", "AzureMaps")
                return result
            else:
                console_error(f"Geolocation failed: {response.status}", "AzureMaps")
                raise Exception(f"Geolocation failed: {response.status}")
