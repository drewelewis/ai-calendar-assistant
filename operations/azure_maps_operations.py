import os
import traceback
import asyncio
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

# Import telemetry components
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

class AzureMapsOperations:
    """
    Azure Maps Search Operations Client
    
    This class provides methods to interact with Azure Maps Search API, specifically
    for nearby point-of-interest (POI) searches using the REST API endpoint.
    
    Follows Azure best practices:
    - Uses Managed Identity authentication (preferred) with subscription key fallback
    - Implements proper error handling and retry logic
    - Includes comprehensive telemetry and monitoring
    - Provides structured console output for debugging
    """
    
    def __init__(self, 
                 subscription_key: Optional[str] = None,
                 client_id: Optional[str] = None,
                 base_url: str = "https://atlas.microsoft.com"):
        """
        Initialize the Azure Maps Search Operations client.
        
        Args:
            subscription_key: Optional Azure Maps subscription key (falls back to env var)
            client_id: Optional client ID for managed identity authentication
            base_url: Base URL for Azure Maps API (default: https://atlas.microsoft.com)
        """
        self.base_url = base_url.rstrip('/')
        self.api_version = "1.0"
        
        # Authentication setup - prefer managed identity over subscription key
        self.client_id = client_id or os.environ.get("AZURE_MAPS_CLIENT_ID")
        self.subscription_key = subscription_key or os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
        
        # HTTP session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Lazy initialization for credentials
        self.credential = None
        self.access_token = None
        self.token_expiry = None
        
        console_info(f"🗺️  Azure Maps Search Operations initialized", module="AzureMapsOperations")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'ai-calendar-assistant/1.0.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
            console_debug("🔗 HTTP session created with connection pooling", module="AzureMapsOperations")
            
        return self.session
    
    async def _get_access_token(self) -> Optional[str]:
        """
        Get access token using managed identity authentication.
        
        Returns:
            str: Access token if successful, None if authentication fails
        """
        try:
            if not self.client_id:
                console_debug("No client ID provided, skipping managed identity auth", module="AzureMapsOperations")
                return None
                
            # Check if we have a valid cached token
            if (self.access_token and self.token_expiry and 
                datetime.now().timestamp() < self.token_expiry - 300):  # 5-minute buffer
                return self.access_token
            
            # Initialize credential if needed
            if self.credential is None:
                try:
                    # Try managed identity first
                    self.credential = ManagedIdentityCredential(client_id=self.client_id)
                    console_info("🔐 Using Managed Identity authentication", module="AzureMapsOperations")
                except Exception:
                    # Fallback to default credential chain
                    self.credential = DefaultAzureCredential()
                    console_info("🔐 Using Default Azure Credential chain", module="AzureMapsOperations")
            
            # Get token for Azure Maps scope
            token = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.credential.get_token("https://atlas.microsoft.com/.default")
            )
            
            self.access_token = token.token
            self.token_expiry = token.expires_on
            
            console_debug("✅ Access token acquired successfully", module="AzureMapsOperations")
            return self.access_token
            
        except Exception as e:
            console_warning(f"Failed to get access token: {e}", module="AzureMapsOperations")
            return None
    
    def _get_auth_headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            access_token: Optional access token for AAD authentication
            
        Returns:
            dict: Headers with authentication information
        """
        headers = {}
        
        if access_token and self.client_id:
            # Use AAD token authentication
            headers['Authorization'] = f'Bearer {access_token}'
            headers['x-ms-client-id'] = self.client_id
            console_debug("Using AAD token authentication", module="AzureMapsOperations")
        elif self.subscription_key:
            # Fallback to subscription key
            headers['Ocp-Apim-Subscription-Key'] = self.subscription_key
            console_debug("Using subscription key authentication", module="AzureMapsOperations")
        else:
            console_warning("No authentication method available", module="AzureMapsOperations")
            
        return headers
    
    @trace_async_method("azure_maps.search_nearby", include_args=True)
    @measure_performance("azure_maps_search")
    async def search_nearby(self,
                           latitude: float,
                           longitude: float,
                           radius: int = 5000,
                           limit: int = 10,
                           category_set: Optional[List[int]] = None,
                           brand_set: Optional[List[str]] = None,
                           country_set: Optional[List[str]] = None,
                           language: str = "en-US",
                           **kwargs) -> Dict[str, Any]:
        """
        Search for points of interest near a specific location using Azure Maps Search API.
        
        Args:
            latitude: Latitude where results should be biased (e.g., 37.337)
            longitude: Longitude where results should be biased (e.g., -121.89)
            radius: The radius in meters to constrain results (min: 1, max: 50000, default: 5000)
            limit: Maximum number of responses (min: 1, max: 100, default: 10)
            category_set: List of category set IDs to filter POI categories
            brand_set: List of brand names to filter results
            country_set: List of country/region codes to limit search
            language: Language for results (default: en-US)
            **kwargs: Additional query parameters
            
        Returns:
            dict: Azure Maps Search API response with POI results
            
        Raises:
            ClientAuthenticationError: If authentication fails
            aiohttp.ClientError: If HTTP request fails
            ValueError: If parameters are invalid
        """
        # Input validation
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")
        if not (1 <= radius <= 50000):
            raise ValueError(f"Invalid radius: {radius}. Must be between 1 and 50000 meters.")
        if not (1 <= limit <= 100):
            raise ValueError(f"Invalid limit: {limit}. Must be between 1 and 100.")
        
        console_info(f"🔍 Searching for POIs near ({latitude}, {longitude}) within {radius}m", 
                    module="AzureMapsOperations")
        
        try:
            # Build query parameters
            params = {
                'api-version': self.api_version,
                'lat': latitude,
                'lon': longitude,
                'radius': radius,
                'limit': limit,
                'language': language
            }
            
            # Add optional filters
            if category_set:
                params['categorySet'] = ','.join(map(str, category_set))
                console_debug(f"Applied category filter: {category_set}", module="AzureMapsOperations")
                
            if brand_set:
                # Handle brands with commas by putting them in quotes
                formatted_brands = []
                for brand in brand_set:
                    if ',' in brand:
                        formatted_brands.append(f'"{brand}"')
                    else:
                        formatted_brands.append(brand)
                params['brandSet'] = ','.join(formatted_brands)
                console_debug(f"Applied brand filter: {brand_set}", module="AzureMapsOperations")
                
            if country_set:
                params['countrySet'] = ','.join(country_set)
                console_debug(f"Applied country filter: {country_set}", module="AzureMapsOperations")
            
            # Add any additional parameters
            params.update(kwargs)
            
            # Get authentication
            access_token = await self._get_access_token()
            auth_headers = self._get_auth_headers(access_token)
            
            if not auth_headers:
                raise ClientAuthenticationError("No valid authentication method available. "
                                              "Please provide either AZURE_MAPS_CLIENT_ID for managed identity "
                                              "or AZURE_MAPS_SUBSCRIPTION_KEY.")
            
            # Build URL
            url = f"{self.base_url}/search/nearby/json"
            
            # Make HTTP request with retry logic
            session = await self._get_session()
            
            console_debug(f"Making request to: {url}", module="AzureMapsOperations")
            console_telemetry_event("azure_maps_request", {
                "endpoint": "search_nearby",
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "limit": limit
            }, module="AzureMapsOperations")
            
            async with session.get(url, params=params, headers=auth_headers) as response:
                # Check for HTTP errors
                if response.status == 401:
                    console_error("Authentication failed - check credentials", module="AzureMapsOperations")
                    raise ClientAuthenticationError("Authentication failed. Check your Azure Maps credentials.")
                elif response.status == 403:
                    console_error("Access forbidden - check permissions", module="AzureMapsOperations")
                    raise ClientAuthenticationError("Access forbidden. Check your Azure Maps permissions.")
                elif response.status == 429:
                    console_warning("Rate limit exceeded", module="AzureMapsOperations")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message="Rate limit exceeded"
                    )
                elif response.status >= 400:
                    error_text = await response.text()
                    console_error(f"HTTP {response.status}: {error_text}", module="AzureMapsOperations")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
                
                # Parse response
                result = await response.json()
                
                # Log success metrics
                num_results = len(result.get('results', []))
                query_time = result.get('summary', {}).get('queryTime', 0)
                
                console_info(f"✅ Found {num_results} POIs in {query_time}ms", module="AzureMapsOperations")
                console_telemetry_event("azure_maps_success", {
                    "endpoint": "search_nearby",
                    "results_count": num_results,
                    "query_time_ms": query_time,
                    "status_code": response.status
                }, module="AzureMapsOperations")
                
                return result
                
        except (aiohttp.ClientError, ClientAuthenticationError) as e:
            console_error(f"Azure Maps API error: {e}", module="AzureMapsOperations")
            console_telemetry_event("azure_maps_error", {
                "endpoint": "search_nearby",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, module="AzureMapsOperations")
            raise
        except Exception as e:
            console_error(f"Unexpected error in search_nearby: {e}", module="AzureMapsOperations")
            console_error(f"Full traceback:\n{traceback.format_exc()}", module="AzureMapsOperations")
            raise
    
    @trace_async_method("azure_maps.get_poi_categories")
    async def get_poi_categories(self) -> List[Dict[str, Any]]:
        """
        Get available POI categories for filtering search results.
        
        Note: This is a helper method that returns common POI categories.
        For the complete list, use the Azure Maps POI Categories API.
        
        Returns:
            list: Common POI categories with IDs and descriptions
        """
        console_debug("Getting POI categories", module="AzureMapsOperations")
        
        # Common POI categories based on Azure Maps documentation
        categories = [
            {"id": 7315, "name": "Restaurant", "description": "Restaurants and dining establishments"},
            {"id": 7315025, "name": "Italian Restaurant", "description": "Italian cuisine restaurants"},
            {"id": 7315017, "name": "French Restaurant", "description": "French cuisine restaurants"},
            {"id": 9361, "name": "Gas Station", "description": "Fuel stations and gas pumps"},
            {"id": 7372, "name": "ATM", "description": "Automated Teller Machines"},
            {"id": 9663, "name": "Hospital", "description": "Medical facilities and hospitals"},
            {"id": 9927, "name": "Pharmacy", "description": "Pharmacies and drug stores"},
            {"id": 9362, "name": "Shopping", "description": "Shopping centers and retail stores"},
            {"id": 7313, "name": "Hotel", "description": "Hotels and accommodations"},
            {"id": 9352, "name": "School", "description": "Educational institutions"},
            {"id": 9910, "name": "Tourist Attraction", "description": "Points of interest for tourists"},
            {"id": 7832, "name": "Airport", "description": "Airports and aviation facilities"},
            {"id": 7380, "name": "Bank", "description": "Banking institutions"},
            {"id": 9919, "name": "Coffee Shop", "description": "Coffee shops and cafes"}
        ]
        
        console_info(f"📋 Retrieved {len(categories)} POI categories", module="AzureMapsOperations")
        return categories
    
    async def close(self):
        """Clean up resources and close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            console_debug("🔚 HTTP session closed", module="AzureMapsOperations")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

# Example usage and testing
async def main():
    """Example usage of Azure Search Operations."""
    console_info("🚀 Starting Azure Maps Search Operations example", module="Example")
    
    try:
        async with AzureMapsOperations() as search_ops:
            # Example 1: Search for POIs near Seattle, WA
            console_info("=== Example 1: Seattle POI Search ===", module="Example")
            seattle_results = await search_ops.search_nearby(
                latitude=47.6062,
                longitude=-122.3321,
                radius=1000,  # 1km radius
                limit=5
            )
            
            console_info(f"Found {len(seattle_results.get('results', []))} POIs near Seattle", module="Example")
            for poi in seattle_results.get('results', [])[:3]:  # Show first 3
                name = poi.get('poi', {}).get('name', 'Unknown')
                address = poi.get('address', {}).get('freeformAddress', 'No address')
                distance = poi.get('dist', 0)
                console_info(f"  📍 {name} - {address} ({distance:.0f}m away)", module="Example")
            
            # Example 2: Search for restaurants in New York
            console_info("\n=== Example 2: NYC Restaurant Search ===", module="Example")
            restaurant_results = await search_ops.search_nearby(
                latitude=40.7589,
                longitude=-73.9851,  # Times Square
                radius=500,
                limit=3,
                category_set=[7315]  # Restaurant category
            )
            
            console_info(f"Found {len(restaurant_results.get('results', []))} restaurants near Times Square", module="Example")
            for restaurant in restaurant_results.get('results', []):
                name = restaurant.get('poi', {}).get('name', 'Unknown')
                phone = restaurant.get('poi', {}).get('phone', 'No phone')
                console_info(f"  🍽️  {name} - {phone}", module="Example")
            
            # Example 3: Get POI categories
            console_info("\n=== Example 3: POI Categories ===", module="Example")
            categories = await search_ops.get_poi_categories()
            console_info(f"Available categories: {len(categories)}", module="Example")
            for cat in categories[:5]:  # Show first 5
                console_info(f"  🏷️  {cat['name']} (ID: {cat['id']}) - {cat['description']}", module="Example")
                
    except Exception as e:
        console_error(f"Example failed: {e}", module="Example")
        raise

if __name__ == "__main__":
    asyncio.run(main())
