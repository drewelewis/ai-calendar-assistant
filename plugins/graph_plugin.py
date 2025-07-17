from datetime import datetime
import os
import asyncio
from typing import List, Optional, Annotated
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

# Try to import the real GraphOperations, fallback to mock if it fails
try:
    from operations.graph_operations import GraphOperations
    # print("✓ Using real Microsoft Graph Operations")
except Exception as e:
    print(f"⚠ Could not import GraphOperations: {e}")
    # print("🎭 Falling back to mock GraphOperations for testing")
    # from operations.mock_graph_operations import GraphOperations


from utils.teams_utilities import TeamsUtilities

# Import telemetry components
from telemetry.decorators import TelemetryContext
from telemetry.console_output import console_info, console_debug, console_telemetry_event

# Initialize TeamsUtilities for sending messages
teams_utils = TeamsUtilities()

graph_operations = GraphOperations(
    user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
    calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
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
        if self.session_id:
            try:
                # Create payload with correct structure - user_id (snake_case) and message
                payload = {
                    "user_id": self.session_id,
                    "message": message
                }
                
                # Add telemetry context for Teams messaging
                with TelemetryContext(operation="teams_notification", session_id=self.session_id, message=message):
                    # Console output for notification
                    try:
                        console_telemetry_event("teams_notification", {
                            "session_id": self.session_id,
                            "message": message,
                            "notification_type": "graph_plugin_activity"
                        }, "graph_plugin")
                    except Exception as console_error:
                        if self.debug:
                            print(f"DEBUG: Could not record console telemetry: {console_error}")
                    
                    # Send the Teams notification
                    asyncio.create_task(teams_utils.send_message_fire_and_forget(payload, self.session_id))
                    
                    if self.debug:
                        console_debug(f"Sent Teams notification: {message}", "graph_plugin")
                        
            except Exception as e:
                # Silently ignore notification errors to not interrupt the main flow
                if self.debug:
                    print(f"DEBUG: Could not send notification: {e}")
                pass

    @kernel_function(
        description="""
        Useful for when you need to find users in Microsoft 365 Tenant Entra Directory.
        OData (Open Data Protocol) query language can be used to filter and search for users.
        Automatically excludes users without active mailboxes by default.
        When searching for the CEO, you can also search for Chief Executive Officer, CEO, or similar titles.
        When searching for a CFO, you can search for Chief Financial Officer, CFO, or similar titles.
        Here are a few example queries:
           
        # Filter Examples
         startswith(displayName,'John')
         jobTitle eq 'SR CLOUD SOLUTION ARCHITECT'
         department eq 'Engineering'
         department eq 'Engineering' and jobTitle eq 'Manager'
        """
    )
    async def user_search(self, filter: Annotated[str, "User search filter parameter. Use OData query syntax to filter users."], include_inactive_mailboxes: Annotated[bool, "Set to true to include users without active mailboxes. Default is false."] = False) -> Annotated[List[dict], "Returns a list of users matching the filter criteria, excluding users without mailboxes by default."]:
        self._log_function_call("user_search", filter=filter, include_inactive_mailboxes=include_inactive_mailboxes)
        self._send_friendly_notification("Searching for users in your directory...")
        if not filter: raise ValueError("Error: filter parameter is empty")
        try:
            # Using a synchronous approach here
            return await graph_operations.search_users(filter, max_results=max_results, exclude_inactive_mailboxes=not include_inactive_mailboxes)
        except Exception as e:
            print(f"Error in user_search: {e}")
            return []

    @kernel_function(
        description="""
        Useful for when you need to get a specific user preference data by their ID from Microsoft 365 Tenant Entra Directory.
        Returns detailed user information including display name, email, job title, department, and manager.
        """
    )
        
    async def get_user_preferences_by_user_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user to retrieve"]) -> Annotated[dict, "Returns detailed information about the specified user."]:
        self._log_function_call("get_user_preferences_by_user_id", user_id=user_id)
        self._send_friendly_notification("Getting user preferences...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_user_preferences_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_preferences_by_user_id: {e}")
            return {}

    @kernel_function(
        description="""
        Useful for when you need to get a specific user's mailbox settings by their ID from Microsoft 365 Tenant Entra Directory.
        Returns detailed mailbox settings including time zone, language, working hours, automatic replies, and other mailbox preferences.
        """
    )
        
    async def get_user_mailbox_settings_by_user_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose mailbox settings you want to retrieve"]) -> Annotated[dict, "Returns detailed mailbox settings for the specified user."]:
        self._log_function_call("get_user_mailbox_settings_by_user_id", user_id=user_id)
        self._send_friendly_notification("Getting user mailbox settings...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_user_mailbox_settings_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_mailbox_settings_by_user_id: {e}")
            return {}
        
    @kernel_function(
        description="""
        Useful for when you need to get a specific user by their ID from Microsoft 365 Tenant Entra Directory.
        Returns detailed user information including display name, email, job title, department, and manager.
        """
    )
        
    async def get_user_by_id(self, user_id: Annotated[str, "The unique user ID (GUID) of the user to retrieve"]) -> Annotated[dict, "Returns detailed information about the specified user."]:
        self._log_function_call("get_user_by_id", user_id=user_id)
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_user_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_by_id: {e}")
            return {}

    @kernel_function(
        description="""
        Useful for when you need to get the manager of a specific user from Microsoft 365 Tenant Entra Directory.
        Returns the manager's information including display name, email, job title, and department.
        """
    )
    async def get_user_manager(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose manager you want to retrieve"]) -> Annotated[dict, "Returns information about the user's manager."]:
        self._log_function_call("get_user_manager", user_id=user_id)
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_users_manager_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_user_manager: {e}")
            return {}

    @kernel_function(
        description="""
        Useful for when you need to get the direct reports (subordinates) of a specific user from Microsoft 365 Tenant Entra Directory.
        Returns a list of users who report directly to the specified user.
        """
    )
    async def get_direct_reports(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose direct reports you want to retrieve"]) -> Annotated[List[dict], "Returns a list of users who report directly to the specified user."]:
        self._log_function_call("get_direct_reports", user_id=user_id)
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        try:
            return await graph_operations.get_direct_reports_by_user_id(user_id.strip())
        except Exception as e:
            print(f"Error in get_direct_reports: {e}")
            return []

    @kernel_function(
        description="""
        Useful for when you need to get all users from Microsoft 365 Tenant Entra Directory.
        Automatically excludes users without active mailboxes by default, returning only users who can receive emails.
        Returns a list of all users with their basic information. Use max_results to limit the number of users returned.
        """
    )
    async def get_all_users(self, max_results: Annotated[int, "Maximum number of users to return (default: 100)"] = 100, include_inactive_mailboxes: Annotated[bool, "Set to true to include users without active mailboxes. Default is false."] = False) -> Annotated[List[dict], "Returns a list of users from the Microsoft 365 Tenant Entra Directory, excluding users without mailboxes by default."]:
        self._log_function_call("get_all_users", max_results=max_results, include_inactive_mailboxes=include_inactive_mailboxes)
        self._send_friendly_notification("Getting all users from your directory...")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_all_users(max_results, exclude_inactive_mailboxes=not include_inactive_mailboxes)
        except Exception as e:
            print(f"Error in get_all_users: {e}")
            return []

    @kernel_function(
        description="""
        Useful for when you need to get all users from a specific department in Microsoft 365 Tenant Entra Directory.
        Automatically excludes users without active mailboxes by default, returning only users who can receive emails.
        Returns a list of users from the specified department.

        When searching for departments, you need to be aware that the department names may vary.
        Before using this function, you can use the get_all_departments function to get a list of all unique departments in the tenant.
        You can then use the department names from that list to filter users.
        If you are not sure about the exact department name to choose, never guess, you will ask the user to clarify.
        """
    )
    async def get_users_by_department(self, department: Annotated[str, "The department name to filter users by"], max_results: Annotated[int, "Maximum number of users to return (default: 100)"] = 100, include_inactive_mailboxes: Annotated[bool, "Set to true to include users without active mailboxes. Default is false."] = False) -> Annotated[List[dict], "Returns a list of users from the specified department, excluding users without mailboxes by default."]:
        self._log_function_call("get_users_by_department", department=department, max_results=max_results, include_inactive_mailboxes=include_inactive_mailboxes)
        self._send_friendly_notification(f"Looking up users in the {department} department...")
        if not department or not department.strip(): raise ValueError("Error: department parameter is empty")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_users_by_department(department.strip(), max_results, exclude_inactive_mailboxes=not include_inactive_mailboxes)
        except Exception as e:
            print(f"Error in get_users_by_department: {e}")
            return []

    @kernel_function(
        description="""
        Useful for when you need to get all departments from Microsoft 365 Tenant Entra Directory.
        Returns a list of all unique departments found in the tenant.
        """
    )
    async def get_all_departments(self, max_results: Annotated[int, "Maximum number of users to scan for departments (default: 100)"] = 100) -> Annotated[List[str], "Returns a list of all unique departments in the Microsoft 365 Tenant Entra Directory."]:
        self._log_function_call("get_all_departments", max_results=max_results)
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_all_departments(max_results)
        except Exception as e:
            print(f"Error in get_all_departments: {e}")
            return []

    @kernel_function(
        description="""
        Useful for validating if a user has a valid mailbox before attempting calendar operations.
        This helps identify users whose mailboxes are inactive, soft-deleted, or hosted on-premise.
        Returns validation status and helpful diagnostic information.
        """
    )
    async def validate_user_mailbox(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose mailbox you want to validate"]) -> Annotated[dict, "Returns validation result with status and diagnostic information."]:
        self._log_function_call("validate_user_mailbox", user_id=user_id)
        self._send_friendly_notification("Validating user mailbox...")
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

    @kernel_function(
        description="""
        Useful for when you need to get calendar events for a specific user from Microsoft 365.
        You can optionally specify a date range to filter events. Dates should be in ISO 8601 format (e.g., '2025-07-01T00:00:00Z').
        Returns a list of calendar events including subject, start time, end time, location, and attendees.
        This function includes enhanced error handling for mailbox issues.
        """
    )
    async def get_calendar_events(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose calendar events you want to retrieve"], start_date: Annotated[str, "Optional start date for filtering events (ISO 8601 format, e.g., '2025-07-01T00:00:00Z')"] = None, end_date: Annotated[str, "Optional end date for filtering events (ISO 8601 format, e.g., '2025-07-31T23:59:59Z')"] = None) -> Annotated[List[dict], "Returns a list of calendar events for the specified user."]:
        self._log_function_call("get_calendar_events", user_id=user_id, start_date=start_date, end_date=end_date)
        self._send_friendly_notification("Retrieving calendar events...")
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

    @kernel_function(
        description="""
        Useful for creating calendar events in a user's Microsoft 365 calendar.
        You can specify the event subject, start/end times, location, and attendees.
        Times should be in ISO 8601 format (e.g., '2025-07-15T14:00:00Z').
        Attendees should be email addresses.
        """
    )
    async def create_calendar_event(self, user_id: Annotated[str, "The unique user ID (GUID) of the user in whose calendar the event will be created"], subject: Annotated[str, "The subject/title of the calendar event"], start: Annotated[str, "Start date and time of the event in ISO 8601 format (e.g., '2025-07-15T14:00:00Z')"], end: Annotated[str, "End date and time of the event in ISO 8601 format (e.g., '2025-07-15T15:00:00Z')"], location: Annotated[str, "Optional location for the event"] = None, attendees: Annotated[List[str], "Optional list of required attendee email addresses"] = None, optional_attendees: Annotated[List[str], "Optional list of optional attendee email addresses"] = None) -> Annotated[dict, "Returns information about the created calendar event."]:
        self._log_function_call("create_calendar_event", user_id=user_id, subject=subject, start=start, end=end, 
                              location=location, attendees=attendees, optional_attendees=optional_attendees)
        self._send_friendly_notification("Creating calendar event...")
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        if not subject or not subject.strip(): raise ValueError("Error: subject parameter is empty")
        if not start or not start.strip(): raise ValueError("Error: start parameter is empty")
        if not end or not end.strip(): raise ValueError("Error: end parameter is empty")
        try:
            return await graph_operations.create_calendar_event(
                user_id.strip(), subject.strip(), start.strip(), end.strip(),
                location, attendees, optional_attendees
            )
        except Exception as e:
            print(f"Error in create_calendar_event: {e}")
            return {}

    @kernel_function(
        description="""
        Useful for when you need to get the current date and time in ISO format.
        Returns the current datetime as an ISO 8601 formatted string.
        This is helpful for creating calendar events, filtering by date ranges, or any time-sensitive operations.
        """
    )
    async def get_current_datetime(self) -> Annotated[str, "Returns the current date and time in ISO 8601 format."]:
        self._log_function_call("get_current_datetime")
        try: return await graph_operations.get_current_datetime()
        except Exception as e:
            print(f"Error in get_current_datetime: {e}")
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()

