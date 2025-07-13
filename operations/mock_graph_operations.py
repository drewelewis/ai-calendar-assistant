"""
Mock Microsoft Graph Operations for testing purposes.
Use this when the real Microsoft Graph SDK is causing import issues.
"""

from datetime import datetime
import os
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)

class MockUser:
    """Mock user object that mimics Microsoft Graph User."""
    def __init__(self, user_id="mock-user-id", display_name="Mock User"):
        self.id = user_id
        self.display_name = display_name
        self.mail = f"{user_id}@example.com"
        self.given_name = "Mock"
        self.surname = "User"
        self.user_principal_name = f"{user_id}@example.com"
        self.job_title = "Mock Job Title"
        self.department = "Mock Department"

class MockEvent:
    """Mock event object that mimics Microsoft Graph Event."""
    def __init__(self, subject="Mock Event"):
        self.id = "mock-event-id"
        self.subject = subject
        self.start = {"dateTime": "2025-07-15T10:00:00Z"}
        self.end = {"dateTime": "2025-07-15T11:00:00Z"}
        self.location = {"displayName": "Mock Location"}

class GraphOperations:
    """Mock GraphOperations class for testing."""
    
    def __init__(self, user_response_fields=None, calendar_response_fields=None):
        """Initialize mock graph operations."""
        self.user_response_fields = user_response_fields or ["id", "displayName", "mail"]
        self.calendar_response_fields = calendar_response_fields or ["subject", "start", "end"]
        print("🔄 Using MOCK Microsoft Graph Operations (no real API calls)")
        print("💡 Set up real Microsoft Graph credentials to use actual functionality")

    def get_current_datetime(self) -> str:
        """Get current datetime in ISO format."""
        return datetime.now().isoformat() + "Z"

    async def get_user_by_user_id(self, user_id: str):
        """Mock get user by ID."""
        print(f"🎭 MOCK: Getting user by ID: {user_id}")
        return MockUser(user_id, f"Mock User {user_id}")

    async def get_users_manager_by_user_id(self, user_id: str):
        """Mock get user's manager."""
        print(f"🎭 MOCK: Getting manager for user: {user_id}")
        return MockUser(f"manager-{user_id}", f"Manager of {user_id}")

    async def get_direct_reports_by_user_id(self, user_id: str) -> List:
        """Mock get direct reports."""
        print(f"🎭 MOCK: Getting direct reports for user: {user_id}")
        return [MockUser(f"report-1-{user_id}", "Direct Report 1")]

    async def get_all_users(self, max_results=100) -> List:
        """Mock get all users."""
        print(f"🎭 MOCK: Getting all users (max: {max_results})")
        return [MockUser(f"user-{i}", f"User {i}") for i in range(min(3, max_results))]

    async def get_all_departments(self, max_results=100) -> List[str]:
        """Mock get all departments."""
        print(f"🎭 MOCK: Getting all departments (max: {max_results})")
        return ["Engineering", "Sales", "Marketing"]

    async def get_users_by_department(self, department: str, max_results=100) -> List:
        """Mock get users by department."""
        print(f"🎭 MOCK: Getting users in department: {department} (max: {max_results})")
        return [MockUser(f"user-{department}-{i}", f"User {i} from {department}") for i in range(min(2, max_results))]

    async def search_users(self, filter_str: str, max_results=100) -> List:
        """Mock search users."""
        print(f"🎭 MOCK: Searching users with filter: {filter_str} (max: {max_results})")
        return [MockUser(f"search-{i}", f"Search Result {i}") for i in range(min(2, max_results))]

    async def get_calendar_events_by_user_id(self, user_id: str, start_date: str = None, end_date: str = None) -> List:
        """Mock get calendar events."""
        print(f"🎭 MOCK: Getting calendar events for user: {user_id}")
        if start_date:
            print(f"      Start date: {start_date}")
        if end_date:
            print(f"      End date: {end_date}")
        return [MockEvent("Mock Meeting 1"), MockEvent("Mock Meeting 2")]

    async def create_calendar_event(self, user_id: str, subject: str, start: str, end: str, 
                                  location: str = None, attendees: List[str] = None, 
                                  optional_attendees: List[str] = None):
        """Mock create calendar event."""
        print(f"🎭 MOCK: Creating calendar event for user: {user_id}")
        print(f"      Subject: {subject}")
        print(f"      Start: {start}")
        print(f"      End: {end}")
        if location:
            print(f"      Location: {location}")
        if attendees:
            print(f"      Attendees: {attendees}")
        return MockEvent(subject)
