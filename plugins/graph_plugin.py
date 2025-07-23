from datetime import datetime
import os
import asyncio
from typing import List, Optional, Annotated, Dict, Any
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

# Import telemetry components first
from telemetry.decorators import TelemetryContext
from telemetry.console_output import console_info, console_debug, console_telemetry_event, console_error, console_warning

# Try to import the real GraphOperations, fallback to mock if it fails
try:
    from operations.graph_operations import GraphOperations
    console_info("✓ Using Microsoft Graph Operations", module="GraphPlugin")
except Exception as e:
    console_error(f"⚠ Could not import GraphOperations: {e}", module="GraphPlugin")
    raise


try:
    from utils.teams_utilities import TeamsUtilities
    # Initialize TeamsUtilities for sending messages
    teams_utils = TeamsUtilities()
    TEAMS_UTILS_AVAILABLE = True
except ImportError as e:
    console_error(f"⚠ Teams utilities not available: {e}", module="GraphPlugin")
    TEAMS_UTILS_AVAILABLE = False
    
    # Fallback TeamsUtilities that does nothing
    class MockTeamsUtilities:
        def send_friendly_notification(self, message, session_id=None, debug=False):
            if debug:
                session_info = f"[session: {session_id}] " if session_id else ""
                print(f"TEAMS: {session_info}{message}")
    
    teams_utils = MockTeamsUtilities()

graph_operations = GraphOperations(
    user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
    calendar_response_fields=["id", "subject", "start", "end", "location", "attendees", "body"]
)
max_results = 100

class GraphPlugin:
    def __init__(self, debug=False, session_id=None):
        self.debug = debug
        self.session_id = session_id

    # Helper method to log function calls if debug is enabled
    def _log_function_call(self, function_name, **kwargs):
        if self.debug:
            params_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
            session_info = f"[session: {self.session_id}] " if self.session_id else ""
            print(f"DEBUG: {session_info}Calling kernel function '{function_name}' with parameters: {params_str}")
    
    # Helper method to send friendly notifications to the user
    def _send_friendly_notification(self, message: str):
        """Send a friendly notification to the user via Teams about what we're working on."""
        teams_utils.send_friendly_notification(message, self.session_id, self.debug)

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Search for users in Microsoft 365 Tenant Entra Directory using flexible filter criteria.
        
        USE THIS WHEN:
        - User asks to "find", "search for", or "look up" specific users
        - Need to locate users by name, job title, department, or other attributes
        - User provides partial information (e.g., "find John in Engineering")
        - Looking for executives, managers, or specific roles
        
        CAPABILITIES:
        - Uses OData query language for powerful filtering
        - Automatically excludes users without active mailboxes by default
        - Supports complex queries with multiple criteria
        - Case-insensitive searches
        
        COMMON USE CASES:
        - "Find the CEO" or "Who is the Chief Executive Officer?"
        - "Show me all managers in the Engineering department"
        - "Find John Smith" or "Look up users named Sarah"
        - "Who works in the Sales department?"
        
        FILTER EXAMPLES:
        - startswith(displayName,'John') - Find users whose name starts with "John"
        - jobTitle eq 'Manager' - Find all managers
        - department eq 'Engineering' - Find all Engineering employees
        - department eq 'Sales' and jobTitle eq 'Manager' - Find Sales managers
        - contains(displayName,'Smith') - Find users with "Smith" in their name
        """
    )
    async def user_search(self, filter: Annotated[str, "User search filter parameter. Use OData query syntax to filter users."], include_inactive_mailboxes: Annotated[bool, "Set to true to include users without active mailboxes. Default is false."] = False) -> Annotated[List[dict], "Returns a list of users matching the filter criteria, excluding users without mailboxes by default."]:
        self._log_function_call("user_search", filter=filter, include_inactive_mailboxes=include_inactive_mailboxes)
        self._send_friendly_notification("🔍 Searching for users in your directory...")
        if not filter: raise ValueError("Error: filter parameter is empty")
        try:
            # Using a synchronous approach here
            return await graph_operations.search_users(filter, max_results=max_results, exclude_inactive_mailboxes=not include_inactive_mailboxes)
        except Exception as e:
            print(f"Error in user_search: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get detailed user preferences and profile information for a specific user by their ID.
        
        USE THIS WHEN:
        - You already have a user's ID and need their detailed profile information
        - User asks for someone's "preferences", "profile", or "details"
        - Need comprehensive user information including personal settings
        - Following up on a user found through search to get more details
        
        RETURNS:
        - Display name, email, job title, department
        - Manager information
        - User preferences and settings
        - Complete user profile data
        
        COMMON USE CASES:
        - "Show me John's profile details"
        - "What are Sarah's user preferences?"
        - "Get detailed information about this user"
        - Getting full profile after finding user through search
        
        NOTE: Requires the exact user ID (GUID format)
        """
    )
        
    async def get_user_preferences_by_user_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user to retrieve"]) -> Annotated[dict, "Returns detailed information about the specified user."]:
        self._log_function_call("get_user_preferences_by_user_id", user_id=user_id)
        self._send_friendly_notification("⚙️ Getting user preferences and settings...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_user_preferences_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_preferences_by_user_id: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get comprehensive mailbox settings and configuration for a specific user.
        
        USE THIS WHEN:
        - User asks about someone's "mailbox settings", "email preferences", or "mail configuration"
        - Need to check time zone settings for scheduling meetings
        - Investigating email-related issues or preferences
        - User asks about working hours, automatic replies, or email signatures
        
        RETURNS:
        - Time zone and language preferences
        - Working hours and availability settings
        - Automatic reply (out-of-office) configurations
        - Email signature settings
        - Mailbox size and quota information
        - Email forwarding rules
        
        COMMON USE CASES:
        - "What time zone is John in?"
        - "Check Sarah's working hours"
        - "Is Mike's out-of-office reply enabled?"
        - "What are the mailbox settings for this user?"
        - Troubleshooting calendar scheduling across time zones
        
        NOTE: Requires the exact user ID (GUID format) and user must have an active mailbox
        """
    )
        
    async def get_user_mailbox_settings_by_user_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose mailbox settings you want to retrieve"]) -> Annotated[dict, "Returns detailed mailbox settings for the specified user."]:
        self._log_function_call("get_user_mailbox_settings_by_user_id", user_id=user_id)
        self._send_friendly_notification("📧 Checking user mailbox settings and configuration...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_user_mailbox_settings_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_mailbox_settings_by_user_id: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get basic user information by their unique ID from Microsoft 365 Directory.
        
        USE THIS WHEN:
        - You have a specific user ID and need basic profile information
        - Need to verify a user exists and get their core details
        - Want basic info without full preferences or mailbox settings
        - Quick lookup for user validation
        
        RETURNS:
        - Display name and email address
        - Job title and department
        - User principal name
        - Manager information
        - Basic contact information
        
        COMMON USE CASES:
        - "Get basic info for user ID xyz"
        - Verifying user exists before other operations
        - Quick profile lookup
        - Getting user's name and title for display
        
        DIFFERENCE FROM OTHER USER FUNCTIONS:
        - get_user_by_id: Basic user info (use for quick lookups)
        - get_user_preferences_by_user_id: Detailed preferences and settings
        - get_user_mailbox_settings_by_user_id: Mailbox-specific configuration
        
        NOTE: Requires the exact user ID (GUID format)
        """
    )
    @kernel_function(
        description="""
        Get basic user information by their unique ID from Microsoft 365 Directory.
        
        USE THIS WHEN:
        - You have a specific user ID and need basic profile information
        - Need to verify a user exists and get their core details
        - Want basic info without full preferences or mailbox settings
        - Quick lookup for user validation
        
        RETURNS:
        - Display name and email address
        - Job title and department
        - User principal name
        - Manager information
        - Basic contact information
        
        COMMON USE CASES:
        - "Get basic info for user ID xyz"
        - Verifying user exists before other operations
        - Quick profile lookup
        - Getting user's name and title for display
        
        DIFFERENCE FROM OTHER USER FUNCTIONS:
        - get_user_by_id: Basic user info (use for quick lookups)
        - get_user_preferences_by_user_id: Detailed preferences and settings
        - get_user_mailbox_settings_by_user_id: Mailbox-specific configuration
        
        NOTE: Requires the exact user ID (GUID format)
        """
    )
    async def get_user_by_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user to retrieve"]) -> Annotated[dict, "Returns detailed information about the specified user."]:
        self._log_function_call("get_user_by_id", user_id=user_id)
        self._send_friendly_notification("🔍 Looking up user profile using their ID information...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_user_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_by_id: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get basic user information by their email address from Microsoft 365 Directory.
        
        USE THIS WHEN:
        - You have a user's email address and need their profile information
        - User provides an email address instead of user ID
        - Need to look up someone by their email
        - Converting email address to user profile data
        
        RETURNS:
        - Display name and email address
        - Job title and department
        - User principal name
        - Manager information
        - Basic contact information
        - User ID (for use with other functions)
        
        COMMON USE CASES:
        - "Get info for john.smith@company.com"
        - "Look up user by email address"
        - "Find profile for this email"
        - Converting email to user details for calendar operations
        
        DIFFERENCE FROM OTHER USER FUNCTIONS:
        - get_user_by_email: Basic user info by email (use when you have email)
        - get_user_by_id: Basic user info by ID (use when you have user ID)
        - user_search: Search multiple users with filters
        
        NOTE: Requires the exact email address (user@domain.com format)
        """
    )
    async def get_user_by_email(self, email: Annotated[str, "The email address of the user to retrieve"]) -> Annotated[dict, "Returns detailed information about the specified user."]:
        self._log_function_call("get_user_by_email", email=email)
        self._send_friendly_notification("📧 Looking up user profile by email address...")
        if not email or not email.strip(): raise ValueError("Error: email parameter is empty")
        try:
            return await graph_operations.get_user_by_email(email.strip())
        except Exception as e:
            print(f"Error in get_user_by_email: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get the manager/supervisor of a specific user from the organizational hierarchy.
        
        USE THIS WHEN:
        - User asks "Who is John's manager?" or "Who does Sarah report to?"
        - Need to find someone's supervisor or boss
        - Building organizational charts or understanding reporting structure
        - Escalation scenarios (need to contact someone's manager)
        
        RETURNS:
        - Manager's display name and email
        - Manager's job title and department
        - Manager's contact information
        - Organizational relationship data
        
        COMMON USE CASES:
        - "Who is the manager of John Smith?"
        - "Find Sarah's supervisor"
        - "Who does this employee report to?"
        - "Show me the reporting structure"
        - "I need to contact Mike's boss"
        
        ORGANIZATIONAL SCENARIOS:
        - Approval workflows (find who can approve)
        - Escalation paths for issues
        - Understanding team structure
        - Manager contact for HR purposes
        
        NOTE: Returns None if user has no manager assigned or is top-level executive
        """
    )
    async def get_users_manager_by_user_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose manager you want to retrieve"]) -> Annotated[dict, "Returns information about the user's manager."]:
        self._log_function_call("get_user_manager", user_id=user_id)
        self._send_friendly_notification("👔 Finding manager information in org chart...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_users_manager_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_manager: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get location details (city, state, and zipcode) for a specific user from their Microsoft 365 profile.
        
        USE THIS WHEN:
        - User asks about someone's location, office, or where they're based
        - Need geographical information for meeting planning or scheduling
        - Want to find users in specific cities, states, or regions
        - Planning logistics for events, meetings, or travel
        - Determining time zones or regional considerations
        
        RETURNS:
        - City where the user is located
        - State/province information
        - Postal/zip code
        - Complete address components for geographical reference
        
        COMMON USE CASES:
        - "Where is John Smith located?" or "What city is Sarah in?"
        - "Find the office location for this user"
        - "What's Mike's address for shipping?"
        - Planning in-person meetings: "Are we in the same city?"
        - Regional team organization: "Who's in our Seattle office?"
        
        LOCATION-BASED SCENARIOS:
        - Meeting planning: Choose convenient locations for attendees
        - Time zone considerations: Schedule across different regions
        - Regional coordination: Find local team members
        - Logistics planning: Shipping, travel, or event coordination
        - Compliance: Data residency or regional requirements
        
        INTEGRATION WITH OTHER SERVICES:
        - Use with Azure Maps plugin to find nearby restaurants/venues
        - Combine with calendar functions for location-based scheduling
        - Support travel planning and expense management
        
        NOTE: Returns None if location information is not populated in user profile
        """
    )
    async def get_users_city_state_zipcode_by_user_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose location details you want to retrieve"]) -> Annotated[dict, "Returns location information (city, state, zipcode) for the specified user."]:
        self._log_function_call("get_user_location", user_id=user_id)
        self._send_friendly_notification("📍 Looking up user location details...")
        if not user_id or not user_id.strip(): 
            raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_users_city_state_zipcode_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_location: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get all direct reports (employees/subordinates) who report directly to a specific user.
        
        USE THIS WHEN:
        - User asks "Who reports to John?" or "Show me Sarah's team"
        - Need to see someone's direct subordinates or team members
        - Building organizational charts or team structures
        - Manager wants to see their team roster
        
        RETURNS:
        - List of all direct reports with their basic information
        - Each report includes name, email, job title, department
        - Complete team roster for the specified manager
        
        COMMON USE CASES:
        - "Who are John's direct reports?"
        - "Show me Sarah's team members"
        - "List all employees under this manager"
        - "What's the size of Mike's team?"
        - "Who works directly for the department head?"
        
        MANAGEMENT SCENARIOS:
        - Team roster for meetings
        - Performance review cycles
        - Team size analysis
        - Organizational restructuring
        - Manager contact lists
        
        NOTE: Returns empty list if user has no direct reports or is not a manager
        """
    )
    async def get_direct_reports(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose direct reports you want to retrieve"]) -> Annotated[List[dict], "Returns a list of users who report directly to the specified user."]:
        self._log_function_call("get_direct_reports", user_id=user_id)
        self._send_friendly_notification("👥 Getting team members and direct reports...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_direct_reports_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_direct_reports: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get all users from the Microsoft 365 organization directory.
        
        USE THIS WHEN:
        - User asks for "all users", "everyone in the company", or "complete user list"
        - Need a comprehensive view of the organization
        - User wants to see company-wide statistics or counts
        - Creating organization-wide reports or analysis
        
        CAPABILITIES:
        - Automatically excludes inactive users without mailboxes (default)
        - Configurable result limits (max 1000 users)
        - Option to include all users including inactive ones
        - Returns essential user information for each person
        
        COMMON USE CASES:
        - "Show me all users in the company"
        - "How many employees do we have?"
        - "List everyone in the organization"
        - "Get a complete directory"
        - Company-wide analysis or reporting
        
        PERFORMANCE CONSIDERATIONS:
        - Large organizations should use smaller max_results values
        - Default excludes inactive users for better performance
        - Consider using department-specific queries for focused results
        
        WHEN NOT TO USE:
        - When looking for specific users (use user_search instead)
        - When interested in a specific department (use get_users_by_department)
        - For very large organizations (>1000 users) without pagination
        
        NOTE: Results are limited to max_results parameter (default 100, max 1000)
        """
    )
    async def get_all_users(self, max_results: Annotated[int, "Maximum number of users to return (default: 100)"] = 100, include_inactive_mailboxes: Annotated[bool, "Set to true to include users without active mailboxes. Default is false."] = False) -> Annotated[List[dict], "Returns a list of users from the Microsoft 365 Tenant Entra Directory, excluding users without mailboxes by default."]:
        self._log_function_call("get_all_users", max_results=max_results, include_inactive_mailboxes=include_inactive_mailboxes)
        self._send_friendly_notification("👥 Getting all users from your organization directory...")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_all_users(max_results, exclude_inactive_mailboxes=not include_inactive_mailboxes)
        except Exception as e:
            print(f"Error in get_all_users: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get all users from a specific department in the organization.
        
        USE THIS WHEN:
        - User asks for people in a specific department (e.g., "Show me IT department users")
        - Need to see team composition for a particular department
        - Department-specific analysis or reporting
        - User specifies department name in their query
        
        CAPABILITIES:
        - Filters users by exact department name match
        - Excludes inactive users without mailboxes (default)
        - Configurable result limits
        - Returns department-specific user roster
        
        COMMON USE CASES:
        - "Who works in the Engineering department?"
        - "Show me all Sales team members"
        - "List everyone in IT"
        - "How many people are in Marketing?"
        - Department roster for meetings or communication
        
        IMPORTANT PREREQUISITES:
        - Department names must match exactly (case-sensitive)
        - Use get_all_departments() first to see available department names
        - Never guess department names - always verify or ask user for clarification
        
        WORKFLOW RECOMMENDATION:
        1. If unsure about department name, call get_all_departments() first
        2. Show user the available departments
        3. Use exact department name from the list
        
        EXAMPLE DEPARTMENTS:
        - "Information Technology", "Engineering", "Sales", "Marketing"
        - "Human Resources", "Finance", "Operations"

        COMMON ALIASES:
        - "IT" for "Information Technology"
        - "HR" for "Human Resources"
        - "Eng" for "Engineering"
        - "App Dev" for "Application Development"

        
        NOTE: Returns empty list if department name doesn't match exactly
        """
    )
    async def get_users_by_department(self, department: Annotated[str, "The department name to filter users by"], max_results: Annotated[int, "Maximum number of users to return (default: 100)"] = 100, include_inactive_mailboxes: Annotated[bool, "Set to true to include users without active mailboxes. Default is false."] = False) -> Annotated[List[dict], "Returns a list of users from the specified department, excluding users without mailboxes by default."]:
        self._log_function_call("get_users_by_department", department=department, max_results=max_results, include_inactive_mailboxes=include_inactive_mailboxes)
        self._send_friendly_notification(f"🏢 Looking up users in the {department} department...")
        if not department or not department.strip(): raise ValueError("Error: department parameter is empty")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_users_by_department(department.strip(), max_results, exclude_inactive_mailboxes=not include_inactive_mailboxes)
        except Exception as e:
            print(f"Error in get_users_by_department: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get a complete list of all unique departments in the organization.
        
        USE THIS WHEN:
        - User asks "What departments exist?" or "Show me all departments"
        - Need to discover available departments before filtering users
        - User is unsure about exact department names
        - Building organizational structure understanding
        
        RETURNS:
        - List of all unique department names found in the directory
        - Exact department names that can be used for filtering
        - Organizational structure insight
        
        COMMON USE CASES:
        - "What departments do we have?"
        - "Show me all the departments in the company"
        - "List the organizational departments"
        - Preparing for department-specific queries
        - Organizational analysis and reporting
        
        CRITICAL FOR WORKFLOW:
        - Use this FIRST when user mentions department but doesn't specify exact name
        - Use returned department names exactly in get_users_by_department()
        - Essential for discovering correct department spelling/formatting
        
        EXAMPLE WORKFLOW:
        User: "Show me people in IT"
        1. Call get_all_departments() to see: ["Information Technology", "Engineering", "Sales"]
        2. Match "IT" to "Information Technology"
        3. Call get_users_by_department("Information Technology")
        
        DISCOVERY SCENARIOS:
        - User says "Engineering" but actual name is "Software Engineering"
        - User says "HR" but actual name is "Human Resources"
        - User says "IT" but actual name is "Information Technology"
        
        NOTE: Scans max_results users to extract department names
        """
    )
    async def get_all_departments(self, max_results: Annotated[int, "Maximum number of users to scan for departments (default: 100)"] = 100) -> Annotated[List[str], "Returns a list of all unique departments in the Microsoft 365 Tenant Entra Directory."]:
        self._log_function_call("get_all_departments", max_results=max_results)
        self._send_friendly_notification("🏢 Discovering all departments in your organization...")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_all_departments(max_results)
        except Exception as e:
            print(f"Error in get_all_departments: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get all conference rooms and meeting spaces available in the organization.
        
        USE THIS WHEN:
        - User asks about "conference rooms", "meeting rooms", or "available rooms"
        - Need to see what meeting spaces are available for booking
        - User wants to find rooms for scheduling meetings
        - Planning events or meetings requiring physical spaces
        
        RETURNS:
        - List of all conference room resources
        - Room names, email addresses, and basic information
        - Available meeting spaces in the organization
        
        COMMON USE CASES:
        - "What conference rooms do we have?"
        - "Show me all meeting rooms"
        - "List available conference rooms"
        - "Find rooms for booking meetings"
        - "What meeting spaces are available?"
        
        MEETING PLANNING SCENARIOS:
        - Scheduling team meetings
        - Planning presentations or training sessions
        - Booking rooms for client meetings
        - Event planning and space management
        
        TYPICAL ROOM NAMING:
        - Rooms usually have email addresses starting with "room" or "conf"
        - Examples: "Conference Room A", "Board Room", "Training Room 1"
        
        NOTE: Use get_conference_room_events() to see room availability and bookings
        """
    )
    async def get_all_conference_rooms(self, max_results: Annotated[int, "Maximum number of conference rooms to scan for (default: 100)"] = 100) -> Annotated[List[str], "Returns a list of all unique conference rooms in the Microsoft 365 Tenant Entra Directory."]:
        self._log_function_call("get_all_conference_rooms", max_results=max_results)
        self._send_friendly_notification("🏢 Finding all available meeting rooms and conference spaces...")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_all_conference_rooms(max_results)
        except Exception as e:
            print(f"Error in get_all_conference_rooms: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get comprehensive details about a specific conference room including capacity and location.
        
        USE THIS WHEN:
        - User asks for specific details about a particular conference room
        - Need room capacity information for meeting planning
        - User wants to know room location or amenities
        - Following up on a room found through get_all_conference_rooms()
        
        RETURNS:
        - Room name, email address, and contact information
        - Room capacity (number of people it can accommodate)
        - Physical location and address details
        - Room configuration and amenities information
        
        COMMON USE CASES:
        - "What's the capacity of Conference Room A?"
        - "Where is the Board Room located?"
        - "Tell me about this specific meeting room"
        - "Does this room have video conferencing equipment?"
        - "How many people can fit in Room 301?"
        
        MEETING PLANNING DETAILS:
        - Verify room can accommodate team size
        - Check if room location is convenient for attendees
        - Understand room layout and equipment
        - Plan meeting logistics based on room features
        
        WORKFLOW:
        1. Use get_all_conference_rooms() to find available rooms
        2. Use this function to get details about specific rooms of interest
        3. Make booking decisions based on detailed information
        
        NOTE: Requires the exact room ID (GUID format) from the conference room list
        """
    )
    async def get_conference_room_details_by_id(self, room_id: Annotated[str, "The unique ID of the conference room to retrieve details for"]) -> Annotated[dict, "Returns detailed information about the specified conference room."]:
        self._log_function_call("get_conference_room_details_by_id", room_id=room_id)
        self._send_friendly_notification("🏢 Getting detailed conference room information...")
        if not room_id or not room_id.strip(): raise ValueError("Error: room_id parameter is empty")
        try:
            return await graph_operations.get_conference_room_details_by_id(room_id.strip())
        except Exception as e:
            print(f"Error in get_conference_room_details_by_id: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get comprehensive conference room usage report showing all rooms and their current bookings/events.
        
        USE THIS WHEN:
        - User asks about "conference room availability", "room bookings", or "meeting room usage"
        - Need to see which rooms are busy or available
        - User wants an overview of all room activity
        - Planning meetings and need to avoid conflicts
        
        PROVIDES COMPLETE VIEW OF:
        - All conference rooms in the organization
        - Current and upcoming bookings for each room
        - Meeting details: subject, time, attendees, location
        - Room availability status and usage patterns
        
        CAPABILITIES:
        - Optional date range filtering (start/end dates)
        - Comprehensive event details including attendees
        - Enhanced error handling for calendar access issues
        
        COMMON USE CASES:
        - "Show me conference room availability"
        - "Which meeting rooms are booked today?"
        - "What's the conference room usage status?"
        - "Are there any available conference rooms?"
        - "Show me all room bookings"
        - "Check conference room availability for this week"
        - "Show me room bookings for July 2025"
        
        DATE FILTERING EXAMPLES:
        - start_date: "2025-07-01T00:00:00Z" (July 1st, 2025)
        - end_date: "2025-07-31T23:59:59Z" (End of July 2025)
        - For today's events: use current date
        - For this week: use Monday to Sunday range
        
        SCHEDULING SCENARIOS:
        - Finding available rooms for immediate meetings
        - Understanding room utilization patterns
        - Avoiding double-booked rooms
        - Planning around existing meetings
        - Room usage analysis and reporting
        
        DETAILED INFORMATION INCLUDES:
        - Room basic info (name, email, capacity)
        - All calendar events per room (within date range if specified)
        - Event details (subject, start/end times, attendees)
        - Meeting organizer and participant information
        
        WHEN TO USE vs OTHER FUNCTIONS:
        - Use this for comprehensive room + calendar overview
        - Use get_all_conference_rooms() for just room list
        - Use get_calendar_events() for specific user calendars
        
        NOTE: This provides the most complete conference room usage picture with optional date filtering
        """
    )
    async def get_conference_room_events(self, max_results: Annotated[int, "Maximum number of conference rooms to scan for events (default: 100)"] = 100, start_date: Annotated[str, "Optional start date for filtering events (ISO 8601 format, e.g., '2025-07-01T00:00:00Z')"] = None, end_date: Annotated[str, "Optional end date for filtering events (ISO 8601 format, e.g., '2025-07-31T23:59:59Z')"] = None) -> Annotated[List[dict], "Returns detailed information about conference rooms and their calendar events."]:
        self._log_function_call("get_conference_room_events", max_results=max_results, start_date=start_date, end_date=end_date)
        self._send_friendly_notification("📅 Checking conference room availability and bookings...")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        
        # Convert string dates to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                # Try parsing ISO 8601 format with timezone
                if start_date.endswith('Z'):
                    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_datetime = datetime.fromisoformat(start_date)
            except ValueError as e:
                print(f"Error parsing start_date '{start_date}': {e}")
                start_datetime = None
                
        if end_date:
            try:
                # Try parsing ISO 8601 format with timezone
                if end_date.endswith('Z'):
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_datetime = datetime.fromisoformat(end_date)
            except ValueError as e:
                print(f"Error parsing end_date '{end_date}': {e}")
                end_datetime = None
        
        try:
            # Get all conference rooms
            conference_rooms = await graph_operations.get_all_conference_rooms(max_results)
            if not conference_rooms:
                return []
            
            # Use the new method to get conference room events data with date filtering
            conference_rooms_with_events = await graph_operations.get_conference_room_events(conference_rooms, start_datetime, end_datetime)
            return conference_rooms_with_events
        except Exception as e:
            print(f"Error in get_conference_room_events: {e}")
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Validate if a user has a functional mailbox before attempting calendar or email operations.
        
        USE THIS WHEN:
        - Calendar operations fail with mailbox-related errors
        - User asks about someone's "mailbox status" or "email availability"
        - Troubleshooting why calendar events can't be retrieved
        - Verifying user has active Exchange Online mailbox
        
        DIAGNOSTIC CAPABILITIES:
        - Checks if user has valid Exchange Online mailbox
        - Identifies inactive, disabled, or on-premise mailboxes
        - Provides specific error messages and solutions
        - Validates mailbox REST API access
        
        COMMON USE CASES:
        - "Why can't I see John's calendar?"
        - "Is this user's mailbox active?"
        - "Check if Sarah can receive emails"
        - Troubleshooting calendar access issues
        - Pre-validation before calendar operations
        
        MAILBOX ISSUES DETECTED:
        - Mailbox not enabled for REST API (on-premise/hybrid)
        - User account disabled or inactive
        - Missing Exchange Online license
        - Soft-deleted mailboxes
        - Insufficient permissions
        
        TROUBLESHOOTING WORKFLOW:
        1. Use this when get_calendar_events() fails
        2. Check the validation result and error message
        3. Follow the provided diagnostic suggestions
        4. Retry calendar operations after resolving issues
        
        NOTE: Essential for diagnosing calendar and email access problems
        """
    )
    async def validate_user_mailbox(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose mailbox you want to validate"]) -> Annotated[dict, "Returns validation result with status and diagnostic information."]:
        self._log_function_call("validate_user_mailbox", user_id=user_id)
        self._send_friendly_notification("🔧 Validating user mailbox status and permissions...")
        if not user_id or not user_id.strip(): 
            raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.validate_user_mailbox(user_id.strip())
        except Exception as e:
            print(f"Error in validate_user_mailbox: {e}")
            return {
                'valid': False,
                'message': f'Error validating user: {e}',
                'user_info': None
            }
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get calendar events and meetings for a specific user with optional date filtering.
        
        USE THIS WHEN:
        - User asks to "show calendar", "get meetings", or "check schedule"
        - Need to see someone's appointments or availability
        - User specifies date ranges for calendar viewing
        - Planning meetings around existing schedules
        
        CAPABILITIES:
        - Retrieves all calendar events for specified user
        - Optional date range filtering (start/end dates)
        - Comprehensive event details including attendees
        - Enhanced error handling for mailbox issues
        
        COMMON USE CASES:
        - "Show me John's calendar for this week"
        - "What meetings does Sarah have tomorrow?"
        - "Check my calendar for July 2025"
        - "Are there any conflicts with Mike's schedule?"
        - "Show upcoming meetings for next month"
        
        DATE FILTERING EXAMPLES:
        - start_date: "2025-07-01T00:00:00Z" (July 1st, 2025)
        - end_date: "2025-07-31T23:59:59Z" (End of July 2025)
        - For today's events: use current date
        - For this week: use Monday to Sunday range
        
        EVENT DETAILS PROVIDED:
        - Meeting subject and description
        - Start and end times with time zones
        - Meeting location (physical or virtual)
        - All attendees and their response status
        - Meeting organizer information
        
        TROUBLESHOOTING:
        - If this fails, use validate_user_mailbox() first
        - Handles mailbox permission and access issues
        - Provides specific error guidance for common problems
        
        NOTE: Requires user to have active Exchange Online mailbox
        """
    )
    async def get_calendar_events(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose calendar events you want to retrieve"], start_date: Annotated[str, "Optional start date for filtering events (ISO 8601 format, e.g., '2025-07-01T00:00:00Z')"] = None, end_date: Annotated[str, "Optional end date for filtering events (ISO 8601 format, e.g., '2025-07-31T23:59:59Z')"] = None) -> Annotated[List[dict], "Returns a list of calendar events for the specified user."]:
        self._log_function_call("get_calendar_events", user_id=user_id, start_date=start_date, end_date=end_date)
        self._send_friendly_notification("📅 Retrieving calendar events and meetings...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        
        # Convert string dates to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                # Try parsing ISO 8601 format with timezone
                if start_date.endswith('Z'):
                    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_datetime = datetime.fromisoformat(start_date)
            except ValueError as e:
                print(f"Error parsing start_date '{start_date}': {e}")
                start_datetime = None
                
        if end_date:
            try:
                # Try parsing ISO 8601 format with timezone
                if end_date.endswith('Z'):
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_datetime = datetime.fromisoformat(end_date)
            except ValueError as e:
                print(f"Error parsing end_date '{end_date}': {e}")
                end_datetime = None
        
        try:
            result = await graph_operations.get_calendar_events_by_user_id(user_id.strip(), start_datetime, end_datetime)
            
            # Handle case where result is None (validation failed or error occurred)
            if result is None:
                print(f"⚠️ Unable to retrieve calendar events for user {user_id}")
                print("   This is typically due to:")
                print("   • Mailbox not enabled for REST API")
                print("   • User account is inactive or disabled")
                print("   • Insufficient permissions")
                print("   • User has no Exchange Online license")
                return []
                
            return result
        except Exception as e:
            error_message = str(e)
            print(f"Error in get_calendar_events: {e}")
            
            # Provide user-friendly error context
            if "MailboxNotEnabledForRESTAPI" in error_message:
                print("💡 TIP: Try validating the user's mailbox first using validate_user_mailbox function")
                print("   This error typically means the user doesn't have a cloud-based Exchange mailbox")
            elif "Forbidden" in error_message or "403" in error_message:
                print("💡 TIP: Check application permissions - may need Calendars.Read or admin consent")
            elif "NotFound" in error_message or "404" in error_message:
                print("💡 TIP: Verify the user ID exists and the user has an active mailbox")
                
            return []
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Create a new calendar event/meeting in a user's Microsoft 365 calendar with attendees.
        
        USE THIS WHEN:
        - User asks to "schedule a meeting", "create an event", or "book a calendar appointment"
        - Need to set up meetings with specific attendees and times
        - User provides meeting details like subject, time, location, participants
        - Organizing team meetings, client calls, or appointments
        
        MEETING CREATION CAPABILITIES:
        - Creates events in specified user's calendar
        - Supports required and optional attendees
        - Includes meeting location (physical or virtual)
        - Sends meeting invitations automatically
        
        COMMON USE CASES:
        - "Schedule a team meeting for tomorrow at 2 PM"
        - "Create a client call for Friday with John and Sarah"
        - "Book a training session in Conference Room A"
        - "Set up a weekly recurring meeting"
        - "Schedule a project review with stakeholders"
        
        REQUIRED INFORMATION:
        - Subject: Meeting title/description
        - Start time: ISO 8601 format (e.g., '2025-07-15T14:00:00Z')
        - End time: ISO 8601 format (e.g., '2025-07-15T15:00:00Z')
        - Organizer user ID: Who creates/owns the meeting
        
        OPTIONAL DETAILS:
        - Location: Conference room, address, or "Microsoft Teams"
        - Required attendees: Email addresses of must-attend participants
        - Optional attendees: Email addresses of optional participants
        - Body: Detailed description, agenda, or other event information (supports HTML formatting)
        
        TIME FORMAT EXAMPLES:
        - "2025-07-15T14:00:00Z" = July 15, 2025, 2:00 PM UTC
        - "2025-07-20T09:30:00Z" = July 20, 2025, 9:30 AM UTC
        
        ATTENDEE MANAGEMENT:
        - Required attendees get "required" invitation type
        - Optional attendees get "optional" invitation type
        - All attendees receive calendar invitations automatically
        
        BODY CONTENT:
        - Supports HTML formatting for rich text
        - Can include agendas, meeting details, links, and instructions
        - Will appear in calendar event details and email invitations
        
        NOTE: Organizer must have calendar creation permissions
        """
    )
    async def create_calendar_event(self, user_id: Annotated[str, "The unique user ID (GUID) of the user in whose calendar the event will be created"], subject: Annotated[str, "The subject/title of the calendar event"], start: Annotated[str, "Start date and time of the event in ISO 8601 format (e.g., '2025-07-15T14:00:00Z')"], end: Annotated[str, "End date and time of the event in ISO 8601 format (e.g., '2025-07-15T15:00:00Z')"], location: Annotated[str, "Optional location for the event"] = None, body: Annotated[str, "Optional detailed description/agenda for the event (supports HTML formatting)"] = None, attendees: Annotated[List[str], "Optional list of required attendee email addresses"] = None, optional_attendees: Annotated[List[str], "Optional list of optional attendee email addresses"] = None) -> Annotated[dict, "Returns information about the created calendar event."]:
        self._log_function_call("create_calendar_event", user_id=user_id, subject=subject, start=start, end=end, 
                              location=location, body=body, attendees=attendees, optional_attendees=optional_attendees)
        self._send_friendly_notification("✨ Creating new calendar event and sending invitations...")
        
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        if not subject or not subject.strip(): raise ValueError("Error: subject parameter is empty")
        if not start or not start.strip(): raise ValueError("Error: start parameter is empty")
        if not end or not end.strip(): raise ValueError("Error: end parameter is empty")
        
        try:
            return await graph_operations.create_calendar_event(
                user_id.strip(), subject.strip(), start.strip(), end.strip(),
                location, body, attendees, optional_attendees
            )
        except Exception as e:
            print(f"Error in create_calendar_event: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Create a new calendar event/meeting with Microsoft Teams meeting link automatically generated.
        
        USE THIS WHEN:
        - User specifically asks for a "Teams meeting", "virtual meeting", or "online meeting"
        - User mentions "video call", "video conference", or "remote meeting"
        - User wants to schedule a meeting with remote participants
        - Need a meeting with dial-in options and screen sharing capabilities
        
        TEAMS MEETING CAPABILITIES:
        - Automatically creates Teams meeting link and conference ID
        - Generates dial-in numbers for phone participants
        - Includes meeting chat thread for collaboration
        - Supports screen sharing, recording, and breakout rooms
        - Provides mobile app integration
        
        COMMON USE CASES:
        - "Schedule a Teams meeting for the project review"
        - "Create a video call with the remote team"
        - "Set up an online meeting with external clients"
        - "Book a virtual training session"
        - "Schedule a hybrid meeting (in-person + remote)"
        
        AUTOMATIC FEATURES:
        - Teams meeting link embedded in calendar invite
        - Conference ID for dial-in access
        - Meeting lobby and security controls
        - Integration with Teams chat and collaboration tools
        - Automatic meeting recording options (if enabled)
        
        ENHANCED BODY CONTENT:
        - Professional Teams meeting invitation template
        - Join link prominently displayed
        - Dial-in information for phone users
        - Meeting etiquette and guidelines
        - Technical support information
        
        LOCATION HANDLING:
        - Automatically sets location to "Microsoft Teams Meeting"
        - Can be combined with physical location for hybrid meetings
        - Override location if user specifies a different preference
        
        TIME FORMAT EXAMPLES:
        - "2025-07-15T14:00:00Z" = July 15, 2025, 2:00 PM UTC
        - "2025-07-20T09:30:00Z" = July 20, 2025, 9:30 AM UTC
        
        ATTENDEE MANAGEMENT:
        - All attendees receive Teams meeting link in their invite
        - Required attendees get "required" invitation type
        - Optional attendees get "optional" invitation type
        - External attendees can join via web browser (no Teams app required)
        
        SECURITY CONSIDERATIONS:
        - Meeting lobby is enabled by default
        - Organizer controls entry and permissions
        - Recording and sharing policies apply
        - Guest access follows organization policies
        
        NOTE: Organizer must have Teams and Exchange Online licenses
        """
    )
    async def create_teams_meeting(self, user_id: Annotated[str, "The unique user ID (GUID) of the user in whose calendar the Teams meeting will be created"], subject: Annotated[str, "The subject/title of the Teams meeting"], start: Annotated[str, "Start date and time of the meeting in ISO 8601 format (e.g., '2025-07-15T14:00:00Z')"], end: Annotated[str, "End date and time of the meeting in ISO 8601 format (e.g., '2025-07-15T15:00:00Z')"], body: Annotated[str, "Optional detailed description/agenda for the meeting (will be enhanced with Teams meeting info)"] = None, attendees: Annotated[List[str], "Optional list of required attendee email addresses"] = None, optional_attendees: Annotated[List[str], "Optional list of optional attendee email addresses"] = None, location: Annotated[str, "Optional additional location info (will be combined with Teams meeting)"] = None) -> Annotated[dict, "Returns information about the created Teams meeting and calendar event."]:
        self._log_function_call("create_teams_meeting", user_id=user_id, subject=subject, start=start, end=end, 
                              body=body, attendees=attendees, optional_attendees=optional_attendees, location=location)
        self._send_friendly_notification("🎥 Creating Microsoft Teams meeting with video conference link...")
        
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        if not subject or not subject.strip(): raise ValueError("Error: subject parameter is empty")
        if not start or not start.strip(): raise ValueError("Error: start parameter is empty")
        if not end or not end.strip(): raise ValueError("Error: end parameter is empty")
        
        try:
            return await graph_operations.create_calendar_event_with_teams(
                user_id.strip(), subject.strip(), start.strip(), end.strip(),
                location, body, attendees, optional_attendees, create_teams_meeting=True
            )
        except Exception as e:
            print(f"Error in create_teams_meeting: {e}")
            return {}
    ############################## KERNEL FUNCTION END #######################################

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Get the current date and time in standardized ISO format for calendar and scheduling operations.
        
        USE THIS WHEN:
        - User asks "what time is it?" or "what's the current date?"
        - Need current timestamp for creating calendar events
        - Setting up relative date ranges (e.g., "from now until next week")
        - Time-sensitive operations requiring precise timing
        
        CRITICAL WORKFLOW REQUIREMENT:
        - ALL calendar and date-related kernel functions should call this function FIRST
        - This ensures consistent time reference across all operations
        - Required before: create_calendar_event, get_calendar_events, get_conference_room_events
        - Use the returned timestamp for validation, comparison, and reference
        
        RETURNS:
        - Current date and time in ISO 8601 format
        - UTC timezone for consistent scheduling
        - Format: "2025-07-18T15:30:45.123456+00:00"
        
        COMMON USE CASES:
        - "What's the current time?"
        - Reference point for "schedule meeting for 2 hours from now"
        - Setting start times for immediate meetings
        - Date calculations and relative scheduling
        - Time validation before creating events
        
        CALENDAR INTEGRATION:
        - Use this timestamp as reference for event creation
        - Essential for "schedule now" or "immediate meeting" requests
        - Provides standardized time format for all calendar operations
        - Validates against past dates when scheduling meetings
        
        TIME CALCULATIONS:
        - Base for "in 1 hour", "tomorrow at this time" calculations
        - Reference for duration-based scheduling
        - Ensures consistent timezone handling
        
        DEPENDENCY PATTERN:
        - Other kernel functions should call this first to establish time context
        - Example: get_current_datetime() → create_calendar_event()
        - Example: get_current_datetime() → get_calendar_events() with relative dates
        - Example: get_current_datetime() → get_conference_room_events() with date range

        
        NOTE: Always returns UTC time for global organization coordination
        """
    )
    async def get_current_datetime(self) -> Annotated[str, "Returns the current date and time in ISO 8601 format."]:
        self._log_function_call("get_current_datetime")
        self._send_friendly_notification("🕐 Getting current date and time...")
        try: return await graph_operations.get_current_datetime()
        except Exception as e:
            print(f"Error in get_current_datetime: {e}")
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()
    ############################## KERNEL FUNCTION END #######################################

