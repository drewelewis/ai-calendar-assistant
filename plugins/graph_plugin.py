from datetime import date
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

graph_operations = GraphOperations(
    user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
    calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
)
max_results = 100

class GraphPlugin:
    def __init__(self, debug=False):
        self.debug = debug

    # Helper method to log function calls if debug is enabled
    def _log_function_call(self, function_name, **kwargs):
        if self.debug:
            params_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
            print(f"DEBUG: Calling kernel function '{function_name}' with parameters: {params_str}")

    @kernel_function(
        description="""
        Useful for when you need to find users in Microsoft 365 Tenant Entra Directory.
        OData (Open Data Protocol) query language can be used to filter and search for users.
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
    async def user_search(self, filter: Annotated[str, "User search filter parameter. Use OData query syntax to filter users."]) -> Annotated[List[dict], "Returns a list of users matching the filter criteria."]:
        self._log_function_call("user_search", filter=filter)
        if not filter: raise ValueError("Error: filter parameter is empty")
        try:
            # Using a synchronous approach here
            return await graph_operations.search_users(filter, max_results=max_results)
        except Exception as e:
            print(f"Error in user_search: {e}")
            return []

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
        Returns a list of all users with their basic information. Use max_results to limit the number of users returned.
        """
    )
    async def get_all_users(self, max_results: Annotated[int, "Maximum number of users to return (default: 100)"] = 100) -> Annotated[List[dict], "Returns a list of users from the Microsoft 365 Tenant Entra Directory."]:
        self._log_function_call("get_all_users", max_results=max_results)
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_all_users(max_results)
        except Exception as e:
            print(f"Error in get_all_users: {e}")
            return []

    @kernel_function(
        description="""
        Useful for when you need to get all users from a specific department in Microsoft 365 Tenant Entra Directory.
        Returns a list of users from the specified department.

        When searching for departments, you need to be aware that the department names may vary.
        Before using this function, you can use the get_all_departments function to get a list of all unique departments in the tenant.
        You can then use the department names from that list to filter users.
        If you are not sure about the exact department name to choose, never guess, you will ask the user to clarify.
        """
    )
    async def get_users_by_department(self, department: Annotated[str, "The department name to filter users by"], max_results: Annotated[int, "Maximum number of users to return (default: 100)"] = 100) -> Annotated[List[dict], "Returns a list of users from the specified department."]:
        self._log_function_call("get_users_by_department", department=department, max_results=max_results)
        if not department or not department.strip(): raise ValueError("Error: department parameter is empty")
        if max_results <= 0: raise ValueError("Error: max_results must be greater than 0")
        if max_results > 1000: raise ValueError("Error: max_results cannot exceed 1000")
        try:
            return await graph_operations.get_users_by_department(department.strip(), max_results)
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
        Useful for when you need to get calendar events for a specific user from Microsoft 365.
        You can optionally specify a date range to filter events. Dates should be in ISO 8601 format (e.g., '2025-07-01T00:00:00Z').
        Returns a list of calendar events including subject, start time, end time, location, and attendees.
        """
    )
    async def get_calendar_events(self, user_id: Annotated[str, "The unique user ID (GUID) of the user whose calendar events you want to retrieve"], start_date: Annotated[Optional[date], "Optional start date for filtering events (ISO 8601 format, e.g., '2025-07-01T00:00:00Z')"] = None, end_date: Annotated[Optional[date], "Optional end date for filtering events (ISO 8601 format, e.g., '2025-07-31T23:59:59Z')"] = None) -> Annotated[List[dict], "Returns a list of calendar events for the specified user."]:
        self._log_function_call("get_calendar_events", user_id=user_id, start_date=start_date, end_date=end_date)
        if not user_id or not user_id.strip(): raise ValueError("Error: user_id parameter is empty")
        if start_date and not start_date: start_date = None
        if end_date and not end_date: end_date = None
        try:
            return await graph_operations.get_calendar_events_by_user_id(user_id.strip(), start_date, end_date)
        except Exception as e:
            print(f"Error in get_calendar_events: {e}")
            return []

    @kernel_function(
        description="""
        Useful for creating calendar events in a user's Microsoft 365 calendar.
        You can specify the event subject, start/end times, location, and attendees.
        Times should be in ISO 8601 format (e.g., '2025-07-15T14:00:00Z').
        Attendees should be email addresses.
        """
    )
    async def create_calendar_event(self, user_id: Annotated[str, "The unique user ID (GUID) of the user in whose calendar the event will be created"], subject: Annotated[str, "The subject/title of the calendar event"], start: Annotated[str, "Start date and time of the event in ISO 8601 format (e.g., '2025-07-15T14:00:00Z')"], end: Annotated[str, "End date and time of the event in ISO 8601 format (e.g., '2025-07-15T15:00:00Z')"], location: Annotated[Optional[str], "Optional location for the event"] = None, attendees: Annotated[Optional[List[str]], "Optional list of required attendee email addresses"] = None, optional_attendees: Annotated[Optional[List[str]], "Optional list of optional attendee email addresses"] = None) -> Annotated[dict, "Returns information about the created calendar event."]:
        self._log_function_call("create_calendar_event", user_id=user_id, subject=subject, start=start, end=end, 
                              location=location, attendees=attendees, optional_attendees=optional_attendees)
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

