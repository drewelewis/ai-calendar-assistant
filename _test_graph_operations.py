#!/usr/bin/env python3
"""
Microsoft Graph Plugin Test Suite
=================================

This file contains comprehensive test commands for all Graph plugin functionality.
Run individual test functions or the entire suite to validate your Microsoft Graph integration.

✨ NEW FEATURES:
- Randomized event scheduling to avoid conflicts
- Multiple random events creation for stress testing
- Unique event IDs and subjects for each test run
- Configurable time ranges for event scheduling
- Conference room booking and hybrid meeting tests

Usage:
    python __test_graph_operations.py

Requirements:
    - Valid Microsoft Graph authentication
    - Proper application permissions
    - Active Microsoft 365 tenant

Event Creation Features:
    - Events are scheduled at random future times on weekdays only (Monday-Friday)
    - Business hours scheduling (9 AM - 5 PM) for professional environments
    - Start times use clean 15-minute intervals (00, 15, 30, 45)
    - Durations vary randomly (30min - 2hrs)
    - Unique subjects with random IDs to avoid duplicates
    - Multiple event types (meetings, reviews, calls, etc.)
    - Automatic fallback to next Monday if no weekday slots found
    - Conference room integration with availability checking
    - Hybrid meeting support (Teams + physical room)
"""

import asyncio
import json
import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Import your Graph plugin and operations
try:
    from plugins.graph_plugin import GraphPlugin
    from operations.graph_operations import GraphOperations
    print("✅ Successfully imported Graph components")
except ImportError as e:
    print(f"❌ Failed to import Graph components: {e}")
    print("This could be due to missing dependencies like 'semantic_kernel'")
    print("You can install missing dependencies with: pip install semantic-kernel")
    print("Or run: pip install -r requirements.txt")
    print("Make sure you're running from the project root directory")
    exit(1)


class GraphTestSuite:
    """Comprehensive test suite for Microsoft Graph plugin functionality."""
    
    def __init__(self, debug: bool = True):
        """Initialize the test suite with optional debug logging."""
        self.debug = debug
        self.plugin = GraphPlugin(debug=debug, session_id="test-session")
        self.test_results = []
        self.test_user_id = None
        self.test_room_id = None
    
    def _generate_random_future_time(self, min_hours_ahead: int = 2, max_hours_ahead: int = 168) -> tuple:
        """
        Generate a random future start and end time for test events on weekdays only.
        
        Args:
            min_hours_ahead: Minimum hours from now (default: 2 hours)
            max_hours_ahead: Maximum hours from now (default: 168 hours = 1 week)
            
        Returns:
            tuple: (start_time_iso, end_time_iso) in ISO 8601 format
        """
        max_attempts = 50  # Prevent infinite loop
        attempt = 0
        
        while attempt < max_attempts:
            # Generate random hour offset
            hours_ahead = random.randint(min_hours_ahead, max_hours_ahead)
            
            # Create potential start time
            potential_start = datetime.now() + timedelta(hours=hours_ahead)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if potential_start.weekday() < 5:  # 0-4 are Monday-Friday
                # Generate business hour (9 AM to 5 PM for professional scheduling)
                business_hour = random.randint(9, 16)  # 9 AM to 4 PM (so meetings can end by 6 PM)
                
                # Generate random minute (0, 15, 30, 45 for cleaner scheduling)
                random_minute = random.choice([0, 15, 30, 45])
                
                # Generate random duration between 30 minutes and 2 hours
                duration_minutes = random.choice([30, 45, 60, 90, 120])
                
                # Create start time with business hours
                start_time = potential_start.replace(
                    hour=business_hour, 
                    minute=random_minute, 
                    second=0, 
                    microsecond=0
                )
                
                # Create end time
                end_time = start_time + timedelta(minutes=duration_minutes)
                
                # Make sure end time doesn't go past 6 PM (18:00)
                if end_time.hour >= 18:
                    # Adjust to end by 6 PM
                    end_time = start_time.replace(hour=17, minute=45)  # 5:45 PM
                    # Recalculate duration to ensure minimum 30 minutes
                    if (end_time - start_time).total_seconds() < 1800:  # Less than 30 minutes
                        start_time = end_time - timedelta(minutes=30)# Adjust to end by 6 PM
                    end_time = start_time.replace(hour=17, minute=45)  # 5:45 PM
                    # Recalculate duration to ensure minimum 30 minutes
                    if (end_time - start_time).total_seconds() < 1800:  # Less than 30 minutes
                        start_time = end_time - timedelta(minutes=30)
                
                # Format as ISO 8601
                start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                
                return start_iso, end_iso
            
            attempt += 1
        
        # Fallback: if we can't find a weekday, use next Monday
        now = datetime.now()
        days_until_monday = (7 - now.weekday()) % 7  # Days until next Monday
        if days_until_monday == 0:  # If today is Monday
            days_until_monday = 7  # Use next Monday
        
        next_monday = now + timedelta(days=days_until_monday)
        start_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)  # 10 AM Monday
        end_time = start_time + timedelta(hours=1)  # 1 hour meeting
        
        start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        return start_iso, end_iso
        
    def log_test(self, test_name: str, success: bool, result: Any = None, error: str = None):
        """Log test results for summary reporting."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if self.debug and result:
            # Handle different result types for logging
            if hasattr(result, '__dict__'):
                # For objects with attributes, show a summary
                result_str = f"{type(result).__name__} object"
                if hasattr(result, 'id'):
                    result_str += f" (id: {getattr(result, 'id', 'N/A')})"
            else:
                # For dicts, lists, and primitives, use JSON serialization
                try:
                    result_str = json.dumps(result, indent=2, default=str)[:200] + "..."
                except:
                    result_str = str(result)[:200] + "..."
            
            print(f"   Result: {result_str}")
        
        if error:
            print(f"   Error: {error}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "result": str(result) if result else None,  # Convert to string for JSON serialization
            "error": error
        })
        print("-" * 50)

    # =============================================================================
    # SYSTEM & TIME TESTS
    # =============================================================================
    
    async def test_get_current_datetime(self):
        """Test: Get current date/time for reference."""
        try:
            result = await self.plugin.get_current_datetime()
            success = result and isinstance(result, str)
            self.log_test("get_current_datetime", success, result)
            return result
        except Exception as e:
            self.log_test("get_current_datetime", False, error=str(e))
            return None

    # =============================================================================
    # USER DISCOVERY & SEARCH TESTS
    # =============================================================================
    
    async def test_user_search_basic(self):
        """Test: Basic user search functionality."""
        test_filters = [
            "jobTitle eq 'Manager'",
            "jobTitle eq 'CEO'",
            "contains(jobTitle,'Director')",
            "startswith(displayName,'A')",  # Find users starting with 'A'
        ]
        
        for filter_query in test_filters:
            try:
                result = await self.plugin.user_search(filter_query)
                success = isinstance(result, list)
                self.log_test(f"user_search: {filter_query}", success, f"Found {len(result)} users")
                
                # Store first user ID for later tests - handle both dict and User object types
                if success and result and not self.test_user_id:
                    first_user = result[0]
                    if isinstance(first_user, dict):
                        self.test_user_id = first_user.get('id')
                    elif hasattr(first_user, 'id'):  # User object
                        self.test_user_id = first_user.id
                    
            except Exception as e:
                self.log_test(f"user_search: {filter_query}", False, error=str(e))

    async def test_user_search_complex(self):
        """Test: Complex user search with multiple criteria."""
        complex_filters = [
            "department eq 'Engineering' and jobTitle eq 'Manager'",
            "startswith(displayName,'John') or startswith(displayName,'Jane')",
        ]
        
        for filter_query in complex_filters:
            try:
                result = await self.plugin.user_search(filter_query)
                success = isinstance(result, list)
                self.log_test(f"user_search_complex: {filter_query}", success, f"Found {len(result)} users")
            except Exception as e:
                self.log_test(f"user_search_complex: {filter_query}", False, error=str(e))

    async def test_get_all_users(self):
        """Test: Get all users with different parameters."""
        test_cases = [
            {"max_results": 10, "include_inactive_mailboxes": False},
            {"max_results": 5, "include_inactive_mailboxes": True},
        ]
        
        for params in test_cases:
            try:
                result = await self.plugin.get_all_users(**params)
                success = isinstance(result, list)
                self.log_test(f"get_all_users({params})", success, f"Found {len(result)} users")
                
                # Store first user ID for later tests - handle both dict and User object types
                if success and result and not self.test_user_id:
                    first_user = result[0]
                    if isinstance(first_user, dict):
                        self.test_user_id = first_user.get('id')
                    elif hasattr(first_user, 'id'):  # User object
                        self.test_user_id = first_user.id
                    
            except Exception as e:
                self.log_test(f"get_all_users({params})", False, error=str(e))

    # =============================================================================
    # DEPARTMENT TESTS
    # =============================================================================
    
    async def test_get_all_departments(self):
        """Test: Get all departments in the organization."""
        try:
            result = await self.plugin.get_all_departments(max_results=100)
            success = isinstance(result, list)
            self.log_test("get_all_departments", success, f"Found departments: {result}")
            return result
        except Exception as e:
            self.log_test("get_all_departments", False, error=str(e))
            return []

    async def test_get_users_by_department(self):
        """Test: Get users by specific department."""
        # First get available departments
        departments = await self.test_get_all_departments()
        
        if departments:
            # Test with first few departments
            for dept in departments[:3]:
                try:
                    result = await self.plugin.get_users_by_department(
                        department=dept, 
                        max_results=10
                    )
                    success = isinstance(result, list)
                    self.log_test(f"get_users_by_department: {dept}", success, f"Found {len(result)} users")
                except Exception as e:
                    self.log_test(f"get_users_by_department: {dept}", False, error=str(e))

    # =============================================================================
    # INDIVIDUAL USER INFORMATION TESTS
    # =============================================================================
    
    async def test_user_lookup_functions(self):
        """Test: User lookup functions (requires user ID from previous tests)."""
        if not self.test_user_id:
            self.log_test("user_lookup_functions", False, error="No test user ID available")
            return
        
        # Test get_user_by_id
        try:
            result = await self.plugin.get_user_by_id(self.test_user_id)
            
            # Handle both dict and User object types
            if isinstance(result, dict):
                success = bool(result.get('id'))
                test_email = result.get('mail') or result.get('userPrincipalName')
            elif hasattr(result, 'id'):  # User object from Microsoft Graph SDK
                success = bool(result.id)
                
                # Try multiple possible email attribute names
                test_email = None
                email_attrs = ['mail', 'userprincipalname', 'user_principal_name', 'email']
                for attr in email_attrs:
                    email_value = getattr(result, attr, None)
                    if email_value:
                        test_email = email_value
                        break
                
                # Debug: Print available attributes if no email found
                if not test_email and self.debug:
                    available_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
                    print(f"   Debug: User object attributes: {available_attrs}")
                    
            else:
                success = False
                test_email = None
                
            self.log_test("get_user_by_id", success, f"User type: {type(result).__name__}")
            
            # Try to get email for email lookup test
            if test_email:
                try:
                    result2 = await self.plugin.get_user_by_email(test_email)
                    
                    # Handle both dict and User object types for email result
                    if isinstance(result2, dict):
                        success2 = bool(result2.get('id'))
                    elif hasattr(result2, 'id'):  # User object
                        success2 = bool(result2.id)
                    else:
                        success2 = False
                        
                    self.log_test("get_user_by_email", success2, f"User type: {type(result2).__name__}")
                except Exception as e:
                    self.log_test("get_user_by_email", False, error=str(e))
            else:
                self.log_test("get_user_by_email", False, error="No email address found for lookup test")
                    
        except Exception as e:
            self.log_test("get_user_by_id", False, error=str(e))

    async def test_user_preferences_and_mailbox(self):
        """Test: User preferences and mailbox settings."""
        if not self.test_user_id:
            self.log_test("user_preferences_and_mailbox", False, error="No test user ID available")
            return
        
        # Test user preferences
        try:
            result = await self.plugin.get_user_preferences_by_user_id(self.test_user_id)
            success = isinstance(result, dict)
            self.log_test("get_user_preferences_by_user_id", success, result)
        except Exception as e:
            self.log_test("get_user_preferences_by_user_id", False, error=str(e))
        
        # Test mailbox settings
        try:
            result = await self.plugin.get_user_mailbox_settings_by_user_id(self.test_user_id)
            success = isinstance(result, dict)
            self.log_test("get_user_mailbox_settings_by_user_id", success, result)
        except Exception as e:
            self.log_test("get_user_mailbox_settings_by_user_id", False, error=str(e))
        
        # Test location
        try:
            result = await self.plugin.get_users_city_state_zipcode_by_user_id(self.test_user_id)
            success = isinstance(result, dict)
            self.log_test("get_users_city_state_zipcode_by_user_id", success, result)
        except Exception as e:
            self.log_test("get_users_city_state_zipcode_by_user_id", False, error=str(e))

    async def test_organizational_hierarchy(self):
        """Test: Organizational hierarchy functions."""
        if not self.test_user_id:
            self.log_test("organizational_hierarchy", False, error="No test user ID available")
            return
        
        # Test manager lookup
        try:
            result = await self.plugin.get_users_manager_by_user_id(self.test_user_id)
            success = isinstance(result, dict)
            self.log_test("get_users_manager_by_user_id", success, result)
        except Exception as e:
            self.log_test("get_users_manager_by_user_id", False, error=str(e))
        
        # Test direct reports
        try:
            result = await self.plugin.get_users_direct_reports(self.test_user_id)
            success = isinstance(result, list)
            self.log_test("get_users_direct_reports", success, f"Found {len(result)} direct reports")
        except Exception as e:
            self.log_test("get_users_direct_reports", False, error=str(e))

    # =============================================================================
    # CONFERENCE ROOM TESTS
    # =============================================================================
    
    async def test_conference_room_discovery(self):
        """Test: Conference room discovery functions."""
        try:
            result = await self.plugin.get_all_conference_rooms(max_results=20)
            success = isinstance(result, list)
            self.log_test("get_all_conference_rooms", success, f"Found {len(result)} rooms")
            
            # Store first room ID for detailed tests
            if success and result:
                # Look for room with ID field
                for room in result:
                    if isinstance(room, dict) and room.get('id'):
                        self.test_room_id = room['id']
                        break
                        
            return result
        except Exception as e:
            self.log_test("get_all_conference_rooms", False, error=str(e))
            return []

    async def test_conference_room_details(self):
        """Test: Conference room detailed information."""
        if not self.test_room_id:
            self.log_test("conference_room_details", False, error="No test room ID available")
            return
        
        try:
            result = await self.plugin.get_conference_room_details_by_id(self.test_room_id)
            success = isinstance(result, dict)
            self.log_test("get_conference_room_details_by_id", success, result)
        except Exception as e:
            self.log_test("get_conference_room_details_by_id", False, error=str(e))

    async def test_conference_room_events(self):
        """Test: Conference room events and availability."""
        today = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z")
        
        test_cases = [
            {"max_results": 5},  # No date filter
            {"max_results": 5, "start_date": today, "end_date": tomorrow},  # With date filter
        ]
        
        for params in test_cases:
            try:
                result = await self.plugin.get_conference_room_events(**params)
                success = isinstance(result, list)
                param_desc = f"params: {params}"
                self.log_test(f"get_conference_room_events({param_desc})", success, f"Found {len(result)} room records")
                
                # Print detailed conference room events if found
                if success and result and self.debug:
                    print(f"\n📋 DETAILED CONFERENCE ROOM EVENTS ({len(result)} rooms):")
                    print("=" * 80)
                    
                    for i, room_record in enumerate(result, 1):
                        if isinstance(room_record, dict):
                            room_name = room_record.get('display_name', 'Unknown Room')
                            room_id = room_record.get('id', 'Unknown ID')
                            room_email = room_record.get('mail', 'No email')
                            events = room_record.get('events', [])
                            event_count = room_record.get('event_count', 0)
                            
                            print(f"\n🏢 Room {i}: {room_name}")
                            print(f"   ID: {room_id}")
                            print(f"   Email: {room_email}")
                            print(f"   Events Found: {event_count}")
                            
                            if events:
                                print(f"   📅 Event Details:")
                                for j, event in enumerate(events, 1):
                                    if isinstance(event, dict):
                                        subject = event.get('subject', 'No Subject')
                                        start_time = event.get('start', {}).get('date_time', 'Unknown')
                                        end_time = event.get('end', {}).get('date_time', 'Unknown')
                                        location = event.get('location', 'No location')
                                        attendees = event.get('attendees', [])
                                        
                                        print(f"      Event {j}: {subject}")
                                        print(f"         Start: {start_time}")
                                        print(f"         End: {end_time}")
                                        print(f"         Location: {location}")
                                        print(f"         Attendees: {len(attendees)}")
                                        
                                        if attendees:
                                            print(f"         Attendee List:")
                                            for attendee in attendees[:3]:  # Show first 3 attendees
                                                email = attendee.get('email', 'No email')
                                                name = attendee.get('name', 'No name')
                                                attendee_type = attendee.get('type', 'Unknown')
                                                print(f"           - {name} ({email}) [{attendee_type}]")
                                            if len(attendees) > 3:
                                                print(f"           ... and {len(attendees) - 3} more attendees")
                                        print()
                            else:
                                print(f"   📭 No events scheduled for this room")
                            
                            print("-" * 60)
                    
                    print(f"\n✅ Conference Room Events Summary:")
                    print(f"   Total Rooms Checked: {len(result)}")
                    total_events = sum(room.get('event_count', 0) for room in result if isinstance(room, dict))
                    print(f"   Total Events Found: {total_events}")
                    print("=" * 80)
                    
            except Exception as e:
                self.log_test(f"get_conference_room_events({params})", False, error=str(e))

    # =============================================================================
    # CALENDAR TESTS
    # =============================================================================
    
    async def test_mailbox_validation(self):
        """Test: Mailbox validation for troubleshooting."""
        if not self.test_user_id:
            self.log_test("mailbox_validation", False, error="No test user ID available")
            return
        
        try:
            result = await self.plugin.validate_user_mailbox(self.test_user_id)
            # Check for both dict and GenericProxy objects (from cache)
            success = result is not None and 'valid' in result
            
            if self.debug:
                print(f"   Mailbox validation result: {result}")
            
            self.log_test("validate_user_mailbox", success, result)
            
            # Return the validation status, but don't fail the test if mailbox is invalid
            # Some users might not have Exchange Online mailboxes
            is_valid = result.get('valid', False) if success else False
            
            if not is_valid and success:
                print(f"   ℹ️  Note: User mailbox validation returned False - this is normal for users without Exchange Online")
                print(f"   ℹ️  Message: {result.get('message', 'No message')}")
            
            return is_valid
        except Exception as e:
            self.log_test("validate_user_mailbox", False, error=str(e))
            return False

    async def test_calendar_events(self):
        """Test: Calendar event retrieval."""
        if not self.test_user_id:
            self.log_test("calendar_events", False, error="No test user ID available")
            return
        
        # First validate mailbox
        mailbox_valid = await self.test_mailbox_validation()
        
        if not mailbox_valid:
            # Try calendar access anyway - some users might have calendar access without Exchange Online
            print(f"   ℹ️  Mailbox validation failed, but attempting calendar access anyway...")
        
        today = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59Z")
        
        test_cases = [
            {"user_id": self.test_user_id},  # No date filter
            {"user_id": self.test_user_id, "start_date": today, "end_date": next_week},  # With date filter
        ]
        
        any_success = False
        for params in test_cases:
            try:
                result = await self.plugin.get_user_calendar_events(**params)
                success = isinstance(result, list)
                param_desc = "with date filter" if len(params) > 1 else "no date filter"
                self.log_test(f"get_user_calendar_events({param_desc})", success, f"Found {len(result)} events")
                if success:
                    any_success = True
                    
                    # Print detailed user calendar events if found
                    if result and self.debug:
                        print(f"\n📅 DETAILED USER CALENDAR EVENTS ({len(result)} events):")
                        print("=" * 80)
                        
                        for i, event in enumerate(result, 1):
                            # Handle both dict and Event object types
                            if isinstance(event, dict):
                                subject = event.get('subject', 'No Subject')
                                event_id = event.get('id', 'Unknown ID')
                                start_time = event.get('start', {}).get('date_time', 'Unknown') if isinstance(event.get('start'), dict) else str(event.get('start', 'Unknown'))
                                end_time = event.get('end', {}).get('date_time', 'Unknown') if isinstance(event.get('end'), dict) else str(event.get('end', 'Unknown'))
                                location = event.get('location', 'No location')
                                body_content = event.get('body', {}).get('content', 'No description') if isinstance(event.get('body'), dict) else str(event.get('body', 'No description'))
                                attendees = event.get('attendees', [])
                                organizer = event.get('organizer', {})
                                is_online_meeting = event.get('isOnlineMeeting', False)
                                web_link = event.get('webLink', 'No link')
                                sensitivity = event.get('sensitivity', 'Normal')
                                show_as = event.get('showAs', 'Unknown')
                            else:
                                # Handle Event objects from Microsoft Graph SDK
                                subject = getattr(event, 'subject', 'No Subject')
                                event_id = getattr(event, 'id', 'Unknown ID')
                                start_obj = getattr(event, 'start', None)
                                end_obj = getattr(event, 'end', None)
                                start_time = getattr(start_obj, 'date_time', 'Unknown') if start_obj else 'Unknown'
                                end_time = getattr(end_obj, 'date_time', 'Unknown') if end_obj else 'Unknown'
                                location_obj = getattr(event, 'location', None)
                                location = getattr(location_obj, 'display_name', 'No location') if location_obj else 'No location'
                                body_obj = getattr(event, 'body', None)
                                body_content = getattr(body_obj, 'content', 'No description') if body_obj else 'No description'
                                attendees = getattr(event, 'attendees', [])
                                organizer = getattr(event, 'organizer', {})
                                is_online_meeting = getattr(event, 'is_online_meeting', False)
                                web_link = getattr(event, 'web_link', 'No link')
                                sensitivity = getattr(event, 'sensitivity', 'Normal')
                                show_as = getattr(event, 'show_as', 'Unknown')
                            
                            print(f"\n📆 Event {i}: {subject}")
                            print(f"   ID: {event_id}")
                            print(f"   Start: {start_time}")
                            print(f"   End: {end_time}")
                            print(f"   Location: {location}")
                            print(f"   Sensitivity: {sensitivity}")
                            print(f"   Show As: {show_as}")
                            print(f"   Online Meeting: {'Yes' if is_online_meeting else 'No'}")
                            print(f"   Web Link: {web_link}")
                            
                            # Show organizer info
                            if organizer:
                                if isinstance(organizer, dict):
                                    org_name = organizer.get('emailAddress', {}).get('name', 'Unknown') if isinstance(organizer.get('emailAddress'), dict) else 'Unknown'
                                    org_email = organizer.get('emailAddress', {}).get('address', 'Unknown') if isinstance(organizer.get('emailAddress'), dict) else 'Unknown'
                                else:
                                    email_obj = getattr(organizer, 'email_address', None)
                                    org_name = getattr(email_obj, 'name', 'Unknown') if email_obj else 'Unknown'
                                    org_email = getattr(email_obj, 'address', 'Unknown') if email_obj else 'Unknown'
                                print(f"   Organizer: {org_name} ({org_email})")
                            
                            # Show description (truncated)
                            if body_content and body_content != 'No description':
                                # Clean up HTML and truncate
                                import re
                                clean_body = re.sub('<[^<]+?>', '', str(body_content))  # Remove HTML tags
                                clean_body = clean_body.strip()
                                if len(clean_body) > 100:
                                    clean_body = clean_body[:100] + "..."
                                print(f"   Description: {clean_body}")
                            
                            # Show attendees
                            if attendees:
                                print(f"   Attendees ({len(attendees)}):")
                                for j, attendee in enumerate(attendees[:5]):  # Show first 5 attendees
                                    if isinstance(attendee, dict):
                                        att_name = attendee.get('emailAddress', {}).get('name', 'Unknown') if isinstance(attendee.get('emailAddress'), dict) else 'Unknown'
                                        att_email = attendee.get('emailAddress', {}).get('address', 'Unknown') if isinstance(attendee.get('emailAddress'), dict) else 'Unknown'
                                        att_type = attendee.get('type', 'Unknown')
                                        response_status = attendee.get('status', {}).get('response', 'Unknown') if isinstance(attendee.get('status'), dict) else 'Unknown'
                                    else:
                                        email_obj = getattr(attendee, 'email_address', None)
                                        att_name = getattr(email_obj, 'name', 'Unknown') if email_obj else 'Unknown'
                                        att_email = getattr(email_obj, 'address', 'Unknown') if email_obj else 'Unknown'
                                        att_type = getattr(attendee, 'type', 'Unknown')
                                        status_obj = getattr(attendee, 'status', None)
                                        response_status = getattr(status_obj, 'response', 'Unknown') if status_obj else 'Unknown'
                                    
                                    print(f"      {j+1}. {att_name} ({att_email}) [{att_type}] - {response_status}")
                                
                                if len(attendees) > 5:
                                    print(f"      ... and {len(attendees) - 5} more attendees")
                            else:
                                print(f"   Attendees: None")
                            
                            print("-" * 60)
                        
                        print(f"\n✅ User Calendar Events Summary:")
                        print(f"   Total Events Found: {len(result)}")
                        
                        # Count different event types
                        online_meetings = sum(1 for e in result if (isinstance(e, dict) and e.get('isOnlineMeeting')) or (hasattr(e, 'is_online_meeting') and e.is_online_meeting))
                        private_events = sum(1 for e in result if (isinstance(e, dict) and e.get('sensitivity') == 'Private') or (hasattr(e, 'sensitivity') and e.sensitivity == 'Private'))
                        
                        print(f"   Online Meetings: {online_meetings}")
                        print(f"   Private Events: {private_events}")
                        print("=" * 80)
                        
            except Exception as e:
                param_desc = "with date filter" if len(params) > 1 else "no date filter"
                self.log_test(f"get_user_calendar_events({param_desc})", False, error=str(e))
        
        # If no calendar tests succeeded and mailbox validation failed, provide helpful message
        if not any_success and not mailbox_valid:
            print(f"   ℹ️  Calendar access failed - user may not have Exchange Online or sufficient permissions")
            print(f"   ℹ️  This is normal in test environments or for users without Office 365 licenses")

    # =============================================================================
    # CONFERENCE ROOM BOOKING TESTS
    # =============================================================================
    
    async def test_find_available_conference_rooms(self):
        """Test: Find available conference rooms for a specific time slot."""
        if not self.test_user_id:
            self.log_test("find_available_conference_rooms", False, error="No test user ID available")
            return
        
        # Generate a future time slot for room availability check
        start_time, end_time = self._generate_random_future_time(
            min_hours_ahead=24,   # At least 1 day from now
            max_hours_ahead=168   # Up to 1 week from now
        )
        
        print(f"🏢 Checking conference room availability for:")
        print(f"   📅 Start: {start_time}")
        print(f"   📅 End: {end_time}")
        
        try:
            # First get all conference rooms
            all_rooms = await self.plugin.get_all_conference_rooms(max_results=50)
            
            if not all_rooms:
                self.log_test("find_available_conference_rooms", False, error="No conference rooms found")
                return
            
            available_rooms = []
            busy_rooms = []
            
            print(f"\n🔍 Checking availability for {len(all_rooms)} conference rooms...")
            
            # Check each room's availability
            for room in all_rooms:
                room_id = room.get('id') if isinstance(room, dict) else getattr(room, 'id', None)
                room_name = room.get('display_name') if isinstance(room, dict) else getattr(room, 'display_name', 'Unknown')
                room_email = room.get('mail') if isinstance(room, dict) else getattr(room, 'mail', 'Unknown')
                
                if room_id:
                    try:
                        # Get room events for the time period
                        room_events = await self.plugin.get_user_calendar_events(
                            user_id=room_id,
                            start_date=start_time,
                            end_date=end_time
                        )
                        
                        if isinstance(room_events, list) and len(room_events) == 0:
                            available_rooms.append({
                                'id': room_id,
                                'name': room_name,
                                'email': room_email,
                                'availability': 'Available'
                            })
                            print(f"   ✅ {room_name} - Available")
                        else:
                            busy_rooms.append({
                                'id': room_id,
                                'name': room_name,
                                'email': room_email,
                                'conflicting_events': len(room_events) if isinstance(room_events, list) else 1,
                                'availability': 'Busy'
                            })
                            conflict_count = len(room_events) if isinstance(room_events, list) else 1
                            print(f"   ❌ {room_name} - Busy ({conflict_count} conflicts)")
                            
                    except Exception as e:
                        print(f"   ⚠️  {room_name} - Error checking availability: {e}")
            
            # Store available rooms for later booking tests
            self.available_rooms = available_rooms
            
            result_summary = {
                'total_rooms_checked': len(all_rooms),
                'available_rooms': len(available_rooms),
                'busy_rooms': len(busy_rooms),
                'time_slot': f"{start_time} to {end_time}",
                'available_room_list': available_rooms[:5]  # First 5 available rooms
            }
            
            success = len(all_rooms) > 0
            self.log_test("find_available_conference_rooms", success, result_summary)
            
            if available_rooms:
                print(f"\n✅ Found {len(available_rooms)} available conference rooms:")
                for room in available_rooms[:10]:  # Show first 10
                    print(f"   🏢 {room['name']} ({room['email']})")
                if len(available_rooms) > 10:
                    print(f"   ... and {len(available_rooms) - 10} more rooms")
            else:
                print(f"\n❌ No available conference rooms found for the specified time slot")
                
            return available_rooms
            
        except Exception as e:
            self.log_test("find_available_conference_rooms", False, error=str(e))
            return []

    async def test_book_conference_room_event(self):
        """Test: Book an actual meeting in an available conference room (WILL CREATE ACTUAL MEETING)."""
        if not self.test_user_id:
            self.log_test("book_conference_room_event", False, error="No test user ID available")
            return
        
        # First find available rooms
        available_rooms = await self.test_find_available_conference_rooms()
        
        if not available_rooms:
            self.log_test("book_conference_room_event", False, error="No available conference rooms found")
            return
        
        # Select the first available room
        selected_room = available_rooms[0]
        room_name = selected_room['name']
        room_email = selected_room['email']
        
        print(f"\n🏢 Selected conference room: {room_name}")
        print(f"📧 Room email: {room_email}")
        print("⚠️  WARNING: This will create an actual meeting booking in this conference room!")
        
        response = input("Do you want to proceed with booking? (y/N): ")
        
        if response.lower() != 'y':
            self.log_test("book_conference_room_event", False, error="Skipped by user choice")
            return
        
        try:
            # Generate time slot for booking
            start_time, end_time = self._generate_random_future_time(
                min_hours_ahead=24,   # At least 1 day from now
                max_hours_ahead=168   # Up to 1 week from now
            )
            
            # Generate unique meeting details
            meeting_id_suffix = random.randint(1000, 9999)
            subject = f"Test Conference Room Booking #{meeting_id_suffix} - Safe to Delete"
            
            # Create rich HTML body for conference room booking
            room_booking_html = f"""
<html>
<body>
<h2>🏢 Conference Room Booking - Microsoft Graph API Test</h2>
<p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Booking Type:</strong> Conference Room Reservation</p>
<p><strong>Status:</strong> ✅ Auto-Generated Test Booking</p>

<h3>🏢 Room Details</h3>
<ul>
    <li><strong>Room Name:</strong> {room_name}</li>
    <li><strong>Room Email:</strong> {room_email}</li>
    <li><strong>Meeting Time:</strong> {start_time} to {end_time}</li>
    <li><strong>Duration:</strong> {((datetime.fromisoformat(end_time.replace('Z', '+00:00')) - datetime.fromisoformat(start_time.replace('Z', '+00:00'))).total_seconds() / 3600):.1f} hours</li>
</ul>

<h3>📋 Meeting Purpose</h3>
<p>This is a test conference room booking created by the Microsoft Graph Plugin test suite to demonstrate:</p>
<ul>
    <li>✅ Conference room discovery and availability checking</li>
    <li>🏢 Room booking via Microsoft Graph API</li>
    <li>📅 Automated scheduling with room resources</li>
    <li>🎯 Resource management integration</li>
    <li>📧 Attendee and room invitation workflow</li>
</ul>

<h3>🎯 Meeting Guidelines</h3>
<ul>
    <li>📱 Arrive 5 minutes early to set up equipment</li>
    <li>🧹 Clean up after the meeting</li>
    <li>💡 Turn off lights and equipment when leaving</li>
    <li>📞 Contact facilities if any issues with room equipment</li>
</ul>

<hr>
<p style="color: #666; font-size: 12px;">
    ⚠️ This is a test room booking and can be safely deleted.<br>
    Generated by Microsoft Graph Plugin Test Suite<br>
    🏢 Room: {room_name} | 📧 {room_email}
</p>
</body>
</html>
            """.strip()
            
            # Create the meeting with the conference room as an attendee
            result = await self.plugin.create_calendar_event(
                user_id=self.test_user_id,
                subject=subject,
                start=start_time,
                end=end_time,
                location=room_name,
                body=room_booking_html,
                attendees=[room_email]  # Add the room as an attendee
            )
            
            success = isinstance(result, dict) and result.get('id')
            self.log_test("book_conference_room_event", success, result)
            
            if success:
                print(f"✅ Successfully booked conference room!")
                print(f"   🏢 Room: {room_name}")
                print(f"   📅 Meeting ID: {result.get('id')}")
                print(f"   ⏰ Time: {start_time} to {end_time}")
                print(f"   📧 Room invited: {room_email}")
                print("📝 You can safely delete this booking from your calendar")
            else:
                print(f"❌ Failed to book conference room")
                
        except Exception as e:
            self.log_test("book_conference_room_event", False, error=str(e))

    async def test_conference_room_teams_meeting(self):
        """Test: Create a Teams meeting in a conference room (HYBRID MEETING)."""
        if not self.test_user_id:
            self.log_test("conference_room_teams_meeting", False, error="No test user ID available")
            return
        
        # Find available rooms
        if not hasattr(self, 'available_rooms') or not self.available_rooms:
            available_rooms = await self.test_find_available_conference_rooms()
        else:
            available_rooms = self.available_rooms
        
        if not available_rooms:
            self.log_test("conference_room_teams_meeting", False, error="No available conference rooms found")
            return
        
        # Select a room for hybrid meeting
        selected_room = available_rooms[0]
        room_name = selected_room['name']
        room_email = selected_room['email']
        
        print(f"\n🏢 Creating hybrid meeting (Teams + Conference Room)")
        print(f"📍 Physical Location: {room_name}")
        print(f"💬 Virtual Platform: Microsoft Teams")
        print("⚠️  WARNING: This will create an actual Teams meeting with room booking!")
        
        response = input("Do you want to proceed? (y/N): ")
        
        if response.lower() != 'y':
            self.log_test("conference_room_teams_meeting", False, error="Skipped by user choice")
            return
        
        try:
            # Generate time slot
            start_time, end_time = self._generate_random_future_time(
                min_hours_ahead=24,   # At least 1 day from now
                max_hours_ahead=168   # Up to 1 week from now
            )
            
            meeting_id_suffix = random.randint(1000, 9999)
            subject = f"Test Hybrid Meeting #{meeting_id_suffix} - Safe to Delete"
            
            # Create comprehensive hybrid meeting body
            hybrid_meeting_html = f"""
<html>
<body>
<h2>🎯 Hybrid Meeting - Teams + Conference Room</h2>
<p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Meeting Type:</strong> Hybrid (Physical + Virtual)</p>
<p><strong>Status:</strong> ✅ Auto-Generated Test Meeting</p>

<h3>📍 Meeting Locations</h3>
<table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 15px 0;">
    <tr style="background-color: #f0f8ff;">
        <th>Attendance Option</th>
        <th>Location/Platform</th>
        <th>Details</th>
    </tr>
    <tr>
        <td><strong>🏢 In-Person</strong></td>
        <td>{room_name}</td>
        <td>Physical conference room booking</td>
    </tr>
    <tr>
        <td><strong>💬 Virtual</strong></td>
        <td>Microsoft Teams</td>
        <td>Online meeting link (auto-generated)</td>
    </tr>
</table>

<h3>🎯 Hybrid Meeting Benefits</h3>
<ul>
    <li>🤝 In-person collaboration for on-site team members</li>
    <li>🌐 Virtual access for remote participants</li>
    <li>📱 Teams integration for screen sharing and recording</li>
    <li>🏢 Professional conference room environment</li>
    <li>🔄 Seamless hybrid experience</li>
</ul>

<h3>📋 Meeting Guidelines</h3>
<p><strong>For In-Person Attendees:</strong></p>
<ul>
    <li>📍 Report to {room_name}</li>
    <li>🎤 Use room microphone for virtual participants</li>
    <li>📺 Ensure camera shows the room clearly</li>
    <li>🔇 Mute Teams audio to avoid echo (room will handle audio)</li>
</ul>

<p><strong>For Virtual Attendees:</strong></p>
<ul>
    <li>💬 Join via Teams link (auto-generated below)</li>
    <li>🎤 Use headset for best audio quality</li>
    <li>📹 Turn on camera for better engagement</li>
    <li>✋ Use Teams reactions and chat</li>
</ul>

<hr>
<p style="color: #666; font-size: 12px;">
    ⚠️ This is a test hybrid meeting and can be safely deleted.<br>
    Generated by Microsoft Graph Plugin Test Suite<br>
    🏢 Room: {room_name} | 📧 {room_email} | 💬 Teams integration enabled
</p>
</body>
</html>
            """.strip()
            
            # Create Teams meeting with conference room
            result = await self.plugin.create_teams_meeting(
                user_id=self.test_user_id,
                subject=subject,
                start=start_time,
                end=end_time,
                body=hybrid_meeting_html,
                location=f"{room_name} + Microsoft Teams",
                attendees=[room_email]  # Include the room as attendee
            )
            
            success = isinstance(result, dict) and result.get('id')
            self.log_test("conference_room_teams_meeting", success, result)
            
            if success:
                print(f"✅ Successfully created hybrid meeting!")
                print(f"   🏢 Physical Location: {room_name}")
                print(f"   💬 Virtual Platform: Microsoft Teams")
                print(f"   📅 Meeting ID: {result.get('id')}")
                print(f"   ⏰ Time: {start_time} to {end_time}")
                print(f"   📧 Room booked: {room_email}")
                print("📝 Attendees can join either in-person or via Teams")
            else:
                print(f"❌ Failed to create hybrid meeting")
                
        except Exception as e:
            self.log_test("conference_room_teams_meeting", False, error=str(e))

    # =============================================================================
    # CALENDAR EVENT CREATION TESTS (USE WITH CAUTION)
    # =============================================================================
    
    async def test_create_test_event(self):
        """Test: Create a test calendar event (WILL CREATE ACTUAL EVENT)."""
        if not self.test_user_id:
            self.log_test("create_test_event", False, error="No test user ID available")
            return
        
        # Generate random future time to avoid scheduling conflicts (weekdays only)
        start_time, end_time = self._generate_random_future_time(
            min_hours_ahead=2,    # At least 2 hours from now
            max_hours_ahead=120   # Up to 5 days (business week) from now
        )
        
        print("⚠️  WARNING: This will create an actual calendar event!")
        print(f"📅 Scheduled for: {start_time} to {end_time}")
        response = input("Do you want to proceed? (y/N): ")
        
        if response.lower() != 'y':
            self.log_test("create_test_event", False, error="Skipped by user choice")
            return
        
        try:
            # Generate a unique subject to avoid duplicates
            event_id_suffix = random.randint(1000, 9999)
            subject = f"Test Event #{event_id_suffix} - Safe to Delete"
            
            # Create rich HTML body content
            body_html = f"""
<html>
<body>
<h2>🧪 Test Event - Microsoft Graph API Suite</h2>
<p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Event Type:</strong> Calendar Event Test</p>
<p><strong>Status:</strong> ✅ Auto-Generated Test Event</p>

<h3>📋 Event Details</h3>
<ul>
    <li><strong>Subject:</strong> {subject}</li>
    <li><strong>Start Time:</strong> {start_time}</li>
    <li><strong>End Time:</strong> {end_time}</li>
    <li><strong>Location:</strong> Test Location (Auto-Generated)</li>
</ul>

<h3>📝 Description</h3>
<p>This is a randomly scheduled test event created by the Microsoft Graph Plugin test suite. It demonstrates the following capabilities:</p>
<ul>
    <li>✅ Calendar event creation via Microsoft Graph API</li>
    <li>📅 Random weekday scheduling within business hours</li>
    <li>🔍 HTML body content formatting</li>
    <li>🎯 Automated testing workflow</li>
</ul>

<hr>
<p style="color: #666; font-size: 12px;">
    ⚠️ This is a test event and can be safely deleted.<br>
    Generated by Microsoft Graph Plugin Test Suite
</p>
</body>
</html>
            """.strip()

            result = await self.plugin.create_calendar_event(
                user_id=self.test_user_id,
                subject=subject,
                start=start_time,
                end=end_time,
                location="Test Location (Auto-Generated)",
                body=body_html
            )
            success = isinstance(result, dict) and result.get('id')
            self.log_test("create_calendar_event", success, result)
            
            if success:
                print(f"✅ Created test event '{subject}' with ID: {result.get('id')}")
                print(f"📅 Scheduled for: {start_time} to {end_time}")
                print("📝 You can safely delete this event from your calendar")
                
        except Exception as e:
            self.log_test("create_calendar_event", False, error=str(e))

    async def test_create_teams_meeting(self):
        """Test: Create a Teams meeting (WILL CREATE ACTUAL MEETING)."""
        if not self.test_user_id:
            self.log_test("create_teams_meeting", False, error="No test user ID available")
            return
        
        print("⚠️  WARNING: This will create an actual Teams meeting!")
        
        # Generate random future time to avoid scheduling conflicts (weekdays only)
        start_time, end_time = self._generate_random_future_time(
            min_hours_ahead=3,    # At least 3 hours from now (different from regular events)
            max_hours_ahead=120   # Up to 5 days (business week) from now
        )
        
        print(f"📅 Scheduled for: {start_time} to {end_time}")
        response = input("Do you want to proceed? (y/N): ")
        
        if response.lower() != 'y':
            self.log_test("create_teams_meeting", False, error="Skipped by user choice")
            return
        
        try:
            # Generate a unique subject to avoid duplicates
            meeting_id_suffix = random.randint(1000, 9999)
            subject = f"Test Teams Meeting #{meeting_id_suffix} - Safe to Delete"
            
            # Create rich HTML body content for Teams meeting
            teams_body_html = f"""
<html>
<body>
<h2>🧪 Test Teams Meeting - Microsoft Graph API Suite</h2>
<p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Meeting Type:</strong> Microsoft Teams Online Meeting</p>
<p><strong>Status:</strong> ✅ Auto-Generated Test Meeting</p>

<h3>📋 Meeting Details</h3>
<ul>
    <li><strong>Subject:</strong> {subject}</li>
    <li><strong>Start Time:</strong> {start_time}</li>
    <li><strong>End Time:</strong> {end_time}</li>
    <li><strong>Platform:</strong> Microsoft Teams</li>
</ul>

<h3>🎯 Meeting Purpose</h3>
<p>This is a test Teams meeting created by the Microsoft Graph Plugin test suite to demonstrate:</p>
<ul>
    <li>✅ Teams meeting creation via Microsoft Graph API</li>
    <li>📅 Random weekday scheduling within business hours</li>
    <li>💬 Teams integration and meeting links</li>
    <li>🔍 HTML body content with Teams branding</li>
    <li>🎯 Automated testing workflow</li>
</ul>

<h3>💬 How to Join</h3>
<p><strong>Note:</strong> Teams meeting link will be automatically added by Microsoft Graph when the meeting is created.</p>
<p>You can join this meeting by:</p>
<ul>
    <li>📱 Clicking the Teams meeting link in your calendar</li>
    <li>📞 Dialing in using the conference details</li>
    <li>💻 Opening Microsoft Teams and finding the meeting</li>
</ul>

<hr>
<p style="color: #666; font-size: 12px;">
    ⚠️ This is a test meeting and can be safely deleted.<br>
    Generated by Microsoft Graph Plugin Test Suite<br>
    🎯 Meeting link and dial-in details will be added automatically by Teams
</p>
</body>
</html>
            """.strip()

            result = await self.plugin.create_teams_meeting(
                user_id=self.test_user_id,
                subject=subject,
                start=start_time,
                end=end_time,
                body=teams_body_html
            )
            success = isinstance(result, dict) and result.get('id')
            self.log_test("create_teams_meeting", success, result)
            
            if success:
                print(f"✅ Created test Teams meeting '{subject}' with ID: {result.get('id')}")
                print(f"📅 Scheduled for: {start_time} to {end_time}")
                print("📝 You can safely delete this meeting from your calendar")
                
        except Exception as e:
            self.log_test("create_teams_meeting", False, error=str(e))

    async def test_create_multiple_random_events(self, num_events: int = 3):
        """Test: Create multiple test events at random future times (WILL CREATE ACTUAL EVENTS)."""
        if not self.test_user_id:
            self.log_test("create_multiple_random_events", False, error="No test user ID available")
            return
        
        print(f"⚠️  WARNING: This will create {num_events} actual calendar events!")
        print("📅 Each event will be scheduled at a random time on weekdays within the next 5 business days")
        response = input(f"Do you want to proceed with creating {num_events} events? (y/N): ")
        
        if response.lower() != 'y':
            self.log_test("create_multiple_random_events", False, error="Skipped by user choice")
            return
        
        created_events = []
        failed_events = 0
        
        for i in range(num_events):
            try:
                # Generate random future time for each event (weekdays only)
                start_time, end_time = self._generate_random_future_time(
                    min_hours_ahead=1,     # Can be as soon as 1 hour from now
                    max_hours_ahead=120    # Up to 5 business days from now
                )
                
                # Generate unique event details
                event_num = i + 1
                event_id_suffix = random.randint(1000, 9999)
                
                # Random event types for variety
                event_types = [
                    ("Team Meeting", "Conference Room A"),
                    ("Project Review", "Virtual - Teams"),
                    ("Client Call", "Phone Conference"),
                    ("Training Session", "Training Room B"),
                    ("One-on-One", "Office"),
                    ("Planning Session", "Breakout Room"),
                ]
                
                event_type, location = random.choice(event_types)
                subject = f"Test {event_type} #{event_id_suffix} - Safe to Delete"
                
                # Create varied rich HTML body content for each event type
                event_descriptions = {
                    "Team Meeting": {
                        "emoji": "👥",
                        "purpose": "Team collaboration and project updates",
                        "agenda": ["Project status updates", "Team coordination", "Next steps planning"],
                        "links": ["📊 Project Dashboard", "📋 Team Board", "📅 Schedule"]
                    },
                    "Project Review": {
                        "emoji": "📊", 
                        "purpose": "Review project progress and deliverables",
                        "agenda": ["Progress assessment", "Quality review", "Timeline validation"],
                        "links": ["📈 Analytics", "🔍 Quality Reports", "📋 Deliverables"]
                    },
                    "Client Call": {
                        "emoji": "📞",
                        "purpose": "Client communication and relationship management",
                        "agenda": ["Client requirements", "Service updates", "Future planning"],
                        "links": ["👤 Client Portal", "📋 Service Board", "📈 Reports"]
                    },
                    "Training Session": {
                        "emoji": "📚",
                        "purpose": "Knowledge transfer and skill development",
                        "agenda": ["Learning objectives", "Hands-on practice", "Q&A session"],
                        "links": ["📖 Training Materials", "🎯 Learning Path", "💡 Resources"]
                    },
                    "One-on-One": {
                        "emoji": "🤝",
                        "purpose": "Individual development and feedback",
                        "agenda": ["Performance discussion", "Goal setting", "Career development"],
                        "links": ["📊 Performance Dashboard", "🎯 Goals", "📈 Development Plan"]
                    },
                    "Planning Session": {
                        "emoji": "🎯",
                        "purpose": "Strategic planning and roadmap development",
                        "agenda": ["Strategy review", "Roadmap planning", "Resource allocation"],
                        "links": ["🗺️ Roadmap", "📋 Strategy Board", "📊 Resource Planning"]
                    }
                }
                
                event_info = event_descriptions.get(event_type, event_descriptions["Team Meeting"])
                
                body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<h2 style="color: #0078d4; margin-bottom: 20px;">{event_info['emoji']} {subject}</h2>

<p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
<strong>Event #{event_num} of {num_events}</strong> | Microsoft Graph API Test Suite</p>

<h3 style="color: #0078d4; border-bottom: 1px solid #ddd; padding-bottom: 5px;">Meeting Details</h3>
<p><strong>Type:</strong> {event_type}<br>
<strong>Purpose:</strong> {event_info['purpose']}<br>
<strong>Location:</strong> {location}<br>
<strong>Duration:</strong> {start_time} to {end_time}</p>

<h3 style="color: #0078d4; border-bottom: 1px solid #ddd; padding-bottom: 5px;">Agenda</h3>
<ol>
{"".join([f"<li>{item}</li>" for item in event_info['agenda']])}
</ol>

<h3 style="color: #0078d4; border-bottom: 1px solid #ddd; padding-bottom: 5px;">Related Resources</h3>
<p>
{"<br>".join([f'<a href="#" style="color: #0078d4;">{link}</a>' for link in event_info['links']])}
</p>

<hr style="border: 1px solid #ddd; margin: 20px 0;">
<p style="color: #666; font-size: 12px;">
This is test event #{event_num} of {num_events} and can be safely deleted.<br>
Generated by Microsoft Graph Plugin Test Suite | Auto-scheduled on weekdays only
</p>
</body>
</html>
                """.strip()

                print(f"\n📅 Creating event {event_num}/{num_events}: {subject}")
                print(f"   ⏰ {start_time} to {end_time}")
                
                result = await self.plugin.create_calendar_event(
                    user_id=self.test_user_id,
                    subject=subject,
                    start=start_time,
                    end=end_time,
                    location=location,
                    body=body_html
                )
                
                if isinstance(result, dict) and result.get('id'):
                    created_events.append({
                        'id': result.get('id'),
                        'subject': subject,
                        'start': start_time,
                        'end': end_time
                    })
                    print(f"   ✅ Created successfully (ID: {result.get('id')})")
                else:
                    failed_events += 1
                    print(f"   ❌ Failed to create event")
                
                # Small delay between events to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_events += 1
                print(f"   ❌ Error creating event {event_num}: {e}")
        
        # Log overall results
        success = len(created_events) > 0
        result_summary = {
            'total_requested': num_events,
            'successfully_created': len(created_events),
            'failed': failed_events,
            'created_events': created_events
        }
        
        self.log_test("create_multiple_random_events", success, result_summary)
        
        if created_events:
            print(f"\n✅ Successfully created {len(created_events)}/{num_events} test events")
            print("📝 All test events are safe to delete from your calendar")
            print("\n📋 Created Events Summary:")
            for event in created_events:
                print(f"   • {event['subject']}")
                print(f"     ⏰ {event['start']} to {event['end']}")
                print(f"     🆔 ID: {event['id']}")
        else:
            print(f"❌ Failed to create any events")

    # =============================================================================
    # TEST SUITE EXECUTION
    # =============================================================================
    
    async def run_all_tests(self, include_creation_tests: bool = False):
        """Run the complete test suite."""
        print("🚀 Starting Microsoft Graph Plugin Test Suite")
        print("=" * 60)
        
        # System tests
        print("\n📅 SYSTEM & TIME TESTS")
        await self.test_get_current_datetime()
        
        # User discovery tests
        print("\n👥 USER DISCOVERY & SEARCH TESTS")
        await self.test_user_search_basic()
        await self.test_user_search_complex()
        await self.test_get_all_users()
        
        # Department tests
        print("\n🏢 DEPARTMENT TESTS")
        await self.test_get_all_departments()
        await self.test_get_users_by_department()
        
        # Individual user tests
        print("\n👤 INDIVIDUAL USER TESTS")
        await self.test_user_lookup_functions()
        await self.test_user_preferences_and_mailbox()
        await self.test_organizational_hierarchy()
        
        # Conference room tests
        print("\n🏢 CONFERENCE ROOM TESTS")
        await self.test_conference_room_discovery()
        await self.test_conference_room_details()
        await self.test_conference_room_events()
        
        # Conference room booking tests
        print("\n🏢 CONFERENCE ROOM BOOKING TESTS")
        await self.test_find_available_conference_rooms()
        
        # Calendar tests
        print("\n📅 CALENDAR TESTS")
        await self.test_mailbox_validation()
        await self.test_calendar_events()
        
        # Optional creation tests
        if include_creation_tests:
            print("\n✨ CALENDAR CREATION TESTS (CREATES ACTUAL EVENTS)")
            await self.test_create_test_event()
            await self.test_create_teams_meeting()
            
            # Conference room booking tests (with user confirmation)
            print("\n🏢 CONFERENCE ROOM BOOKING TESTS (CREATES ACTUAL BOOKINGS)")
            book_rooms = input("Test conference room booking functionality? (y/N): ")
            if book_rooms.lower() == 'y':
                await self.test_book_conference_room_event()
                await self.test_conference_room_teams_meeting()
            
            # Ask if user wants to create multiple random events
            print("\n🎲 MULTIPLE RANDOM EVENTS TEST")
            create_multiple = input("Create multiple random test events for stress testing? (weekdays only) (y/N): ")
            if create_multiple.lower() == 'y':
                num_events = input("How many events to create? (default: 3): ").strip()
                try:
                    num_events = int(num_events) if num_events else 3
                    num_events = max(1, min(num_events, 10))  # Limit between 1 and 10
                except ValueError:
                    num_events = 3
                await self.test_create_multiple_random_events(num_events)
        
        # Summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print a summary of all test results."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['error']}")
        
        print("\n🎉 Test suite completed!")
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print("📝 Detailed results saved to test_results.json")


# =============================================================================
# INDIVIDUAL TEST FUNCTIONS (for running specific tests)
# =============================================================================

async def quick_connection_test():
    """Quick test to verify Graph connection is working."""
    print("🔍 Running quick connection test...")
    suite = GraphTestSuite(debug=False)
    
    # Test basic connectivity
    await suite.test_get_current_datetime()
    await suite.test_get_all_users()
    
    suite.print_test_summary()

async def conference_room_tests_only():
    """Run only conference room-related tests."""
    print("🏢 Running Conference Room Tests Only")
    print("=" * 50)
    
    suite = GraphTestSuite(debug=True)
    
    # System test for reference
    await suite.test_get_current_datetime()
    
    # User discovery (needed for room booking)
    print("\n👥 USER DISCOVERY (for room booking)")
    await suite.test_get_all_users()
    
    # Conference room discovery
    print("\n🏢 CONFERENCE ROOM DISCOVERY")
    await suite.test_conference_room_discovery()
    await suite.test_conference_room_details()
    await suite.test_conference_room_events()
    
    # Conference room availability and booking
    print("\n📅 CONFERENCE ROOM AVAILABILITY & BOOKING")
    available_rooms = await suite.test_find_available_conference_rooms()
    
    if available_rooms:
        print(f"\n✅ Found {len(available_rooms)} available conference rooms")
        print("Would you like to test actual room booking? (Creates real meetings)")
        
        # Test room booking
        test_booking = input("Test conference room booking? (y/N): ")
        if test_booking.lower() == 'y':
            await suite.test_book_conference_room_event()
        
        # Test hybrid meetings
        test_hybrid = input("Test hybrid Teams + conference room meeting? (y/N): ")
        if test_hybrid.lower() == 'y':
            await suite.test_conference_room_teams_meeting()
    else:
        print("❌ No available conference rooms found for testing")
    
    # Print results
    suite.print_test_summary()

async def quick_room_availability_check():
    """Quick check of conference room availability without booking."""
    print("🔍 Quick Conference Room Availability Check")
    print("=" * 50)
    
    suite = GraphTestSuite(debug=True)
    
    # Get user for calendar access
    await suite.test_get_all_users()
    
    # Check room availability
    available_rooms = await suite.test_find_available_conference_rooms()
    
    if available_rooms:
        print(f"\n📊 AVAILABILITY SUMMARY:")
        print(f"   Available Rooms: {len(available_rooms)}")
        print(f"\n🏢 TOP AVAILABLE ROOMS:")
        for i, room in enumerate(available_rooms[:5], 1):
            print(f"   {i}. {room['name']}")
            print(f"      📧 {room['email']}")
            print(f"      ✅ Available for booking")
        
        if len(available_rooms) > 5:
            print(f"   ... and {len(available_rooms) - 5} more rooms available")
    else:
        print("❌ No available rooms found for the checked time slot")

async def user_tests_only():
    """Run only user-related tests."""
    print("👥 Running user-focused tests...")
    suite = GraphTestSuite(debug=True)
    
    await suite.test_get_current_datetime()
    await suite.test_user_search_basic()
    await suite.test_get_all_users()
    await suite.test_get_all_departments()
    await suite.test_user_lookup_functions()
    
    suite.print_test_summary()

async def calendar_tests_only():
    """Run only calendar-related tests."""
    print("📅 Running calendar-focused tests...")
    suite = GraphTestSuite(debug=True)
    
    await suite.test_get_current_datetime()
    await suite.test_get_all_users()  # Need user ID for calendar tests
    await suite.test_mailbox_validation()
    await suite.test_calendar_events()
    
    suite.print_test_summary()

async def room_tests_only():
    """Run only conference room tests."""
    print("🏢 Running conference room tests...")
    suite = GraphTestSuite(debug=True)
    
    await suite.test_get_current_datetime()
    await suite.test_conference_room_discovery()
    await suite.test_conference_room_details()
    await suite.test_conference_room_events()
    
    suite.print_test_summary()

async def multiple_random_events_test():
    """Run only the multiple random events creation test (weekdays only)."""
    print("� Running multiple random events test...")
    suite = GraphTestSuite(debug=True)
    
    # Need user ID first
    await suite.test_get_current_datetime()
    await suite.test_get_all_users()
    
    # Ask for number of events
    num_events = input("How many random weekday events to create? (1-10, default: 3): ").strip()
    try:
        num_events = int(num_events) if num_events else 3
        num_events = max(1, min(num_events, 10))  # Limit between 1 and 10
    except ValueError:
        num_events = 3
    
    await suite.test_create_multiple_random_events(num_events)
    suite.print_test_summary()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function with user menu."""
    print("🔧 Microsoft Graph Plugin Test Suite")
    print("=" * 40)
    print("1. Quick Connection Test")
    print("2. User Tests Only")
    print("3. Calendar Tests Only") 
    print("4. Conference Room Tests Only")
    print("5. Full Test Suite (No Event Creation)")
    print("6. Full Test Suite (With Event Creation)")
    print("7. Multiple Random Events Test (Weekdays Only)")
    print("0. Exit")
    
    choice = input("\nSelect test option (0-7): ")
    
    if choice == "1":
        await quick_connection_test()
    elif choice == "2":
        await user_tests_only()
    elif choice == "3":
        await calendar_tests_only()
    elif choice == "4":
        await room_tests_only()
    elif choice == "5":
        suite = GraphTestSuite(debug=True)
        await suite.run_all_tests(include_creation_tests=False)
    elif choice == "6":
        suite = GraphTestSuite(debug=True)
        await suite.run_all_tests(include_creation_tests=True)
    elif choice == "7":
        await multiple_random_events_test()
    elif choice == "0":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        await main()


if __name__ == "__main__":
    """Entry point for the test suite."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Make sure you have proper Microsoft Graph authentication configured.")
