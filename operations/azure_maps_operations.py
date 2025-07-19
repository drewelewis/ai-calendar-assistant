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
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def diagnose_azure_maps_setup(self) -> Dict[str, Any]:
        """
        Diagnose Azure Maps configuration and managed identity setup.
        Useful for troubleshooting Azure deployment issues.
        """
        console_info("🔍 Starting Azure Maps setup diagnosis...", "AzureMaps")
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "subscription_key_available": bool(self.subscription_key),
            "client_id_available": bool(self.client_id),
            "managed_identity_test": None,
            "azure_maps_permissions": None,
            "recommendations": []
        }
        
        # Test managed identity authentication
        if not self.subscription_key:
            console_info("🔐 Testing managed identity authentication...", "AzureMaps")
            try:
                credential = DefaultAzureCredential()
                console_info("✅ DefaultAzureCredential created", "AzureMaps")
                
                # Test getting token
                token = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: credential.get_token("https://atlas.microsoft.com/.default")
                )
                
                diagnosis["managed_identity_test"] = {
                    "status": "success",
                    "token_acquired": True,
                    "expires_on": token.expires_on
                }
                console_info("✅ Managed identity token acquired successfully", "AzureMaps")
                
            except ClientAuthenticationError as e:
                diagnosis["managed_identity_test"] = {
                    "status": "auth_failed",
                    "error": str(e),
                    "token_acquired": False
                }
                diagnosis["recommendations"].append("Enable system-assigned or user-assigned managed identity")
                diagnosis["recommendations"].append("Ensure managed identity has Azure Maps Data Reader role")
                console_error(f"❌ Managed identity authentication failed: {e}", "AzureMaps")
                
            except Exception as e:
                diagnosis["managed_identity_test"] = {
                    "status": "error",
                    "error": str(e),
                    "token_acquired": False
                }
                console_error(f"❌ Token acquisition failed: {e}", "AzureMaps")
        else:
            diagnosis["managed_identity_test"] = {
                "status": "skipped",
                "reason": "subscription_key_available"
            }
            console_info("🔑 Using subscription key, skipping managed identity test", "AzureMaps")
        
        # Add general recommendations
        if not self.subscription_key and not diagnosis.get("managed_identity_test", {}).get("token_acquired"):
            diagnosis["recommendations"].extend([
                "Configure Azure Maps account with managed identity access",
                "Assign 'Azure Maps Data Reader' role to the managed identity", 
                "Ensure the resource has system-assigned managed identity enabled",
                "Check that the Azure Maps account allows managed identity authentication",
                "Verify the application is running in an Azure service that supports managed identity"
            ])
        
        # Log diagnosis results
        console_info("📋 Azure Maps Diagnosis Complete:", "AzureMaps")
        console_info(f"   • Subscription Key: {'✅ Available' if diagnosis['subscription_key_available'] else '❌ Not configured'}", "AzureMaps")
        console_info(f"   • Managed Identity: {diagnosis.get('managed_identity_test', {}).get('status', 'Unknown')}", "AzureMaps")
        
        if diagnosis["recommendations"]:
            console_info("💡 Recommendations:", "AzureMaps")
            for rec in diagnosis["recommendations"]:
                console_info(f"   • {rec}", "AzureMaps")
        
        return diagnosis
            
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
        console_info("🔗 Starting connection test...", "AzureMaps")
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
                console_info("🔑 Using subscription key authentication", "AzureMaps")
            else:
                # Use managed identity with Authorization header
                console_info("🔐 Attempting managed identity authentication...", "AzureMaps")
                
                # Debug environment variables
                msi_endpoint = os.environ.get("MSI_ENDPOINT")
                identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
                identity_header = os.environ.get("IDENTITY_HEADER")
                azure_client_id = os.environ.get("AZURE_CLIENT_ID")
                
                console_info(f"   • MSI_ENDPOINT: {'✅ Set' if msi_endpoint else '❌ Not set'}", "AzureMaps")
                console_info(f"   • IDENTITY_ENDPOINT: {'✅ Set' if identity_endpoint else '❌ Not set'}", "AzureMaps")
                console_info(f"   • IDENTITY_HEADER: {'✅ Set' if identity_header else '❌ Not set'}", "AzureMaps")
                console_info(f"   • AZURE_CLIENT_ID: {'✅ Set' if azure_client_id else '❌ Not set'}", "AzureMaps")
                
                if not (msi_endpoint or identity_endpoint):
                    console_error("❌ No managed identity endpoints found - not running in Azure environment", "AzureMaps")
                    raise Exception("Managed identity not available - must run in Azure Container App")
                
                try:
                    console_info("   🔄 Creating DefaultAzureCredential...", "AzureMaps")
                    credential = DefaultAzureCredential()
                    console_info("   ✅ DefaultAzureCredential created successfully", "AzureMaps")
                    
                    console_info("   🎫 Requesting access token for Azure Maps...", "AzureMaps")
                    token_scope = "https://atlas.microsoft.com/.default"
                    console_info(f"   • Token scope: {token_scope}", "AzureMaps")
                    
                    token = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: credential.get_token(token_scope)
                    )
                    
                    if token and token.token:
                        console_info(f"   ✅ Token acquired successfully!", "AzureMaps")
                        console_info(f"   • Token length: {len(token.token)} characters", "AzureMaps")
                        console_info(f"   • Token expires: {token.expires_on}", "AzureMaps")
                        console_info(f"   • Token preview: {token.token[:20]}...", "AzureMaps")
                        
                        headers["Authorization"] = f"Bearer {token.token}"
                        
                        # Add required x-ms-client-id header for Azure Maps managed identity
                        if self.client_id:
                            headers["x-ms-client-id"] = self.client_id
                            console_info(f"   🆔 Added x-ms-client-id header: {self.client_id}", "AzureMaps")
                        else:
                            console_error("   ❌ Missing AZURE_MAPS_CLIENT_ID for managed identity authentication", "AzureMaps")
                        
                        auth_method = "managed_identity"
                        console_info("   🔐 Authorization header set with Bearer token", "AzureMaps")
                    else:
                        console_error("   ❌ Token acquisition returned None", "AzureMaps")
                        raise Exception("Token acquisition failed - no token returned")
                        
                except Exception as token_error:
                    console_error(f"   ❌ Token acquisition failed: {token_error}", "AzureMaps")
                    console_error(f"   • Error type: {type(token_error).__name__}", "AzureMaps")
                    console_error(f"   • Error details: {str(token_error)}", "AzureMaps")
                    
                    # Try different credential types for debugging
                    console_info("   🔄 Trying alternative credential types...", "AzureMaps")
                    
                    try:
                        from azure.identity import ManagedIdentityCredential
                        console_info("   🧪 Testing ManagedIdentityCredential (system-assigned)...", "AzureMaps")
                        mi_credential = ManagedIdentityCredential()
                        mi_token = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: mi_credential.get_token(token_scope)
                        )
                        
                        if mi_token and mi_token.token:
                            console_info("   ✅ ManagedIdentityCredential succeeded!", "AzureMaps")
                            headers["Authorization"] = f"Bearer {mi_token.token}"
                            
                            # Add required x-ms-client-id header for Azure Maps managed identity
                            if self.client_id:
                                headers["x-ms-client-id"] = self.client_id
                                console_info(f"   🆔 Added x-ms-client-id header: {self.client_id}", "AzureMaps")
                            else:
                                console_error("   ❌ Missing AZURE_MAPS_CLIENT_ID for managed identity authentication", "AzureMaps")
                            
                            auth_method = "managed_identity_explicit"
                        else:
                            console_error("   ❌ ManagedIdentityCredential also failed", "AzureMaps")
                            raise Exception("All managed identity methods failed")
                            
                    except Exception as mi_error:
                        console_error(f"   ❌ ManagedIdentityCredential failed: {mi_error}", "AzureMaps")
                        raise Exception(f"Managed identity authentication failed: {token_error}")
                
                console_info("🔐 Managed identity authentication configured successfully", "AzureMaps")
            
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
        console_info("📋 Fetching POI categories...", "AzureMaps")
        
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
            
            # Add required x-ms-client-id header for Azure Maps managed identity
            if self.client_id:
                headers["x-ms-client-id"] = self.client_id
            else:
                console_error("Missing AZURE_MAPS_CLIENT_ID for managed identity authentication", "AzureMaps")
        
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
                
    async def search_nearby(self, 
                           latitude: float, 
                           longitude: float, 
                           radius: int = 10, 
                           limit: int = 20, 
                           category_set: Optional[List[int]] = None,
                           brand_set: Optional[List[str]] = None,
                           country_set: Optional[List[str]] = None,
                           language: str = "en-US") -> Dict[str, Any]:
        """Search nearby POIs with fast execution."""
        console_info(f"🔍 Searching near {latitude}, {longitude} within {radius}m...", "AzureMaps")
        
        # Setup authentication and parameters
        params = {
            "api-version": "1.0",
            "lat": latitude,
            "lon": longitude,
            "radius": radius,
            "limit": limit,
            "language": language
        }
        
        # Add optional filters
        if category_set:
            params["categorySet"] = ",".join(map(str, category_set))
        if brand_set:
            params["brandSet"] = ",".join(brand_set)
        if country_set:
            params["countrySet"] = ",".join(country_set)
        
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
            
            # Add required x-ms-client-id header for Azure Maps managed identity
            if self.client_id:
                headers["x-ms-client-id"] = self.client_id
            else:
                console_error("Missing AZURE_MAPS_CLIENT_ID for managed identity authentication", "AzureMaps")

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

        # Setup authentication and parameters for search geocoding
        # Use the search/address/json endpoint instead of search/geocode/json
        params = {
            "api-version": "1.0",
            "query": f"{city}, {state}",  # Combined query format
            "limit": 1,  # Only need the best match
            "countrySet": "US"  # Limit to US for state searches
        }
        headers = {}

        if self.subscription_key:
            # Use subscription key as URL parameter
            params["subscription-key"] = self.subscription_key
            console_info("🔑 Using subscription key authentication for geocoding", "AzureMaps")
        else:
            # Use managed identity with Authorization header
            console_info("🔐 Attempting managed identity authentication for geocoding...", "AzureMaps")
            
            # Debug environment variables for managed identity
            msi_endpoint = os.environ.get("MSI_ENDPOINT")
            identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
            identity_header = os.environ.get("IDENTITY_HEADER")
            azure_client_id = os.environ.get("AZURE_CLIENT_ID")
            
            console_info(f"   • Environment check:", "AzureMaps")
            console_info(f"     - MSI_ENDPOINT: {'✅ Available' if msi_endpoint else '❌ Missing'}", "AzureMaps")
            console_info(f"     - IDENTITY_ENDPOINT: {'✅ Available' if identity_endpoint else '❌ Missing'}", "AzureMaps")
            console_info(f"     - IDENTITY_HEADER: {'✅ Available' if identity_header else '❌ Missing'}", "AzureMaps")
            console_info(f"     - AZURE_CLIENT_ID: {'✅ Available' if azure_client_id else '❌ Missing'}", "AzureMaps")
            
            if not (msi_endpoint or identity_endpoint):
                console_error("❌ Managed identity environment not detected!", "AzureMaps")
                console_error("💡 This appears to be running outside Azure Container App", "AzureMaps")
                console_error("💡 Deploy to Azure Container App to use managed identity", "AzureMaps")
                return None
            
            try:
                console_info("   🔄 Creating DefaultAzureCredential...", "AzureMaps")
                credential = DefaultAzureCredential()
                console_info("   ✅ DefaultAzureCredential created successfully", "AzureMaps")
                
                # Get token with detailed logging
                console_info("   🎫 Requesting Azure Maps access token...", "AzureMaps")
                token_scope = "https://atlas.microsoft.com/.default"
                console_info(f"   • Token scope: {token_scope}", "AzureMaps")
                
                token = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: credential.get_token(token_scope)
                )
                
                if token and token.token:
                    console_info(f"   ✅ Token acquired successfully!", "AzureMaps")
                    console_info(f"   • Token length: {len(token.token)} characters", "AzureMaps")
                    console_info(f"   • Token expires: {token.expires_on}", "AzureMaps")
                    console_info(f"   • Token starts with: {token.token[:30]}...", "AzureMaps")
                    
                    # Additional token validation
                    try:
                        import base64
                        import json as json_lib
                        parts = token.token.split('.')
                        if len(parts) >= 2:
                            # Decode payload to check audience
                            payload_data = parts[1]
                            payload_data += '=' * (4 - len(payload_data) % 4)
                            decoded_payload = base64.urlsafe_b64decode(payload_data).decode('utf-8')
                            payload_json = json_lib.loads(decoded_payload)
                            
                            audience = payload_json.get('aud', '')
                            console_info(f"   • Token audience: {audience}", "AzureMaps")
                            console_info(f"   • Token subject: {payload_json.get('sub', 'N/A')}", "AzureMaps")
                            console_info(f"   • Token issuer: {payload_json.get('iss', 'N/A')}", "AzureMaps")
                            
                            # Verify audience is correct
                            if "atlas.microsoft.com" in str(audience):
                                console_info(f"   ✅ Token audience is correct for Azure Maps", "AzureMaps")
                            else:
                                console_error(f"   ⚠️  Token audience may be incorrect!", "AzureMaps")
                                console_error(f"   Expected: https://atlas.microsoft.com", "AzureMaps")
                                console_error(f"   Actual: {audience}", "AzureMaps")
                    except Exception as decode_error:
                        console_info(f"   • Token decode error: {decode_error}", "AzureMaps")
                    
                    headers["Authorization"] = f"Bearer {token.token}"
                    
                    # Add required x-ms-client-id header for Azure Maps managed identity
                    if self.client_id:
                        headers["x-ms-client-id"] = self.client_id
                        console_info(f"   🆔 Added x-ms-client-id header: {self.client_id}", "AzureMaps")
                    else:
                        console_error("   ❌ Missing AZURE_MAPS_CLIENT_ID for managed identity authentication", "AzureMaps")
                    
                    console_info("   🔐 Authorization header configured", "AzureMaps")
                else:
                    console_error("   ❌ Token acquisition returned None or empty token", "AzureMaps")
                    return None
                
            except ClientAuthenticationError as auth_error:
                console_error(f"   ❌ Azure authentication failed: {auth_error}", "AzureMaps")
                console_error(f"   • Error type: {type(auth_error).__name__}", "AzureMaps")
                console_error("   💡 Managed identity configuration issues:", "AzureMaps")
                console_error("     - Check if system-assigned managed identity is enabled", "AzureMaps")
                console_error("     - Verify 'Azure Maps Data Reader' role is assigned", "AzureMaps")
                console_error("     - Ensure Container App was restarted after identity setup", "AzureMaps")
                console_error(f"     - Verify identity 5238e629-da2f-4bb0-aea5-14d45526c864 has correct permissions", "AzureMaps")
                return None
            except Exception as token_error:
                console_error(f"   ❌ Token acquisition failed: {token_error}", "AzureMaps")
                console_error(f"   • Error type: {type(token_error).__name__}", "AzureMaps")
                console_error("   💡 Troubleshooting steps:", "AzureMaps")
                console_error("     - Verify Azure Container App environment", "AzureMaps")
                console_error("     - Check network connectivity to Azure AD", "AzureMaps")
                console_error("     - Ensure azure-identity package is up to date", "AzureMaps")
                return None

        if not self.session:
            self.session = aiohttp.ClientSession()

        # Use the search/address/json endpoint which is more reliable for city/state geocoding
        url = f"{self.base_url}/search/address/json"
        
        console_info(f"🌐 Making Azure Maps API request:", "AzureMaps")
        console_info(f"   • URL: {url}", "AzureMaps")
        console_info(f"   • Query: {params['query']}", "AzureMaps")
        console_info(f"   • Auth method: {'Subscription Key' if self.subscription_key else 'Managed Identity (Bearer Token)'}", "AzureMaps")
        console_info(f"   • Headers: {list(headers.keys())}", "AzureMaps")
        console_info(f"   • Parameters: {list(params.keys())}", "AzureMaps")

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                console_info(f"📡 API Response received: HTTP {response.status}", "AzureMaps")
                
                if response.status == 200:
                    result = await response.json()
                    console_info(f"✅ Successfully geocoded {city}, {state}", "AzureMaps")
                    
                    # Check if we have results
                    results = result.get('results', [])
                    console_info(f"   • Results found: {len(results)}", "AzureMaps")
                    
                    if not results:
                        console_warning(f"No geocoding results found for {city}, {state}", "AzureMaps")
                        return None
                    
                    # Transform the result to match the expected format
                    best_match = results[0]
                    transformed_result = {
                        "features": [{
                            "geometry": {
                                "coordinates": [
                                    best_match.get('position', {}).get('lon', 0),
                                    best_match.get('position', {}).get('lat', 0)
                                ]
                            },
                            "properties": {
                                "address": {
                                    "formattedAddress": best_match.get('address', {}).get('freeformAddress', f"{city}, {state}"),
                                    "country": best_match.get('address', {}).get('country', 'United States'),
                                    "adminDivision": best_match.get('address', {}).get('adminDistricts', [{}])[0].get('name', state) if best_match.get('address', {}).get('adminDistricts') else state,
                                    "locality": best_match.get('address', {}).get('municipality', city)
                                },
                                "confidence": best_match.get('score', 1.0),
                                "matchCodes": [best_match.get('matchCode', {}).get('confidence', 'High')] if best_match.get('matchCode') else ['High']
                            }
                        }]
                    }
                    
                    console_debug(f"Transformed geocoding result: {transformed_result}", "AzureMaps")
                    return transformed_result
                    
                elif response.status == 404:
                    error_text = await response.text()
                    console_error(f"❌ Azure Maps API endpoint not found (404)", "AzureMaps")
                    console_error(f"   • Response: {error_text}", "AzureMaps")
                    console_error(f"   • URL used: {url}", "AzureMaps")
                    console_error("   💡 Check API endpoint URL is correct", "AzureMaps")
                    return None
                elif response.status == 401:
                    error_text = await response.text()
                    console_error(f"❌ Azure Maps authentication failed (401)", "AzureMaps")
                    console_error(f"   • Response: {error_text}", "AzureMaps")
                    console_error(f"   • Auth method: {'Subscription Key' if self.subscription_key else 'Managed Identity'}", "AzureMaps")
                    if not self.subscription_key:
                        console_error("   💡 Managed identity 401 troubleshooting:", "AzureMaps")
                        console_error("     - Token is being acquired but rejected by Azure Maps", "AzureMaps")
                        console_error("     - This usually means the managed identity lacks proper permissions", "AzureMaps")
                        console_error("     - Check Azure Portal → Azure Maps → Access Control (IAM)", "AzureMaps")
                        console_error(f"     - Verify identity 5238e629-da2f-4bb0-aea5-14d45526c864 has 'Azure Maps Data Reader' role", "AzureMaps")
                        console_error("     - Ensure role assignment scope is the Azure Maps account (not resource group)", "AzureMaps")
                        console_error("     - Try removing and re-adding the role assignment", "AzureMaps")
                        console_error("     - Wait 10-15 minutes after role changes for propagation", "AzureMaps")
                        
                        # Add token debugging for 401 errors
                        console_error("   🔍 Token debugging info:", "AzureMaps")
                        if 'Authorization' in headers:
                            auth_header = headers['Authorization']
                            if auth_header.startswith('Bearer '):
                                token_part = auth_header[7:]  # Remove 'Bearer ' prefix
                                console_error(f"     - Token length: {len(token_part)} characters", "AzureMaps")
                                console_error(f"     - Token starts: {token_part[:40]}...", "AzureMaps")
                                console_error(f"     - Token ends: ...{token_part[-20:]}", "AzureMaps")
                                
                                # Try to decode token header to see if it's valid JWT
                                try:
                                    import base64
                                    import json as json_lib
                                    # JWT tokens have 3 parts separated by dots
                                    parts = token_part.split('.')
                                    if len(parts) >= 2:
                                        # Decode header (first part)
                                        header_data = parts[0]
                                        # Add padding if needed
                                        header_data += '=' * (4 - len(header_data) % 4)
                                        decoded_header = base64.urlsafe_b64decode(header_data).decode('utf-8')
                                        header_json = json_lib.loads(decoded_header)
                                        console_error(f"     - Token type: {header_json.get('typ', 'unknown')}", "AzureMaps")
                                        console_error(f"     - Algorithm: {header_json.get('alg', 'unknown')}", "AzureMaps")
                                        
                                        # Decode payload (second part) for more info
                                        payload_data = parts[1]
                                        payload_data += '=' * (4 - len(payload_data) % 4)
                                        decoded_payload = base64.urlsafe_b64decode(payload_data).decode('utf-8')
                                        payload_json = json_lib.loads(decoded_payload)
                                        console_error(f"     - Audience: {payload_json.get('aud', 'unknown')}", "AzureMaps")
                                        console_error(f"     - Issuer: {payload_json.get('iss', 'unknown')}", "AzureMaps")
                                        console_error(f"     - Subject: {payload_json.get('sub', 'unknown')}", "AzureMaps")
                                        
                                        # Check if the audience is correct for Azure Maps
                                        expected_audience = "https://atlas.microsoft.com"
                                        actual_audience = payload_json.get('aud', '')
                                        if expected_audience not in str(actual_audience):
                                            console_error(f"     ⚠️  AUDIENCE MISMATCH!", "AzureMaps")
                                            console_error(f"     - Expected: {expected_audience}", "AzureMaps")
                                            console_error(f"     - Actual: {actual_audience}", "AzureMaps")
                                            console_error(f"     - This may be the cause of the 401 error", "AzureMaps")
                                        else:
                                            console_error(f"     ✅ Audience looks correct", "AzureMaps")
                                            
                                except Exception as decode_error:
                                    console_error(f"     - Token decode failed: {decode_error}", "AzureMaps")
                        
                        console_error("   🔧 Recommended actions:", "AzureMaps")
                        console_error("     1. Go to Azure Portal → Azure Maps → Access Control (IAM)", "AzureMaps")
                        console_error("     2. Click 'Role assignments' tab", "AzureMaps")
                        console_error("     3. Look for your Container App's managed identity", "AzureMaps")
                        console_error("     4. Verify it has 'Azure Maps Data Reader' role", "AzureMaps")
                        console_error("     5. Check the scope is the Azure Maps account (not subscription/RG)", "AzureMaps")
                        console_error("     6. If missing, add the role assignment", "AzureMaps")
                        console_error("     7. Restart your Container App after changes", "AzureMaps")
                    else:
                        console_error("   💡 Subscription key authentication issues:", "AzureMaps")
                        console_error("     - Check subscription key is valid", "AzureMaps")
                        console_error("     - Verify Azure Maps account is active", "AzureMaps")
                    return None
                elif response.status == 403:
                    error_text = await response.text()
                    console_error(f"❌ Azure Maps access forbidden (403)", "AzureMaps")
                    console_error(f"   • Response: {error_text}", "AzureMaps")
                    console_error(f"   • Auth method: {'Subscription Key' if self.subscription_key else 'Managed Identity'}", "AzureMaps")
                    if not self.subscription_key:
                        console_error("   💡 Managed identity permission issues:", "AzureMaps")
                        console_error("     - Check 'Azure Maps Data Reader' role is assigned", "AzureMaps")
                        console_error("     - Verify role assignment scope includes Azure Maps account", "AzureMaps")
                        console_error("     - Wait 5-10 minutes for role propagation", "AzureMaps")
                        console_error(f"     - Identity: 5238e629-da2f-4bb0-aea5-14d45526c864", "AzureMaps")
                    else:
                        console_error("   💡 Subscription permission issues:", "AzureMaps")
                        console_error("     - Check Azure Maps subscription status", "AzureMaps")
                        console_error("     - Verify quota and billing", "AzureMaps")
                    return None
                else:
                    error_text = await response.text()
                    console_error(f"❌ Unexpected response (HTTP {response.status})", "AzureMaps")
                    console_error(f"   • Response: {error_text}", "AzureMaps")
                    console_error(f"   • Request URL: {url}", "AzureMaps")
                    console_error(f"   • Request params: {params}", "AzureMaps")
                    return None
                    
        except Exception as e:
            console_error(f"❌ Exception during geocoding request:", "AzureMaps")
            console_error(f"   • Error: {str(e)}", "AzureMaps")
            console_error(f"   • Error type: {type(e).__name__}", "AzureMaps")
            console_error(f"   • City/State: {city}, {state}", "AzureMaps")
            console_error(f"   • Auth method: {'Subscription Key' if self.subscription_key else 'Managed Identity'}", "AzureMaps")
            import traceback
            console_error(f"   • Traceback: {traceback.format_exc()}", "AzureMaps")
            return None
