from datetime import datetime
from typing import List, Optional, Annotated, Dict, Any
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

# Import telemetry components first
from telemetry.decorators import TelemetryContext
from telemetry.console_output import console_info, console_debug, console_telemetry_event, console_error, console_warning

# Import the Azure Maps Operations
try:
    from operations.azure_maps_operations import AzureMapsOperations
    console_info("✓ Using Azure Maps Search Operations", module="AzureMapsPlugin")
except Exception as e:
    console_error(f"⚠ Could not import AzureMapsOperations: {e}", module="AzureMapsPlugin")
    raise

try:
    from utils.teams_utilities import TeamsUtilities
    # Initialize TeamsUtilities for sending messages
    teams_utils = TeamsUtilities()
    TEAMS_UTILS_AVAILABLE = True
except ImportError as e:
    console_error(f"⚠ Teams utilities not available: {e}", module="AzureMapsPlugin")
    TEAMS_UTILS_AVAILABLE = False
    
    # Fallback TeamsUtilities that does nothing
    class MockTeamsUtilities:
        def send_friendly_notification(self, message, session_id=None, debug=False):
            if debug:
                session_info = f"[session: {session_id}] " if session_id else ""
                print(f"TEAMS: {session_info}{message}")
    
    teams_utils = MockTeamsUtilities()

class AzureMapsPlugin:
    """
    Azure Maps Search Plugin for Semantic Kernel
    
    This plugin provides location-based search capabilities using Azure Maps Search API.
    It enables AI assistants to find nearby points of interest, restaurants, hotels,
    gas stations, and other location-based services.
    
    Features:
    - Nearby POI search with configurable radius and filters
    - Category-based filtering (restaurants, hotels, gas stations, etc.)
    - Brand-specific searches (Starbucks, McDonald's, etc.)
    - Geographic region filtering
    - Comprehensive POI information including addresses, phone numbers, ratings
    """
    
    def __init__(self, debug=False, session_id=None):
        """
        Initialize the Azure Search Plugin.
        
        Args:
            debug: Enable debug logging for function calls
            session_id: Optional session identifier for tracking
        """
        self.debug = debug
        self.session_id = session_id or f"azure_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize the Azure Search Operations client
        self.search_ops = None
        
        console_info(f"🗺️ Azure Search Plugin initialized (session: {self.session_id})", 
                    module="AzureMapsPlugin")
        
        if self.debug:
            console_debug("Debug mode enabled for Azure Search Plugin", module="AzureMapsPlugin")
    
    async def _get_search_client(self) -> AzureMapsOperations:
        """Get or create the Azure Search Operations client."""
        if self.search_ops is None:
            self.search_ops = AzureMapsOperations()
        return self.search_ops
    
    def _log_function_call(self, function_name, **kwargs):
        """Log function calls if debug is enabled."""
        if self.debug:
            console_debug(f"🔍 Function called: {function_name}", module="AzureMapsPlugin")
            for key, value in kwargs.items():
                if key not in ['session_id']:  # Don't log sensitive info
                    console_debug(f"  {key}: {value}", module="AzureMapsPlugin")
            
            console_telemetry_event("azure_search_function_call", {
                "function": function_name,
                "session_id": self.session_id,
                "args_count": len(kwargs)
            }, module="AzureMapsPlugin")
    
    def _send_friendly_notification(self, message: str):
        """Send a friendly notification to the user via Teams about what we're working on."""
        teams_utils.send_friendly_notification(message, self.session_id, self.debug)
    
    async def _cleanup(self):
        """Clean up resources when done."""
        if self.search_ops:
            await self.search_ops.close()
            self.search_ops = None
    
    @kernel_function(
        description="""
        Search for nearby points of interest (POIs) around a specific location using Azure Maps.
        
        USE THIS WHEN:
        - User asks to "find places near", "what's around", or "search nearby"
        - Need to locate businesses, services, or amenities near a specific location
        - User provides coordinates or asks about a specific area
        - Looking for things like restaurants, gas stations, hotels, shops
        
        CAPABILITIES:
        - Searches within configurable radius (up to 50km)
        - Returns detailed POI information including names, addresses, phone numbers
        - Provides distance calculations from search center
        - Supports worldwide searches with local language preferences
        
        COMMON USE CASES:
        - "What restaurants are near downtown Seattle?"
        - "Find gas stations within 5 miles of Times Square"
        - "Show me hotels near the airport"
        - "What's around latitude 47.6062, longitude -122.3321?"
        - "Find coffee shops in a 1km radius from my location"
        
        LOCATION EXAMPLES:
        - Seattle, WA: latitude=47.6062, longitude=-122.3321
        - Times Square, NYC: latitude=40.7589, longitude=-73.9851
        - Los Angeles, CA: latitude=34.0522, longitude=-118.2437
        - London, UK: latitude=51.5074, longitude=-0.1278
        
        SEARCH RESULTS INCLUDE:
        - Business name and category
        - Full address and location coordinates
        - Phone number and website (if available)
        - Distance from search center
        - Operating hours and additional details
        """
    )
    async def search_nearby_locations(self,
                                     latitude: Annotated[float, "Latitude coordinate (-90 to 90)"],
                                     longitude: Annotated[float, "Longitude coordinate (-180 to 180)"],
                                     radius: Annotated[int, "Search radius in meters (default: 5000, max: 50000)"] = 5000,
                                     limit: Annotated[int, "Maximum number of results (default: 10, max: 100)"] = 10,
                                     language: Annotated[str, "Response language code (default: en-US)"] = "en-US") -> str:
        """
        Search for nearby points of interest around a specific location.
        
        Returns formatted results with POI details including names, addresses, and distances.
        """
        self._log_function_call("search_nearby_locations", 
                               latitude=latitude, longitude=longitude, 
                               radius=radius, limit=limit, language=language)
        
        try:
            # Notify user we're searching
            self._send_friendly_notification(f"🔍 Searching for places near coordinates {latitude}, {longitude}...")
            
            search_client = await self._get_search_client()
            
            # Perform the search
            results = await search_client.search_nearby(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                limit=limit,
                language=language
            )
            
            # Format results for AI consumption
            pois = results.get('results', [])
            if not pois:
                return f"No points of interest found within {radius} meters of coordinates ({latitude}, {longitude})."
            
            # Build formatted response
            response_lines = [
                f"Found {len(pois)} points of interest near ({latitude}, {longitude}) within {radius}m radius:\n"
            ]
            
            for i, poi in enumerate(pois, 1):
                poi_info = poi.get('poi', {})
                address_info = poi.get('address', {})
                position = poi.get('position', {})
                distance = poi.get('dist', 0)
                
                name = poi_info.get('name', 'Unknown Business')
                phone = poi_info.get('phone', 'No phone available')
                address = address_info.get('freeformAddress', 'No address available')
                website = poi_info.get('url', 'No website available')
                
                # Extract category information
                categories = poi_info.get('categorySet', [])
                category_names = []
                if categories:
                    for cat in categories:
                        if isinstance(cat, dict) and 'id' in cat:
                            # Map common category IDs to names
                            category_map = {
                                7315: "Restaurant", 9361: "Gas Station", 7313: "Hotel",
                                9663: "Hospital", 9927: "Pharmacy", 9362: "Shopping",
                                7372: "ATM", 9352: "School", 7832: "Airport", 7380: "Bank",
                                9919: "Coffee Shop", 9910: "Tourist Attraction"
                            }
                            cat_name = category_map.get(cat['id'], f"Category {cat['id']}")
                            category_names.append(cat_name)
                
                category_str = " | ".join(category_names) if category_names else "General Business"
                
                response_lines.append(
                    f"{i}. **{name}** ({category_str})\n"
                    f"   📍 Address: {address}\n"
                    f"   📞 Phone: {phone}\n"
                    f"   🌐 Website: {website}\n"
                    f"   📏 Distance: {distance:.0f} meters away\n"
                    f"   🗺️  Coordinates: {position.get('lat', 'N/A')}, {position.get('lon', 'N/A')}\n"
                )
            
            # Add summary information
            query_info = results.get('summary', {})
            query_time = query_info.get('queryTime', 0)
            total_results = query_info.get('totalResults', len(pois))
            
            response_lines.append(
                f"\n📊 Search completed in {query_time}ms. "
                f"Showing {len(pois)} of {total_results} total results available."
            )
            
            return "\n".join(response_lines)
            
        except Exception as e:
            error_msg = f"Error searching for nearby locations: {str(e)}"
            console_error(error_msg, module="AzureMapsPlugin")
            return f"Sorry, I encountered an error while searching for nearby locations: {str(e)}"
    
    @kernel_function(
        description="""
        Search for specific types of businesses or services near a location using category filtering.
        
        USE THIS WHEN:
        - User asks for specific types of places (restaurants, gas stations, hotels, etc.)
        - Need to filter search results to particular business categories
        - User wants focused results for a specific service type
        - Looking for multiple related business types
        
        CAPABILITIES:
        - Filters POI results by specific business categories
        - Supports multiple category types in a single search
        - Returns detailed information for matching businesses only
        - More focused results than general nearby search
        
        COMMON USE CASES:
        - "Find restaurants near downtown"
        - "Show me gas stations and car repair shops nearby"
        - "Where are the hospitals and pharmacies?"
        - "Find hotels and tourist attractions in the area"
        - "Locate all the banks and ATMs around here"
        
        SUPPORTED CATEGORIES:
        - restaurant: Restaurants and dining establishments
        - gas_station: Fuel stations and gas pumps
        - hotel: Hotels and accommodations
        - hospital: Medical facilities and hospitals
        - pharmacy: Pharmacies and drug stores
        - shopping: Shopping centers and retail stores
        - atm: Automated Teller Machines
        - school: Educational institutions
        - airport: Airports and aviation facilities
        - bank: Banking institutions
        - coffee_shop: Coffee shops and cafes
        - tourist_attraction: Points of interest for tourists
        
        FILTERING ADVANTAGES:
        - Reduces noise in search results
        - Faster response times with focused queries
        - More relevant results for specific needs
        - Better for targeted business discovery
        """
    )
    async def search_by_category(self,
                                latitude: Annotated[float, "Latitude coordinate (-90 to 90)"],
                                longitude: Annotated[float, "Longitude coordinate (-180 to 180)"],
                                categories: Annotated[str, "Comma-separated category types (restaurant,gas_station,hotel,etc.)"],
                                radius: Annotated[int, "Search radius in meters (default: 5000, max: 50000)"] = 5000,
                                limit: Annotated[int, "Maximum number of results (default: 10, max: 100)"] = 10,
                                language: Annotated[str, "Response language code (default: en-US)"] = "en-US") -> str:
        """
        Search for specific categories of businesses near a location.
        
        Returns filtered results containing only the specified business types.
        """
        self._log_function_call("search_by_category", 
                               latitude=latitude, longitude=longitude,
                               categories=categories, radius=radius, limit=limit)
        
        try:
            # Notify user we're searching by category
            self._send_friendly_notification(f"🏷️ Searching for {categories} near your location...")
            
            # Map category names to Azure Maps category IDs
            category_mapping = {
                'restaurant': 7315,
                'italian_restaurant': 7315025,
                'french_restaurant': 7315017,
                'gas_station': 9361,
                'hotel': 7313,
                'hospital': 9663,
                'pharmacy': 9927,
                'shopping': 9362,
                'atm': 7372,
                'school': 9352,
                'airport': 7832,
                'bank': 7380,
                'coffee_shop': 9919,
                'tourist_attraction': 9910
            }
            
            # Parse and validate categories
            category_list = [cat.strip().lower() for cat in categories.split(',')]
            category_ids = []
            invalid_categories = []
            
            for category in category_list:
                if category in category_mapping:
                    category_ids.append(category_mapping[category])
                else:
                    invalid_categories.append(category)
            
            if not category_ids:
                available_cats = ", ".join(sorted(category_mapping.keys()))
                return (f"No valid categories specified. Please use one or more of: {available_cats}")
            
            if invalid_categories:
                console_warning(f"Invalid categories ignored: {invalid_categories}", module="AzureMapsPlugin")
            
            search_client = await self._get_search_client()
            
            # Perform the categorized search
            results = await search_client.search_nearby(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                limit=limit,
                category_set=category_ids,
                language=language
            )
            
            # Format results
            pois = results.get('results', [])
            if not pois:
                category_names = [cat.replace('_', ' ').title() for cat in category_list if cat in category_mapping]
                return (f"No {', '.join(category_names)} found within {radius} meters of "
                       f"coordinates ({latitude}, {longitude}).")
            
            # Build response
            response_lines = [
                f"Found {len(pois)} businesses matching your category filter near ({latitude}, {longitude}):\n"
            ]
            
            for i, poi in enumerate(pois, 1):
                poi_info = poi.get('poi', {})
                address_info = poi.get('address', {})
                distance = poi.get('dist', 0)
                
                name = poi_info.get('name', 'Unknown Business')
                phone = poi_info.get('phone', 'No phone available')
                address = address_info.get('freeformAddress', 'No address available')
                website = poi_info.get('url', 'No website available')
                
                # Get specific category for this POI
                poi_categories = poi_info.get('categorySet', [])
                poi_category = "Business"
                if poi_categories and isinstance(poi_categories[0], dict):
                    cat_id = poi_categories[0].get('id')
                    reverse_mapping = {v: k.replace('_', ' ').title() for k, v in category_mapping.items()}
                    poi_category = reverse_mapping.get(cat_id, "Business")
                
                response_lines.append(
                    f"{i}. **{name}** ({poi_category})\n"
                    f"   📍 {address}\n"
                    f"   📞 {phone}\n"
                    f"   🌐 {website}\n"
                    f"   📏 {distance:.0f} meters away\n"
                )
            
            # Add search summary
            query_info = results.get('summary', {})
            query_time = query_info.get('queryTime', 0)
            
            response_lines.append(
                f"\n📊 Category search completed in {query_time}ms. "
                f"Filtered for: {', '.join([cat.replace('_', ' ').title() for cat in category_list if cat in category_mapping])}"
            )
            
            return "\n".join(response_lines)
            
        except Exception as e:
            error_msg = f"Error searching by category: {str(e)}"
            console_error(error_msg, module="AzureMapsPlugin")
            return f"Sorry, I encountered an error while searching by category: {str(e)}"
    
    @kernel_function(
        description="""
        Search for specific brands or franchise locations near a coordinate.
        
        USE THIS WHEN:
        - User asks for specific brand names or franchises
        - Looking for particular restaurant chains, retail stores, or services
        - User mentions brand names like "Starbucks", "McDonald's", "Walmart"
        - Need to find familiar brands in unfamiliar locations
        
        CAPABILITIES:
        - Filters search results to specific brand names
        - Supports multiple brands in a single search
        - Handles complex brand names with punctuation
        - Returns brand-specific location information
        
        COMMON USE CASES:
        - "Find the nearest Starbucks"
        - "Where's the closest McDonald's and Burger King?"
        - "Show me Walmart and Target stores nearby"
        - "Find Marriott or Hilton hotels in the area"
        - "Locate CVS and Walgreens pharmacies"
        
        BRAND EXAMPLES:
        - Restaurants: McDonald's, Burger King, KFC, Pizza Hut, Domino's, Starbucks, Dunkin'
        - Hotels: Marriott, Hilton, Holiday Inn, Best Western, Hampton Inn
        - Retail: Walmart, Target, Costco, Home Depot, Lowe's
        - Gas Stations: Shell, Exxon, BP, Chevron, Texaco
        - Pharmacies: CVS, Walgreens, Rite Aid
        
        BRAND MATCHING:
        - Searches are case-insensitive
        - Handles brands with apostrophes and special characters
        - Matches official brand names and common variations
        """
    )
    async def search_by_brand(self,
                             latitude: Annotated[float, "Latitude coordinate (-90 to 90)"],
                             longitude: Annotated[float, "Longitude coordinate (-180 to 180)"],
                             brands: Annotated[str, "Comma-separated brand names (Starbucks,McDonald's,etc.)"],
                             radius: Annotated[int, "Search radius in meters (default: 5000, max: 50000)"] = 5000,
                             limit: Annotated[int, "Maximum number of results (default: 10, max: 100)"] = 10,
                             language: Annotated[str, "Response language code (default: en-US)"] = "en-US") -> str:
        """
        Search for specific brand locations near a coordinate.
        
        Returns results filtered to show only the specified brand locations.
        """
        self._log_function_call("search_by_brand", 
                               latitude=latitude, longitude=longitude,
                               brands=brands, radius=radius, limit=limit)
        
        try:
            # Notify user we're searching by brand
            self._send_friendly_notification(f"🏪 Searching for {brands} locations near you...")
            
            # Parse brand list
            brand_list = [brand.strip() for brand in brands.split(',') if brand.strip()]
            
            if not brand_list:
                return "No brands specified. Please provide one or more brand names separated by commas."
            
            search_client = await self._get_search_client()
            
            # Perform the brand search
            results = await search_client.search_nearby(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                limit=limit,
                brand_set=brand_list,
                language=language
            )
            
            # Format results
            pois = results.get('results', [])
            if not pois:
                brand_names = ', '.join(brand_list)
                return (f"No {brand_names} locations found within {radius} meters of "
                       f"coordinates ({latitude}, {longitude}).")
            
            # Build response
            response_lines = [
                f"Found {len(pois)} brand locations matching your search near ({latitude}, {longitude}):\n"
            ]
            
            for i, poi in enumerate(pois, 1):
                poi_info = poi.get('poi', {})
                address_info = poi.get('address', {})
                distance = poi.get('dist', 0)
                
                name = poi_info.get('name', 'Unknown Location')
                phone = poi_info.get('phone', 'No phone available')
                address = address_info.get('freeformAddress', 'No address available')
                website = poi_info.get('url', 'No website available')
                
                # Get brand information if available
                brands_info = poi_info.get('brands', [])
                brand_name = "Unknown Brand"
                if brands_info and isinstance(brands_info[0], dict):
                    brand_name = brands_info[0].get('name', brand_name)
                
                response_lines.append(
                    f"{i}. **{name}** ({brand_name})\n"
                    f"   📍 {address}\n"
                    f"   📞 {phone}\n"
                    f"   🌐 {website}\n"
                    f"   📏 {distance:.0f} meters away\n"
                )
            
            # Add search summary
            query_info = results.get('summary', {})
            query_time = query_info.get('queryTime', 0)
            
            response_lines.append(
                f"\n📊 Brand search completed in {query_time}ms. "
                f"Searched for: {', '.join(brand_list)}"
            )
            
            return "\n".join(response_lines)
            
        except Exception as e:
            error_msg = f"Error searching by brand: {str(e)}"
            console_error(error_msg, module="AzureMapsPlugin")
            return f"Sorry, I encountered an error while searching by brand: {str(e)}"
    
    @kernel_function(
        description="""
        Get a comprehensive list of available point-of-interest categories for filtering searches.
        
        USE THIS WHEN:
        - User asks "what categories are available?" or "what types of places can you find?"
        - Need to show available filter options before performing searches
        - User is unsure what category names to use for filtering
        - Providing guidance on search capabilities
        
        PROVIDES:
        - Complete list of supported POI categories
        - Category names that can be used in search_by_category function
        - Category descriptions to help users understand options
        - Category IDs for technical reference
        
        COMMON USE CASES:
        - "What types of businesses can you search for?"
        - "Show me all available categories"
        - "What search filters are available?"
        - "List the POI categories I can use"
        - Help users discover search options
        
        CATEGORY INFORMATION:
        - Each category includes name, description, and ID
        - Categories cover major business types and services
        - Includes specialized categories like EV charging stations
        - Organized for easy browsing and selection
        
        HELPFUL FOR:
        - Discovering search capabilities
        - Understanding available filter options
        - Planning targeted searches
        - Learning about POI classification system
        """
    )
    async def get_available_categories(self) -> str:
        """
        Get a list of all available POI categories for search filtering.
        
        Returns comprehensive category information to help users understand search options.
        """
        self._log_function_call("get_available_categories")
        
        try:
            # Notify user we're fetching categories
            self._send_friendly_notification("📋 Getting available search categories for you...")
            
            search_client = await self._get_search_client()
            categories = await search_client.get_poi_categories()
            
            # Build formatted response
            response_lines = [
                "🏷️ Available Point-of-Interest Categories for Search Filtering:\n",
                "Use these category names with the search_by_category function:\n"
            ]
            
            # Group categories by type for better organization
            service_categories = []
            food_categories = []
            accommodation_categories = []
            transport_categories = []
            other_categories = []
            
            for cat in categories:
                cat_name = cat['name'].lower()
                if any(word in cat_name for word in ['restaurant', 'coffee', 'food']):
                    food_categories.append(cat)
                elif any(word in cat_name for word in ['hotel', 'accommodation']):
                    accommodation_categories.append(cat)
                elif any(word in cat_name for word in ['gas', 'airport', 'station']):
                    transport_categories.append(cat)
                elif any(word in cat_name for word in ['hospital', 'pharmacy', 'atm', 'bank']):
                    service_categories.append(cat)
                else:
                    other_categories.append(cat)
            
            # Add categorized sections
            if food_categories:
                response_lines.append("🍽️ **Food & Dining:**")
                for cat in food_categories:
                    response_lines.append(f"   • **{cat['name']}** (ID: {cat['id']}) - {cat['description']}")
                response_lines.append("")
            
            if accommodation_categories:
                response_lines.append("🏨 **Accommodation:**")
                for cat in accommodation_categories:
                    response_lines.append(f"   • **{cat['name']}** (ID: {cat['id']}) - {cat['description']}")
                response_lines.append("")
            
            if transport_categories:
                response_lines.append("🚗 **Transportation:**")
                for cat in transport_categories:
                    response_lines.append(f"   • **{cat['name']}** (ID: {cat['id']}) - {cat['description']}")
                response_lines.append("")
            
            if service_categories:
                response_lines.append("🏥 **Services:**")
                for cat in service_categories:
                    response_lines.append(f"   • **{cat['name']}** (ID: {cat['id']}) - {cat['description']}")
                response_lines.append("")
            
            if other_categories:
                response_lines.append("🏢 **Other Categories:**")
                for cat in other_categories:
                    response_lines.append(f"   • **{cat['name']}** (ID: {cat['id']}) - {cat['description']}")
                response_lines.append("")
            
            # Add usage instructions
            response_lines.extend([
                "📝 **Usage Instructions:**",
                "• Use category names (converted to lowercase with underscores) in search_by_category",
                "• Example: 'Restaurant' becomes 'restaurant', 'Gas Station' becomes 'gas_station'",
                "• You can combine multiple categories separated by commas",
                "• Categories help filter search results to specific business types",
                "",
                f"📊 Total Categories Available: {len(categories)}"
            ])
            
            return "\n".join(response_lines)
            
        except Exception as e:
            error_msg = f"Error getting available categories: {str(e)}"
            console_error(error_msg, module="AzureMapsPlugin")
            return f"Sorry, I encountered an error while getting available categories: {str(e)}"
    
    @kernel_function(
        description="""
        Search for places within a specific country or geographic region.
        
        USE THIS WHEN:
        - User specifies a particular country or region for the search
        - Need to limit search results to specific geographic boundaries
        - User is traveling and wants to find places only in certain countries
        - Cross-border searches where you want to include/exclude specific regions
        
        CAPABILITIES:
        - Filters search results by country/region codes
        - Supports multiple countries in a single search
        - Uses standard ISO country codes for accurate filtering
        - Useful for international travel and border area searches
        
        COMMON USE CASES:
        - "Find restaurants in France only"
        - "Show me hotels in US and Canada"
        - "Search for gas stations but only in Mexico"
        - "Find hospitals within EU countries"
        - Border area searches with specific country preferences
        
        SUPPORTED COUNTRY CODES:
        - US: United States
        - CA: Canada  
        - MX: Mexico
        - GB: United Kingdom
        - FR: France
        - DE: Germany
        - IT: Italy
        - ES: Spain
        - JP: Japan
        - AU: Australia
        - And many more ISO 3166-1 alpha-2 codes
        
        GEOGRAPHIC FILTERING:
        - Results will only include POIs within specified countries
        - Useful for avoiding cross-border results
        - Helps with travel planning and regional searches
        - Ensures regulatory and preference compliance
        """
    )
    async def search_by_region(self,
                              latitude: Annotated[float, "Latitude coordinate (-90 to 90)"],
                              longitude: Annotated[float, "Longitude coordinate (-180 to 180)"],
                              countries: Annotated[str, "Comma-separated country codes (US,CA,MX,etc.)"],
                              radius: Annotated[int, "Search radius in meters (default: 10000, max: 50000)"] = 10000,
                              limit: Annotated[int, "Maximum number of results (default: 10, max: 100)"] = 10,
                              language: Annotated[str, "Response language code (default: en-US)"] = "en-US") -> str:
        """
        Search for places limited to specific countries or regions.
        
        Returns results filtered to only include POIs within the specified countries.
        """
        self._log_function_call("search_by_region", 
                               latitude=latitude, longitude=longitude,
                               countries=countries, radius=radius, limit=limit)
        
        try:
            # Notify user we're searching by region
            self._send_friendly_notification(f"🌍 Searching for places in {countries} region...")
            
            # Parse and validate country codes
            country_list = [country.strip().upper() for country in countries.split(',') if country.strip()]
            
            if not country_list:
                return "No countries specified. Please provide one or more ISO country codes separated by commas (e.g., US,CA,MX)."
            
            # Validate country codes (basic check for 2-letter format)
            invalid_codes = [code for code in country_list if len(code) != 2]
            if invalid_codes:
                return f"Invalid country codes: {', '.join(invalid_codes)}. Please use 2-letter ISO codes (e.g., US, CA, GB)."
            
            search_client = await self._get_search_client()
            
            # Perform the regional search
            results = await search_client.search_nearby(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                limit=limit,
                country_set=country_list,
                language=language
            )
            
            # Format results
            pois = results.get('results', [])
            if not pois:
                country_names = ', '.join(country_list)
                return (f"No points of interest found in {country_names} within {radius} meters of "
                       f"coordinates ({latitude}, {longitude}).")
            
            # Build response
            response_lines = [
                f"Found {len(pois)} places in {', '.join(country_list)} near ({latitude}, {longitude}):\n"
            ]
            
            for i, poi in enumerate(pois, 1):
                poi_info = poi.get('poi', {})
                address_info = poi.get('address', {})
                distance = poi.get('dist', 0)
                
                name = poi_info.get('name', 'Unknown Location')
                phone = poi_info.get('phone', 'No phone available')
                address = address_info.get('freeformAddress', 'No address available')
                country_code = address_info.get('countryCode', 'Unknown')
                country_name = address_info.get('country', 'Unknown Country')
                
                # Get category information
                categories = poi_info.get('categorySet', [])
                category_name = "Business"
                if categories and isinstance(categories[0], dict):
                    cat_id = categories[0].get('id')
                    category_mapping = {
                        7315: "Restaurant", 9361: "Gas Station", 7313: "Hotel",
                        9663: "Hospital", 9927: "Pharmacy", 9362: "Shopping",
                        7372: "ATM", 9352: "School", 7832: "Airport", 7380: "Bank",
                        9919: "Coffee Shop", 9910: "Tourist Attraction"
                    }
                    category_name = category_mapping.get(cat_id, "Business")
                
                response_lines.append(
                    f"{i}. **{name}** ({category_name})\n"
                    f"   🌍 Country: {country_name} ({country_code})\n"
                    f"   📍 Address: {address}\n"
                    f"   📞 Phone: {phone}\n"
                    f"   📏 Distance: {distance:.0f} meters away\n"
                )
            
            # Add search summary
            query_info = results.get('summary', {})
            query_time = query_info.get('queryTime', 0)
            total_results = query_info.get('totalResults', len(pois))
            
            response_lines.append(
                f"\n📊 Regional search completed in {query_time}ms. "
                f"Searched in: {', '.join(country_list)}. "
                f"Showing {len(pois)} of {total_results} total results."
            )
            
            return "\n".join(response_lines)
            
        except Exception as e:
            error_msg = f"Error searching by region: {str(e)}"
            console_error(error_msg, module="AzureMapsPlugin")
            return f"Sorry, I encountered an error while searching by region: {str(e)}"
    
    @kernel_function(
        description="""
        Get geographical coordinates (latitude and longitude) for a city and state using Azure Maps geocoding.
        
        USE THIS WHEN:
        - User provides a city and state and needs coordinates
        - Converting location names to lat/lng for other location services
        - User asks "where is [city], [state]?" or "what are the coordinates of [city]?"
        - Need to find the exact location of a place for mapping or distance calculations
        
        CAPABILITIES:
        - Converts city/state combinations to precise coordinates
        - Returns detailed location information including formatted addresses
        - Supports US cities and states with high accuracy
        - Provides additional location metadata when available
        
        COMMON USE CASES:
        - "What are the coordinates of Seattle, WA?"
        - "Where exactly is Austin, Texas located?"
        - "Get the lat/lng for Portland, Oregon"
        - "Find the location of Miami, Florida"
        
        EXAMPLES:
        - Input: city="Seattle", state="WA" → Returns coordinates and location details
        - Input: city="Austin", state="Texas" → Returns coordinates and location details
        - Input: city="Portland", state="OR" → Returns coordinates and location details
        
        RESPONSE INCLUDES:
        - Latitude and longitude coordinates
        - Formatted address
        - Administrative region details
        - Bounding box information
        - Match confidence score
        """
    )
    async def geolocate_city_state(self,
                                   city: Annotated[str, "City name (e.g., 'Seattle', 'Austin', 'Portland')"],
                                   state: Annotated[str, "State name or abbreviation (e.g., 'WA', 'Washington', 'TX', 'Texas')"]) -> str:
        """
        Get geographical coordinates and location details for a city and state.
        
        Returns formatted location information including coordinates and address details.
        """
        self._log_function_call("geolocate_city_state", city=city, state=state)
        
        try:
            search_client = await self._get_search_client()
            
            # Notify user we're looking up the location
            self._send_friendly_notification(f"🗺️ Looking up coordinates for {city}, {state}...")
            
            # Perform the geocoding search
            result = await search_client.geolocate_city_state(city, state)
            
            if not result or 'features' not in result:
                return f"Could not find location information for {city}, {state}. Please check the spelling and try again."
            
            features = result.get('features', [])
            if not features:
                return f"No location found for {city}, {state}. Please verify the city and state names."
            
            # Get the best match (first result)
            best_match = features[0]
            geometry = best_match.get('geometry', {})
            properties = best_match.get('properties', {})
            
            # Extract coordinates
            coordinates = geometry.get('coordinates', [])
            if len(coordinates) >= 2:
                longitude, latitude = coordinates[0], coordinates[1]  # GeoJSON format: [lng, lat]
            else:
                return f"Invalid coordinate data received for {city}, {state}."
            
            # Extract location details
            address = properties.get('address', {})
            formatted_address = address.get('formattedAddress', f"{city}, {state}")
            country = address.get('country', 'Unknown')
            admin_division = address.get('adminDivision', 'Unknown')
            locality = address.get('locality', city)
            
            # Get confidence information
            confidence = properties.get('confidence', 'Unknown')
            match_type = properties.get('matchCodes', [])
            
            # Build formatted response
            response_lines = [
                f"📍 Location found for {city}, {state}:",
                f"",
                f"🎯 Coordinates: {latitude:.6f}, {longitude:.6f}",
                f"📮 Formatted Address: {formatted_address}",
                f"🌍 Country: {country}",
                f"🏛️ Administrative Division: {admin_division}",
                f"🏙️ Locality: {locality}",
                f"✅ Match Confidence: {confidence}",
            ]
            
            if match_type:
                response_lines.append(f"🔍 Match Type: {', '.join(match_type)}")
            
            response_lines.extend([
                f"",
                f"💡 Use these coordinates ({latitude:.6f}, {longitude:.6f}) for:",
                f"   • Finding nearby places and services",
                f"   • Distance calculations",
                f"   • Map integration and directions"
            ])
            
            # Log successful geocoding
            console_telemetry_event("azure_maps_geocode_success", {
                "city": city,
                "state": state,
                "latitude": latitude,
                "longitude": longitude,
                "confidence": confidence,
                "session_id": self.session_id
            }, module="AzureMapsPlugin")
            
            return "\n".join(response_lines)
            
        except Exception as e:
            error_msg = f"Error geocoding {city}, {state}: {str(e)}"
            console_error(error_msg, module="AzureMapsPlugin")
            
            # Log failed geocoding
            console_telemetry_event("azure_maps_geocode_error", {
                "city": city,
                "state": state,
                "error": str(e),
                "session_id": self.session_id
            }, module="AzureMapsPlugin")
            
            return f"Sorry, I encountered an error while looking up coordinates for {city}, {state}: {str(e)}"
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()

