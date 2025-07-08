import os
import asyncio
from typing import List, Optional, Type
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv(override=True)

from operations.graph_operations import GraphOperations

graph_operations=GraphOperations(
    user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
    calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
)
max_results=100
class GraphTools():

    class UserSearch(BaseTool):
        name: str = "UserSearch"
        description: str = """
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
        """.strip()
        return_direct: bool = False

        class UserSearchInputModel(BaseModel):
            filter: str = Field(description="User search filter parameter. Use OData query syntax to filter users.")

            # Validation method to check parameter input from agent
            @field_validator("filter")
            def validate_query_param(filter):
                if not filter:
                    raise ValueError("UserSearchInputModel error: filter parameter is empty")
                else:
                    return filter

        args_schema: Optional[ArgsSchema] = UserSearchInputModel

        def _run(self, filter: str) -> List[dict]:
            """Synchronous version - runs the async method in an event loop"""
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we need to handle this differently
                    # This is a fallback that shouldn't normally be used in async context
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.search_users(filter,max_results=max_results))
                        return future.result()
                else:
                    # If no loop is running, we can use asyncio.run
                    return asyncio.run(graph_operations.search_users(filter,max_results=max_results))
            except RuntimeError:
                # If we can't get a loop, create a new one
                return asyncio.run(graph_operations.search_users(filter,max_results=max_results))

        async def _arun(self, filter: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> List[dict]:
            """Async version - preferred when in async context"""
            return await graph_operations.search_users(filter, max_results=max_results)

    class GetUserById(BaseTool):
        name: str = "GetUserById"
        description: str = """
           Useful for when you need to get a specific user by their ID from Microsoft 365 Tenant Entra Directory.
           Returns detailed user information including display name, email, job title, department, and manager.
        """.strip()
        return_direct: bool = False

        class GetUserByIdInputModel(BaseModel):
            user_id: str = Field(description="The unique user ID (GUID) of the user to retrieve")

            @field_validator("user_id")
            def validate_user_id(cls, user_id):
                if not user_id or not user_id.strip():
                    raise ValueError("GetUserById error: user_id parameter is empty")
                return user_id.strip()

        args_schema: Optional[ArgsSchema] = GetUserByIdInputModel

        def _run(self, user_id: str) -> dict:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_user_by_user_id(user_id))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_user_by_user_id(user_id))
            except RuntimeError:
                return asyncio.run(graph_operations.get_user_by_user_id(user_id))

        async def _arun(self, user_id: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> dict:
            """Async version"""
            return await graph_operations.get_user_by_user_id(user_id)

    class GetUserManager(BaseTool):
        name: str = "GetUserManager"
        description: str = """
           Useful for when you need to get the manager of a specific user from Microsoft 365 Tenant Entra Directory.
           Returns the manager's information including display name, email, job title, and department.
        """.strip()
        return_direct: bool = False

        class GetUserManagerInputModel(BaseModel):
            user_id: str = Field(description="The unique user ID (GUID) of the user whose manager you want to retrieve")

            @field_validator("user_id")
            def validate_user_id(cls, user_id):
                if not user_id or not user_id.strip():
                    raise ValueError("GetUserManager error: user_id parameter is empty")
                return user_id.strip()

        args_schema: Optional[ArgsSchema] = GetUserManagerInputModel

        def _run(self, user_id: str) -> dict:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_users_manager_by_user_id(user_id))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_users_manager_by_user_id(user_id))
            except RuntimeError:
                return asyncio.run(graph_operations.get_users_manager_by_user_id(user_id))

        async def _arun(self, user_id: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> dict:
            """Async version"""
            return await graph_operations.get_users_manager_by_user_id(user_id)

    class GetDirectReports(BaseTool):
        name: str = "GetDirectReports"
        description: str = """
           Useful for when you need to get the direct reports (subordinates) of a specific user from Microsoft 365 Tenant Entra Directory.
           Returns a list of users who report directly to the specified user.
        """.strip()
        return_direct: bool = False

        class GetDirectReportsInputModel(BaseModel):
            user_id: str = Field(description="The unique user ID (GUID) of the user whose direct reports you want to retrieve")

            @field_validator("user_id")
            def validate_user_id(cls, user_id):
                if not user_id or not user_id.strip():
                    raise ValueError("GetDirectReports error: user_id parameter is empty")
                return user_id.strip()

        args_schema: Optional[ArgsSchema] = GetDirectReportsInputModel

        def _run(self, user_id: str) -> List[dict]:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_direct_reports_by_user_id(user_id))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_direct_reports_by_user_id(user_id))
            except RuntimeError:
                return asyncio.run(graph_operations.get_direct_reports_by_user_id(user_id))

        async def _arun(self, user_id: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> List[dict]:
            """Async version"""
            return await graph_operations.get_direct_reports_by_user_id(user_id)

    class GetAllUsers(BaseTool):
        name: str = "GetAllUsers"
        description: str = """
           Useful for when you need to get all users from Microsoft 365 Tenant Entra Directory.
           Returns a list of all users with their basic information. Use max_results to limit the number of users returned.
        """.strip()
        return_direct: bool = False

        class GetAllUsersInputModel(BaseModel):
            max_results: int = Field(default=100, description="Maximum number of users to return (default: 100)")

            @field_validator("max_results")
            def validate_max_results(cls, max_results):
                if max_results <= 0:
                    raise ValueError("GetAllUsers error: max_results must be greater than 0")
                if max_results > 1000:
                    raise ValueError("GetAllUsers error: max_results cannot exceed 1000")
                return max_results

        args_schema: Optional[ArgsSchema] = GetAllUsersInputModel

        def _run(self, max_results: int = 100) -> List[dict]:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_all_users(max_results))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_all_users(max_results))
            except RuntimeError:
                return asyncio.run(graph_operations.get_all_users(max_results))

        async def _arun(self, max_results: int = 100, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> List[dict]:
            """Async version"""
            return await graph_operations.get_all_users(max_results)

    class GetUsersByDepartment(BaseTool):
        name: str = "GetUsersByDepartment"
        description: str = """
           Useful for when you need to get all users from a specific department in Microsoft 365 Tenant Entra Directory.
           Returns a list of users from the specified department.
        """.strip()
        return_direct: bool = False

        class GetUsersByDepartmentInputModel(BaseModel):
            department: str = Field(description="The department name to filter users by")
            max_results: int = Field(default=100, description="Maximum number of users to return (default: 100)")

            @field_validator("department")
            def validate_department(cls, department):
                if not department or not department.strip():
                    raise ValueError("GetUsersByDepartment error: department parameter is empty")
                return department.strip()

            @field_validator("max_results")
            def validate_max_results(cls, max_results):
                if max_results <= 0:
                    raise ValueError("GetUsersByDepartment error: max_results must be greater than 0")
                if max_results > 1000:
                    raise ValueError("GetUsersByDepartment error: max_results cannot exceed 1000")
                return max_results

        args_schema: Optional[ArgsSchema] = GetUsersByDepartmentInputModel

        def _run(self, department: str, max_results: int = 100) -> List[dict]:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_users_by_department(department, max_results))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_users_by_department(department, max_results))
            except RuntimeError:
                return asyncio.run(graph_operations.get_users_by_department(department, max_results))

        async def _arun(self, department: str, max_results: int = 100, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> List[dict]:
            """Async version"""
            return await graph_operations.get_users_by_department(department, max_results)

    
    class GetAllDepartments(BaseTool):
        name: str = "GetAllDepartments"
        description: str = """
           Useful for when you need to get all departments from Microsoft 365 Tenant Entra Directory.
           Returns a list of all unique departments found in the tenant.
        """.strip()
        return_direct: bool = False

        class GetAllDepartmentsInputModel(BaseModel):
            max_results: int = Field(default=100, description="Maximum number of users to scan for departments (default: 100)")

            @field_validator("max_results")
            def validate_max_results(cls, max_results):
                if max_results <= 0:
                    raise ValueError("GetAllDepartments error: max_results must be greater than 0")
                if max_results > 1000:
                    raise ValueError("GetAllDepartments error: max_results cannot exceed 1000")
                return max_results

        args_schema: Optional[ArgsSchema] = GetAllDepartmentsInputModel

        def _run(self, max_results: int = 100) -> List[str]:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_all_departments(max_results))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_all_departments(max_results))
            except RuntimeError:
                return asyncio.run(graph_operations.get_all_departments(max_results))

        async def _arun(self, max_results: int = 100, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> List[str]:
            """Async version"""
            return await graph_operations.get_all_departments(max_results)

    class GetCalendarEvents(BaseTool):
        name: str = "GetCalendarEvents"
        description: str = """
           Useful for when you need to get calendar events for a specific user from Microsoft 365.
           You can optionally specify a date range to filter events. Dates should be in ISO 8601 format (e.g., '2025-07-01T00:00:00Z').
           Returns a list of calendar events including subject, start time, end time, location, and attendees.
        """.strip()
        return_direct: bool = False

        class GetCalendarEventsInputModel(BaseModel):
            user_id: str = Field(description="The unique user ID (GUID) of the user whose calendar events you want to retrieve")
            start_date: Optional[str] = Field(default=None, description="Optional start date for filtering events (ISO 8601 format, e.g., '2025-07-01T00:00:00Z')")
            end_date: Optional[str] = Field(default=None, description="Optional end date for filtering events (ISO 8601 format, e.g., '2025-07-31T23:59:59Z')")

            @field_validator("user_id")
            def validate_user_id(cls, user_id):
                if not user_id or not user_id.strip():
                    raise ValueError("GetCalendarEvents error: user_id parameter is empty")
                return user_id.strip()

            @field_validator("start_date")
            def validate_start_date(cls, start_date):
                if start_date and not start_date.strip():
                    return None
                return start_date

            @field_validator("end_date")
            def validate_end_date(cls, end_date):
                if end_date and not end_date.strip():
                    return None
                return end_date

        args_schema: Optional[ArgsSchema] = GetCalendarEventsInputModel

        def _run(self, user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[dict]:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.get_calendar_events_by_user_id(user_id, start_date, end_date))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.get_calendar_events_by_user_id(user_id, start_date, end_date))
            except RuntimeError:
                return asyncio.run(graph_operations.get_calendar_events_by_user_id(user_id, start_date, end_date))

        async def _arun(self, user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> List[dict]:
            """Async version"""
            return await graph_operations.get_calendar_events_by_user_id(user_id, start_date, end_date)

    class CreateCalendarEvent(BaseTool):
        name: str = "CreateCalendarEvent"
        description: str = """
           Useful for creating calendar events in a user's Microsoft 365 calendar.
           You can specify the event subject, start/end times, location, and attendees.
           Times should be in ISO 8601 format (e.g., '2025-07-15T14:00:00Z').
           Attendees should be email addresses.
        """.strip()
        return_direct: bool = False

        class CreateCalendarEventInputModel(BaseModel):
            user_id: str = Field(description="The unique user ID (GUID) of the user in whose calendar the event will be created")
            subject: str = Field(description="The subject/title of the calendar event")
            start: str = Field(description="Start date and time of the event in ISO 8601 format (e.g., '2025-07-15T14:00:00Z')")
            end: str = Field(description="End date and time of the event in ISO 8601 format (e.g., '2025-07-15T15:00:00Z')")
            location: Optional[str] = Field(default=None, description="Optional location for the event")
            attendees: Optional[List[str]] = Field(default=None, description="Optional list of required attendee email addresses")
            optional_attendees: Optional[List[str]] = Field(default=None, description="Optional list of optional attendee email addresses")

            @field_validator("user_id")
            def validate_user_id(cls, user_id):
                if not user_id or not user_id.strip():
                    raise ValueError("CreateCalendarEvent error: user_id parameter is empty")
                return user_id.strip()

            @field_validator("subject")
            def validate_subject(cls, subject):
                if not subject or not subject.strip():
                    raise ValueError("CreateCalendarEvent error: subject parameter is empty")
                return subject.strip()

            @field_validator("start")
            def validate_start(cls, start):
                if not start or not start.strip():
                    raise ValueError("CreateCalendarEvent error: start parameter is empty")
                return start.strip()

            @field_validator("end")
            def validate_end(cls, end):
                if not end or not end.strip():
                    raise ValueError("CreateCalendarEvent error: end parameter is empty")
                return end.strip()

        args_schema: Optional[ArgsSchema] = CreateCalendarEventInputModel

        def _run(self, user_id: str, subject: str, start: str, end: str, location: Optional[str] = None, 
                attendees: Optional[List[str]] = None, optional_attendees: Optional[List[str]] = None) -> dict:
            """Synchronous version"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, graph_operations.create_calendar_event(
                            user_id, subject, start, end, location, attendees, optional_attendees))
                        return future.result()
                else:
                    return asyncio.run(graph_operations.create_calendar_event(
                        user_id, subject, start, end, location, attendees, optional_attendees))
            except RuntimeError:
                return asyncio.run(graph_operations.create_calendar_event(
                    user_id, subject, start, end, location, attendees, optional_attendees))

        async def _arun(self, user_id: str, subject: str, start: str, end: str, location: Optional[str] = None, 
                       attendees: Optional[List[str]] = None, optional_attendees: Optional[List[str]] = None,
                       run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> dict:
            """Async version"""
            return await graph_operations.create_calendar_event(
                user_id, subject, start, end, location, attendees, optional_attendees)

    class GetCurrentDateTime(BaseTool):
        name: str = "GetCurrentDateTime"
        description: str = """
           Useful for when you need to get the current date and time in ISO format.
           Returns the current datetime as an ISO 8601 formatted string.
           This is helpful for creating calendar events, filtering by date ranges, or any time-sensitive operations.
        """.strip()
        return_direct: bool = False

        class GetCurrentDateTimeInputModel(BaseModel):
            # No input parameters needed for getting current datetime
            pass

        args_schema: Optional[ArgsSchema] = GetCurrentDateTimeInputModel

        def _run(self) -> str:
            """Synchronous version"""
            return graph_operations.get_current_datetime()

        async def _arun(self, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
            """Async version"""
            return graph_operations.get_current_datetime()

    # Init above tools and make available
    def __init__(self) -> None:
        self._tools = [
            self.UserSearch(),
            self.GetUserById(),
            self.GetUserManager(),
            self.GetDirectReports(),
            self.GetAllUsers(),
            self.GetUsersByDepartment(),
            self.GetAllDepartments(),
            self.GetCalendarEvents(),
            self.CreateCalendarEvent(),
            self.GetCurrentDateTime()
        ]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools
