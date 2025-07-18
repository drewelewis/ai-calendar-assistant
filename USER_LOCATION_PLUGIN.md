# User Location Plugin Documentation

## Overview

The User Location Plugin extends the Graph Plugin with location-based functionality, allowing you to retrieve geographical information (city, state, zipcode) for users from their Microsoft 365 profiles.

## New Function Added: `get_user_location`

### Function Signature
```python
async def get_user_location(self, user_id: str) -> dict
```

### Description
Retrieves location details (city, state, and zipcode) for a specific user from their Microsoft 365 profile.

### Parameters
- **user_id** (str): The unique user ID (GUID) of the user whose location details you want to retrieve

### Returns
- **dict**: A dictionary containing location information with the following keys:
  - `city`: City where the user is located (str or None)
  - `state`: State/province information (str or None) 
  - `zipcode`: Postal/zip code (str or None)

### Example Usage

#### Basic Usage
```python
from plugins.graph_plugin import GraphPlugin

# Initialize the plugin
graph_plugin = GraphPlugin(debug=True, session_id="my-session")

# Get user location
user_id = "12345678-1234-1234-1234-123456789012"
location = await graph_plugin.get_user_location(user_id)

if location:
    print(f"City: {location.get('city', 'Not specified')}")
    print(f"State: {location.get('state', 'Not specified')}")
    print(f"Zipcode: {location.get('zipcode', 'Not specified')}")
else:
    print("No location information found")
```

#### Integration with User Search
```python
# First find users, then get their locations
users = await graph_plugin.user_search("department eq 'Engineering'")

for user in users:
    location = await graph_plugin.get_user_location(user.id)
    if location and location.get('city'):
        print(f"{user.display_name} is located in {location['city']}")
```

#### Meeting Planning Scenario
```python
async def plan_regional_meeting(attendee_emails):
    """Find common location for meeting attendees."""
    locations = {}
    
    for email in attendee_emails:
        # First find user by email
        users = await graph_plugin.user_search(f"mail eq '{email}'")
        if users:
            user = users[0]
            location = await graph_plugin.get_user_location(user.id)
            if location:
                city = location.get('city')
                if city:
                    locations[email] = city
    
    # Analyze locations for meeting planning
    cities = list(locations.values())
    most_common_city = max(set(cities), key=cities.count) if cities else None
    
    return {
        'attendee_locations': locations,
        'suggested_city': most_common_city,
        'attendee_count_by_city': {city: cities.count(city) for city in set(cities)}
    }
```

## Common Use Cases

### 1. Location-Based Queries
- **"Where is John Smith located?"**
- **"What city is Sarah in?"**
- **"Find the office location for this user"**

### 2. Meeting and Event Planning
- **"Are we in the same city for this meeting?"**
- **"Choose a convenient location for all attendees"**
- **"Plan regional team events"**

### 3. Logistics and Coordination
- **"What's Mike's address for shipping?"**
- **"Find local team members for collaboration"**
- **"Regional coordination and support"**

### 4. Time Zone and Regional Considerations
- **"Determine time zones for scheduling"**
- **"Plan across different regions"**
- **"Regional compliance requirements"**

## Integration with Other Services

### Azure Maps Integration
Combine user location with Azure Maps for enhanced functionality:

```python
from plugins.azure_maps_plugin import AzureMapsPlugin

# Get user location
location = await graph_plugin.get_user_location(user_id)
if location and location.get('city'):
    # Use Azure Maps to find nearby restaurants for meeting
    maps_plugin = AzureMapsPlugin()
    
    # Note: You would need to geocode the city to get coordinates
    # This is a conceptual example
    nearby_restaurants = await maps_plugin.search_nearby_locations(
        latitude=47.6062,  # Seattle coordinates (example)
        longitude=-122.3321,
        radius=5000,
        limit=10
    )
```

### Calendar Integration
Use location for intelligent scheduling:

```python
async def smart_meeting_scheduling(organizer_id, attendee_ids):
    """Schedule meetings considering attendee locations."""
    locations = []
    
    for attendee_id in attendee_ids:
        location = await graph_plugin.get_user_location(attendee_id)
        if location:
            locations.append(location)
    
    # Determine if virtual or in-person meeting is better
    unique_cities = set(loc.get('city') for loc in locations if loc.get('city'))
    
    if len(unique_cities) <= 1:
        # All attendees in same city - suggest in-person meeting
        meeting_type = "in-person"
        location_suggestion = list(unique_cities)[0] if unique_cities else "Virtual"
    else:
        # Distributed team - suggest virtual meeting
        meeting_type = "virtual"
        location_suggestion = "Microsoft Teams"
    
    return {
        'meeting_type': meeting_type,
        'suggested_location': location_suggestion,
        'attendee_locations': locations
    }
```

## Error Handling

The function includes comprehensive error handling:

```python
try:
    location = await graph_plugin.get_user_location(user_id)
    if location:
        # Process location data
        city = location.get('city', 'Unknown')
        print(f"User is in {city}")
    else:
        print("Location information not available")
except ValueError as ve:
    print(f"Invalid input: {ve}")
except Exception as e:
    print(f"Error retrieving location: {e}")
```

## Data Availability Notes

### Profile Completion
Location information depends on user profile completion:
- Users must have populated their city, state, and postal code fields
- Some organizations may not require or collect this information
- Profile data may be managed by HR systems or user self-service

### Privacy Considerations
- Respect user privacy and organizational policies
- Location data may be sensitive in some contexts
- Consider data retention and access policies

### Fallback Strategies
When location data is not available:
```python
location = await graph_plugin.get_user_location(user_id)

if not location or not any(location.values()):
    # Fallback strategies:
    # 1. Use manager's location
    manager = await graph_plugin.get_user_manager(user_id)
    if manager:
        manager_location = await graph_plugin.get_user_location(manager.id)
    
    # 2. Use department default location
    # 3. Use organizational headquarters
    # 4. Default to virtual/remote
```

## Testing

Run the included test script to verify functionality:

```bash
python test_user_location_plugin.py
```

The test script will:
1. Validate environment variables
2. Initialize the Graph Plugin
3. Search for test users
4. Test location retrieval
5. Display results and usage examples

## Environment Setup

Ensure these environment variables are set:
- `ENTRA_GRAPH_APPLICATION_TENANT_ID`
- `ENTRA_GRAPH_APPLICATION_CLIENT_ID`
- `ENTRA_GRAPH_APPLICATION_CLIENT_SECRET`

## AI Agent Integration

### Semantic Kernel Integration
The function is decorated with `@kernel_function` and includes comprehensive descriptions for AI agents:

```python
# The AI agent can automatically understand when to use this function
# based on user queries like:
# - "Where is John located?"
# - "Find users in Seattle"
# - "Plan a meeting with local team members"
```

### Natural Language Examples
The function description includes examples that help AI agents understand appropriate usage:
- Location-based queries
- Meeting planning scenarios
- Regional coordination
- Logistics planning

## Performance Considerations

- Location lookup is a lightweight operation
- Results can be cached for frequently accessed users
- Batch processing for multiple users is recommended
- Consider rate limiting for large-scale operations

## Future Enhancements

Potential improvements for the location functionality:
1. **Geocoding Integration**: Convert city/state to coordinates
2. **Distance Calculations**: Find users within X miles of a location
3. **Time Zone Detection**: Automatically determine time zones from location
4. **Office Mapping**: Map users to specific office buildings/floors
5. **Travel Distance Matrix**: Calculate travel times between user locations
