import os

# CRITICAL: Check telemetry disable flag BEFORE any other imports
TELEMETRY_EXPLICITLY_DISABLED = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', '').lower() in ('true', '1', 'yes')

if TELEMETRY_EXPLICITLY_DISABLED:
    print("🚫 Telemetry explicitly disabled via environment variable")

from datetime import datetime
import traceback
import asyncio
from typing import List, Dict, Optional, Any
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
import msgraph
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.user import User
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.email_address import EmailAddress

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without loading .env file
    pass

# Production-grade telemetry import with timeout and graceful fallback
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

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
                    if os.environ.get('DEBUG_GRAPH_OPERATIONS', '').lower() in ('true', '1'):
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
        prefix = f"[{module}]" if module else "[GraphOps]"
        print(f"{timestamp} INFO {prefix} {message}")
    
    def console_debug(message, module=None):
        """Production console debug (only in debug mode)."""
        if os.environ.get('DEBUG_GRAPH_OPERATIONS', '').lower() in ('true', '1'):
            timestamp = datetime.now().isoformat()
            prefix = f"[{module}]" if module else "[GraphOps]"
            print(f"{timestamp} DEBUG {prefix} {message}")
    
    def console_warning(message, module=None):
        """Production console warning."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        print(f"{timestamp} WARNING {prefix} {message}")
    
    def console_error(message, module=None):
        """Production console error."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        print(f"{timestamp} ERROR {prefix} {message}")
    
    def console_telemetry_event(event_name, properties=None, module=None):
        """Production telemetry event with structured logging."""
        timestamp = datetime.now().isoformat()
        prefix = f"[{module}]" if module else "[GraphOps]"
        props_str = f" | {properties}" if properties else ""
        print(f"{timestamp} TELEMETRY {prefix} {event_name}{props_str}")

class GraphOperations:
    def __init__(self, user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"], calendar_response_fields=["subject", "start", "end", "location", "attendees"]):
        """
        Initialize the GraphOperations class.
        This class provides methods to interact with Microsoft Graph API.
        """
        self.user_response_fields = user_response_fields
        self.calendar_response_fields = calendar_response_fields

        # Replace with your values
        self.tenant_id = os.environ.get("ENTRA_GRAPH_APPLICATION_TENANT_ID")
        # Deferred validation - will check when client is actually needed
        # if self.tenant_id is None:
        #     raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_TENANT_ID' to your Azure tenant ID.")

        self.client_id = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_ID")
        # if self.client_id is None:
        #     raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_ID' to your Azure application client ID.")

        self.client_secret = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_SECRET")
        # if self.client_secret is None:
        #     raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_SECRET' to your Azure application client secret.")

        self.graph_client = None  # Lazy initialization
        
        console_info(f"Graph Operations initialized (telemetry: {'enabled' if TELEMETRY_AVAILABLE else 'disabled'})", "GraphOps")

    def _get_client(self) -> GraphServiceClient:
        """Get or create the Graph client with lazy initialization."""
        if self.graph_client is None:
            try:
                # print("🔄 Initializing Microsoft Graph client...")
                
                # Validate credentials when actually needed
                if self.tenant_id is None:
                    raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_TENANT_ID' to your Azure tenant ID.")
                if self.client_id is None:
                    raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_ID' to your Azure application client ID.")
                if self.client_secret is None:
                    raise ValueError("Please set the environment variable 'ENTRA_GRAPH_APPLICATION_CLIENT_SECRET' to your Azure application client secret.")
                
                credential = ClientSecretCredential(self.tenant_id, self.client_id, self.client_secret)
                # scopes = ["https://graph.microsoft.com/.default"] # Or specific scopes like "Chat.ReadWrite"
                # Add chat.readAll for read access to all chats to scope
                scope = ["https://graph.microsoft.com/.default"]
                self.graph_client = GraphServiceClient(credential, scope)
                # print("✓ Microsoft Graph client initialized successfully!")
            except Exception as e:
                print(f"❌ Failed to initialize Microsoft Graph client: {e}")
                # print("🔧 Please check your ENTRA_GRAPH_APPLICATION_* environment variables")
                raise
        return self.graph_client
    
    # Get Current Date and Time
    def get_current_datetime(self) -> str:
        return datetime.now().isoformat()
    
    def get_telemetry_status(self) -> Dict[str, Any]:
        """Get comprehensive telemetry status."""
        return {
            "telemetry_available": TELEMETRY_AVAILABLE,
            "telemetry_disabled": TELEMETRY_EXPLICITLY_DISABLED,
            "mode": "production_fast_load",
            "startup_time": "optimized",
            "hanging_prevention": "enabled"
        }
    
    def _has_valid_mailbox_properties(self, user: User) -> bool:
        """
        Quick client-side check for mailbox indicators.
        This is a preliminary check before making API calls for full validation.
        
        Args:
            user (User): User object to check
            
        Returns:
            bool: True if user appears to have mailbox properties, False otherwise
        """
        # Only check if user has mail property (indicates Exchange mailbox assignment)
        if not hasattr(user, 'mail') or not user.mail:
            return False
            
        return True

    # Helper method to validate if a user has a valid mailbox for calendar operations
    @trace_async_method("validate_user_mailbox")
    async def validate_user_mailbox(self, user_id: str) -> dict:
        """
        Validate if a user has a valid mailbox for calendar operations.
        
        Args:
            user_id (str): The ID of the user to validate
            
        Returns:
            dict: Validation result with 'valid', 'message', and 'user_info' keys
        """
        try:
            # First check if user exists and get their properties
            user = await self.get_user_by_user_id(user_id)
            
            if not user:
                return {
                    'valid': False,
                    'message': f'User {user_id} not found in the directory',
                    'user_info': None
                }
            # Check for valid Exchange Online mailbox using Microsoft Graph API
            # A "valid mailbox" means the user has an Exchange Online mailbox provisioned
            # We'll test mailbox access using the recommended Graph API endpoints
            
            # Test for valid Exchange Online mailbox using Microsoft Graph API
            # Try multiple endpoints to determine if user has a valid mailbox
            try:
                # Method 1: Try to access mailbox settings (recommended approach)
                # If user doesn't have a mailbox, this will return ErrorMailboxNotEnabled
                mailbox_settings = await self._get_client().users.by_user_id(user_id).mailbox_settings.get()
                
                if mailbox_settings:
                    return {
                        'valid': True,
                        'message': f'User {user.display_name} ({user_id}) has a valid Exchange Online mailbox',
                        'user_info': user
                    }
                    
            except Exception as mailbox_error:
                error_message = str(mailbox_error)
                
                # Check for specific mailbox-related errors
                if "MailboxNotEnabledForRESTAPI" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {user.display_name} ({user_id}) mailbox is not enabled for REST API access (likely on-premise or inactive)',
                        'user_info': user
                    }
                elif "ErrorMailboxNotEnabled" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {user.display_name} ({user_id}) does not have an Exchange Online mailbox provisioned',
                        'user_info': user
                    }
                elif "Forbidden" in error_message or "403" in error_message:
                    return {
                        'valid': False,
                        'message': f'Access denied to mailbox for user {user.display_name} ({user_id}) - insufficient permissions',
                        'user_info': user
                    }
                elif "NotFound" in error_message or "404" in error_message:
                    return {
                        'valid': False,
                        'message': f'User {user.display_name} ({user_id}) or mailbox not found',
                        'user_info': user
                    }
                else:
                    # Try fallback method: check messages endpoint
                    try:
                        # Method 2: Try to access messages (alternative approach)
                        # This is another way to test for valid mailbox
                        messages_response = await self._get_client().users.by_user_id(user_id).messages.get()
                        
                        # If we can access messages (even if empty), mailbox is valid
                        return {
                            'valid': True,
                            'message': f'User {user.display_name} ({user_id}) has a valid Exchange Online mailbox (verified via messages endpoint)',
                            'user_info': user
                        }
                        
                    except Exception as messages_error:
                        messages_error_str = str(messages_error)
                        
                        if "MailboxNotEnabledForRESTAPI" in messages_error_str or "ErrorMailboxNotEnabled" in messages_error_str:
                            return {
                                'valid': False,
                                'message': f'User {user.display_name} ({user_id}) does not have a valid Exchange Online mailbox',
                                'user_info': user
                            }
                        else:
                            # If both methods fail with non-mailbox errors, assume valid but with access issues
                            return {
                                'valid': False,
                                'message': f'Cannot verify mailbox for user {user.display_name} ({user_id}): {mailbox_error}',
                                'user_info': user
                            }
                    
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error validating user {user_id}: {e}',
                'user_info': None
            }

    # Get a user by user ID
    @trace_async_method("get_user_by_user_id")
    async def get_user_by_user_id(self, user_id: str) -> User | None:
        try:
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                    
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            query_params.filter = f"id eq '{user_id}'"
            # Limit results for testing
            query_params.top = 1
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value') and response.value:
                # response.value is a list, get the first (and should be only) user
                user = response.value[0]
                return user
            else:
                return None
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
            
    # Get a users manager by user ID
    @trace_async_method("get_users_manager_by_user_id")
    async def get_users_manager_by_user_id(self, user_id: str) -> DirectoryObject  | None:
        try:
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                        
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            query_params.filter = f"id eq '{user_id}'"
            # Limit results for testing
            query_params.top = 1
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value') and response.value:
                # response.value is a list, get the first (and should be only) user
                user = response.value[0]
                
                # Fetch manager details if available
                try:
                    manager = await self._get_client().users.by_user_id(user_id).manager.get()
                except Exception as manager_error:
                    print(f"Could not fetch manager for user {user_id}: {manager_error}")
                    manager = None
                    
                return manager
            else:
                return None
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Get direct reports for a user by user ID
    @trace_async_method("get_direct_reports_by_user_id")
    async def get_direct_reports_by_user_id(self, user_id: str) -> List[User]:
        """
        Get direct reports for a specific user.
        
        Args:
            user_id (str): The ID of the user to get direct reports for
            
        Returns:
            List[User]: List of User objects representing direct reports, empty list if none found
        """
        try:

            
            # Fetch direct reports details
            direct_reports_response = await self._get_client().users.by_user_id(user_id).direct_reports.get()

            if not direct_reports_response or not hasattr(direct_reports_response, 'value'):
                return []
            
            direct_reports = direct_reports_response.value
            if not direct_reports:
                return []
            
            return direct_reports
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_direct_reports_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
                
    # Get all users in the Microsoft 365 Tenant Entra Directory
    @trace_async_method("get_all_users")
    async def get_all_users(self, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        """
        Get all users from the Microsoft 365 tenant directory.
        
        Args:
            max_results (int): Maximum number of results to return
            exclude_inactive_mailboxes (bool): If True, filters out users without active mailboxes
            
        Returns:
            List[User]: List of User objects, optionally filtered to exclude users without mailboxes
        """
        try:
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            
            # No API-level filtering - rely on validate_user_mailbox for verification
            
            # Limit results for testing
            query_params.top = max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if exclude_inactive_mailboxes and users:
                    # Client-side filtering using mailbox property validation only
                    original_count = len(users)
                    users = [user for user in users if self._has_valid_mailbox_properties(user)]
                    filtered_count = original_count - len(users)
                    print(f"📊 Retrieved {original_count} users, filtered out {filtered_count} without mail addresses, {len(users)} users remaining")
                else:
                    print(f"📊 Retrieved {len(users)} users (no mailbox filtering applied)")
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Get all conference room resources 
    async def get_all_conference_rooms(self, max_results) -> List[User]:
        """
        Get all conference room resources in the Microsoft 365 tenant.
        
        Args:
            max_results (int): Maximum number of results to return
            
        Returns:
            List[User]: List of User objects representing conference rooms
        """
        try:
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Filter for conference rooms (typically have a specific naming convention or email domain)
            query_params.filter = "startswith(mail, 'room') or startswith(mail, 'conf')"
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            
            # Limit results for testing
            query_params.top = max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if not users:
                    print("No conference rooms found")
                    return []
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_all_conference_rooms: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []

    async def get_conference_room_availability(self, room_id: str, start_time: datetime, end_time: datetime) -> bool:
        try:
            # Call the Graph API to get the availability of the conference room
            response = await self._get_client().users[room_id].calendar.get_schedule(
                start_time=start_time,
                end_time=end_time
            )
            return response.value
        except Exception as e:
            print(f"Error in get_conference_room_availability: {e}")
            return False

    async def get_conference_room_details_by_id(self, room_id: str) -> dict:
        """
        Get detailed information about a specific conference room by its ID.
        
        Args:
            room_id (str): The unique ID of the conference room to retrieve details for
            
        Returns:
            dict: Detailed information about the specified conference room
        """
        try:
            # Fetch the conference room details
            room = await self._get_client().users.by_user_id(room_id).get()
            
            if not room:
                return {}
            
            # Convert to dict for easier handling, checking for attribute existence
            room_details = {
                'id': room.id,
                'displayName': room.display_name,
                'mail': room.mail,
                'userPrincipalName': getattr(room, 'user_principal_name', None),
                'jobTitle': getattr(room, 'job_title', None),
                'department': getattr(room, 'department', None)
            }
            
            # Check for capacity attribute (might not exist for User objects representing rooms)
            if hasattr(room, 'capacity'):
                room_details['capacity'] = room.capacity
            else:
                room_details['capacity'] = None
            
            # Check for location attribute and handle it safely
            if hasattr(room, 'location') and room.location:
                try:
                    room_details['location'] = room.location.__dict__
                except:
                    room_details['location'] = str(room.location) if room.location else None
            else:
                room_details['location'] = None
            
            return room_details
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_conference_room_details_by_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return {}
        
    # Get all departments
    async def get_all_departments(self, max_results) -> List[str]:
        try:
            departments = set()  # Use a set to avoid duplicates

            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                        
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Limit results for testing
            query_params.top = max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                for user in users:
                    department = user.department
                    if department:
                        departments.add(department)
                return list(departments)
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
        
    # Get all users by department
    async def get_users_by_department(self, department: str, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        """
        Get users by department with optional inactive mailbox filtering.
        
        Args:
            department (str): Department name to filter by
            max_results (int): Maximum number of results to return
            exclude_inactive_mailboxes (bool): If True, filters out users without active mailboxes
            
        Returns:
            List[User]: List of User objects in the specified department
        """
        if not department:
            return []
        try:
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Build filter for department only
            query_params.filter = f"department eq '{department}'"
            print(f"Applied department filter: {query_params.filter}")
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Limit results for testing
            query_params.top = max_results
            
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )

            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if exclude_inactive_mailboxes and users:
                    # Client-side filtering using mailbox property validation only
                    original_count = len(users)
                    users = [user for user in users if self._has_valid_mailbox_properties(user)]
                    filtered_count = original_count - len(users)
                    print(f"📊 Retrieved {original_count} users from {department}, filtered out {filtered_count} without mail addresses, {len(users)} users remaining")
                else:
                    print(f"📊 Retrieved {len(users)} users from {department} (no mailbox filtering applied)")
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_users_by_department: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
        
    async def search_users(self, filter, max_results, exclude_inactive_mailboxes: bool = True) -> List[User]:
        """
        Search for users with optional filtering to exclude users without active mailboxes.
        
        Args:
            filter (str): OData filter string for user search
            max_results (int): Maximum number of results to return
            exclude_inactive_mailboxes (bool): If True, filters out users without active mailboxes
            
        Returns:
            List[User]: List of User objects matching the filter criteria
        """
        try:
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Use only the provided filter - no additional accountEnabled filtering
            if filter:
                query_params.filter = filter
                # print(f"Applied filter: {query_params.filter}")
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Limit results for testing
            query_params.top = max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await self._get_client().users.get(request_configuration=request_configuration)

            if hasattr(response, 'value'):
                users = response.value
                
                if exclude_inactive_mailboxes and users:
                    # Client-side filtering using mailbox property validation only
                    original_count = len(users)
                    users = [user for user in users if self._has_valid_mailbox_properties(user)]
                    filtered_count = original_count - len(users)
                    print(f"📊 Search returned {original_count} users, filtered out {filtered_count} without mail addresses, {len(users)} users remaining")
                else:
                    print(f"📊 Search returned {len(users)} users (no mailbox filtering applied)")
                
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.search_users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []

    # Get uses mailbox settings by user ID
    async def get_user_mailbox_settings_by_user_id(self, user_id: str) -> dict:
        """
        Get mailbox settings for a user by user ID.
        
        Args:
            user_id (str): The ID of the user to retrieve mailbox settings for
            
        Returns:
            dict: Mailbox settings as a dictionary, or None if not found
        """
        try:
            mailbox_settings = await self._get_client().users.by_user_id(user_id).mailbox_settings.get()
            if mailbox_settings:
                return mailbox_settings.__dict__  # Convert to dict for easier handling
            else:
                return None
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_user_mailbox_settings_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    async def get_users_city_state_zipcode_by_user_id(self, user_id: str) -> dict:
        """
        Get city, state, and zipcode for a user by user ID.
        
        Args:
            user_id (str): The ID of the user to retrieve location details for

        Returns:
            dict: Dictionary with city, state, and zipcode, or None if not found
        """
        try:
            from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
            
            # Configure the request with proper query parameters
            query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters()
            query_params.select = ["city", "state", "postalCode", "countryOrRegion"]
            
            request_configuration = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            user = await self._get_client().users.by_user_id(user_id).get(request_configuration=request_configuration)
            if not user:
                return None

            # Extract location details from the user object
            location = {
                'city': getattr(user, 'city', None),
                'state': getattr(user, 'state', None),
                'zipcode': getattr(user, 'postal_code', None)
            }

            return location

        except Exception as e:
            print(f"An error occurred with GraphOperations.get_users_city_state_zipcode_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None
            return None
        
    # Get user preferences by user ID
    async def get_user_preferences_by_user_id(self, user_id: str) -> User | None:
        """
        Get user preferences by user ID.
        
        Args:
            user_id (str): The ID of the user to retrieve preferences for
            
        Returns:
            User: User object with preferences, or None if not found
        """
        try:
            # Fetch user details
            user = await self.get_user_by_user_id(user_id)
            if not user:
                return None
            
            # Return the user object with preferences
            return user
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_user_preferences_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None
        
    # Calendar Operations
    # Get calendar events for a user by user ID with optional date range
    async def get_calendar_events_by_user_id(self, user_id: str, start_date: datetime = None, end_date: datetime = None) -> DirectoryObject  | None:
        try:
            # First validate the user's mailbox
            validation_result = await self.validate_user_mailbox(user_id)
            
            if not validation_result['valid']:
                print(f"❌ Mailbox validation failed: {validation_result['message']}")
                return None
            
            print(f"✅ Mailbox validation passed: {validation_result['message']}")
            user = validation_result['user_info']
            
            # If we have a valid user, proceed with calendar access
            try:
                from msgraph.generated.users.item.calendar.events.events_request_builder import EventsRequestBuilder
                
                # Configure query parameters to order by start date
                events_query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters()
                events_query_params.orderby = ["start/dateTime"]
                events_query_params.select = self.calendar_response_fields
                
                # Add date range filter if provided
                filters = []
                if start_date:
                    filters.append(f"start/dateTime ge '{start_date.isoformat()}'")
                if end_date:
                    filters.append(f"end/dateTime le '{end_date.isoformat()}'")

                if filters:
                    events_query_params.filter = " and ".join(filters)
                
                events_request_config = EventsRequestBuilder.EventsRequestBuilderGetRequestConfiguration(
                    query_parameters=events_query_params
                )

                event_response = await self._get_client().users.by_user_id(user_id).calendar.events.get(request_configuration=events_request_config)
                if hasattr(event_response, 'value') and event_response.value:
                    events = event_response.value
                    print(f"📅 Retrieved {len(events)} calendar events for user {user.display_name}")
                else:
                    events = []
                    print(f"📅 No calendar events found for user {user.display_name}")
            except Exception as events_error:
                # Enhanced error handling for specific Graph API errors
                error_message = str(events_error)
                print(f"Could not fetch events for user {user_id}: ")
                print(f"        APIError")
                print(f"        Code: {getattr(events_error, 'code', 'Unknown')}")
                print(f"        message: {getattr(events_error, 'message', 'None')}")
                print(f"        error: {getattr(events_error, 'error', events_error)}")
                print(f"        ")
                
                # Provide specific guidance for common errors
                if "MailboxNotEnabledForRESTAPI" in error_message:
                    print("🔍 DIAGNOSIS: Mailbox Not Enabled for REST API")
                    print("   This indicates the user's mailbox is either:")
                    print("   • Inactive or disabled")
                    print("   • Soft-deleted (recently removed)")
                    print("   • Hosted on-premise (hybrid setup)")
                    print("   • Not licensed for Exchange Online")
                    print("")
                    print("💡 SOLUTIONS:")
                    print("   1. Verify the user exists and is active in Azure AD")
                    print("   2. Check if user has an Exchange Online license")
                    print("   3. Ensure mailbox is not soft-deleted")
                    print("   4. For hybrid environments, verify cloud mailbox setup")
                    print("   5. Contact admin to enable the mailbox for cloud access")
                elif "Forbidden" in error_message or "403" in error_message:
                    print("🔒 DIAGNOSIS: Permission Denied")
                    print("   The application lacks required permissions to access this user's calendar")
                    print("💡 SOLUTIONS:")
                    print("   1. Ensure app has 'Calendars.Read' or 'Calendars.ReadWrite' permissions")
                    print("   2. Admin consent may be required for application permissions")
                    print("   3. Check if user has restricted their calendar sharing")
                elif "NotFound" in error_message or "404" in error_message:
                    print("👤 DIAGNOSIS: User or Calendar Not Found")
                    print("   The user ID may be invalid or the user doesn't have a calendar")
                    print("💡 SOLUTIONS:")
                    print("   1. Verify the user ID is correct")
                    print("   2. Check if the user exists in the tenant")
                    print("   3. Ensure the user has an Exchange Online mailbox")
                
                events = None

            return events
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_calendar_events_by_user_id: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Create calendar event for a list of attendees and optional attendees
    async def create_calendar_event(self, user_id: str, subject: str, start: str, end: str, location: str = None, attendees: List[str] = None, optional_attendees: List[str] = None) -> Event:
        try:
            
            # Create the event object
            event = Event(
                subject=subject,
                start=DateTimeTimeZone(date_time=start, time_zone="UTC"),
                end=DateTimeTimeZone(date_time=end, time_zone="UTC"),
                location=Location(display_name=location) if location else None,
                attendees=[]
            )
            
            # Add required attendees
            if attendees:
                for attendee in attendees:
                    email_address = EmailAddress(address=attendee)
                    event.attendees.append(Attendee(email_address=email_address, type="required"))
            
            # Add optional attendees
            if optional_attendees:
                for attendee in optional_attendees:
                    email_address = EmailAddress(address=attendee)
                    event.attendees.append(Attendee(email_address=email_address, type="optional"))
            
            # Create the event in the user's calendar
            created_event = await self._get_client().users.by_user_id(user_id).calendar.events.post(event)
            return created_event
            
        except Exception as e:
            print(f"An error occurred while creating calendar event: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None

    # Get and display conference room events
    async def get_conference_room_events(self, conference_rooms: List[User]) -> List[dict]:
        """
        Get and display calendar events for a list of conference rooms.
        
        Args:
            conference_rooms (List[User]): List of conference room User objects
            
        Returns:
            List[dict]: List of conference room objects with their events
        """
        try:
            conference_rooms_with_events = []
            
            for room in conference_rooms:
                print(60 * "=")
                print(f"ID: {room.id}")
                print(f"Display Name: {room.display_name}")
                print(f"User Principal Name: {room.user_principal_name}")
                print(f"Mail: {room.mail}")
                print(f"Job Title: {room.job_title}")
                print(f"Department: {room.department}")
                print(f"Manager: {room.manager}")

                # Get calendar events for this room
                get_calendar_events = await self.get_calendar_events_by_user_id(room.id)
                
                # Process events into a structured format
                events_list = []
                if get_calendar_events:
                    print(f"Found {len(get_calendar_events)} calendar events for room {room.display_name}")
                    for event in get_calendar_events:
                        # Print event details (keeping original console output)
                        print(f"Event Subject: {event.subject}")
                        print(f"Start: {event.start.date_time} {event.start.time_zone}")
                        print(f"End: {event.end.date_time} {event.end.time_zone}")
                        print(f"Location: {event.location.display_name if event.location else 'No location'}")
                        print("Attendees:")
                        for attendee in event.attendees:
                            print(f"  - {attendee.email_address.address} ({attendee.type})")
                        
                        # Create structured event data
                        attendees_list = []
                        if event.attendees:
                            for attendee in event.attendees:
                                attendees_list.append({
                                    "email": attendee.email_address.address,
                                    "type": attendee.type,
                                    "name": getattr(attendee.email_address, 'name', '') or attendee.email_address.address
                                })
                        
                        event_data = {
                            "id": getattr(event, 'id', ''),
                            "subject": event.subject or '',
                            "start": {
                                "date_time": event.start.date_time,
                                "time_zone": event.start.time_zone
                            },
                            "end": {
                                "date_time": event.end.date_time,
                                "time_zone": event.end.time_zone
                            },
                            "location": event.location.display_name if event.location else 'No location',
                            "attendees": attendees_list
                        }
                        events_list.append(event_data)
                else:
                    print(f"No calendar events found for room {room.display_name}")
                
                # Create structured room data with events
                room_data = {
                    "id": room.id,
                    "display_name": room.display_name,
                    "user_principal_name": room.user_principal_name,
                    "mail": room.mail,
                    "job_title": room.job_title,
                    "department": room.department,
                    "manager": room.manager,
                    "events": events_list,
                    "event_count": len(events_list)
                }
                conference_rooms_with_events.append(room_data)
            
            return conference_rooms_with_events
                            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_conference_room_events: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
      
# # Example usage:

async def main():
    ops = GraphOperations(
        user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
        calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
    )
    # get_all_conference_rooms
    print(60 * "=")
    print("Getting all conference rooms in the Microsoft 365 Tenant Entra Directory...")
    print(60 * "=")
    conference_rooms = await ops.get_all_conference_rooms(100)
    if conference_rooms:
        await ops.get_conference_room_events(conference_rooms)
    else:
        print("No conference rooms found.")




    # print("Get User Mailbox Settings by User ID")
    # mailbox_settings = await ops.get_user_mailbox_settings_by_user_id("69149650-b87e-44cf-9413-db5c1a5b6d3f")
    # if mailbox_settings:
    #     for key, value in mailbox_settings.items():
    #         print(f"{key}: {value}")
    # print(60 * "=")

    # print("Get User Preferences by User ID")
    # preferences = await ops.get_user_preferences_by_user_id("69149650-b87e-44cf-9413-db5c1a5b6d3f")
    # if preferences:
    #     for key, value in preferences.__dict__.items():
    #         print(f"{key}: {value}")


    # Example usage for other methods (uncomment as needed):
    
    # print(60 * "=")
    # print("Get User by User ID")
    # print(60 * "=")
    # user_id = "69149650-b87e-44cf-9413-db5c1a5b6d3f"  # Example user ID
    # user = await ops.get_user_by_user_id(user_id)
    # print(60 * "=")
    # print(f"ID: {user.id}")
    # print(f"Given Name: {user.given_name}")
    # print(f"Surname: {user.surname}")
    # print(f"Display Name: {user.display_name}")
    # print(f"User Principal Name: {user.user_principal_name}")
    # print(f"Mail: {user.mail}")
    # print(f"Job Title: {user.job_title}")
    # print(f"Department: {user.department}")
    # print(f"Manager: {user.manager}")
    
    # print(60 * "=")
    # print("Getting all users in the Microsoft 365 Tenant Entra Directory...")
    # print(60 * "=")
    # users = await ops.get_all_users(100, exclude_inactive_mailboxes=True)  # Filter out users without mailboxes
    # for user in users:
    #     print(60 * "=")
    #     print(f"ID: {user.id}")
    #     print(f"Given Name: {user.given_name}")
    #     print(f"Surname: {user.surname}")
    #     print(f"Display Name: {user.display_name}")
    #     print(f"User Principal Name: {user.user_principal_name}")
    #     print(f"Mail: {user.mail}")
    #     print(f"Job Title: {user.job_title}")
    #     print(f"Department: {user.department}")
    #     print(f"Manager: {user.manager}")
    
    
    # # Get the system administrators manager
    # print(60 * "=")
    # print("Getting the system administrator's manager...")
    # print(60 * "=")
    # user = await ops.get_users_manager_by_user_id("69149650-b87e-44cf-9413-db5c1a5b6d3f")
    # print(60 * "=")
    # print(f"ID: {user.id}")
    # print(f"Given Name: {user.given_name}")
    # print(f"Surname: {user.surname}")
    # print(f"Display Name: {user.display_name}")
    # print(f"User Principal Name: {user.user_principal_name}")
    # print(f"Mail: {user.mail}")
    # print(f"Job Title: {user.job_title}")
    # print(f"Department: {user.department}")
    # print(f"Manager: {user.manager}")

    # # Get Prita's Direct Reports
    # print(60 * "=")
    # print("Getting Prita's (IT Manager) direct reports...")
    # print(60 * "=")
    # direct_reports = await ops.get_direct_reports_by_user_id("5d6bc6b4-4294-4994-8206-8be6ee865407")
    # for user in direct_reports:
    #     print(60 * "=")
    #     print(f"ID: {user.id}")
    #     print(f"Given Name: {user.given_name}")
    #     print(f"Surname: {user.surname}")
    #     print(f"Display Name: {user.display_name}")
    #     print(f"User Principal Name: {user.user_principal_name}")
    #     print(f"Mail: {user.mail}")
    #     print(f"Job Title: {user.job_title}")
    #     print(f"Department: {user.department}")
    #     print(f"Manager: {user.manager}")

    # # Get all departments
    # print(60 * "=")
    # print("Getting all departments in the Microsoft 365 Tenant Entra Directory...")
    # print(60 * "=")
    # departments = await ops.get_all_departments(100)
    # print(f"Found {len(departments)} departments:")
    # for dept in departments:
    #     print(f"  - {dept}")

    # # Get all users by department
    # print(60 * "=")
    # print("Getting all users in the Information Technology department...")
    # print(60 * "=")
    # it_users = await ops.get_users_by_department("Information Technology", 100, exclude_inactive_mailboxes=True)
    # print(f"Found {len(it_users)} users in the Information Technology department:")
    # for user in it_users:
    #    print(f"  - {user.display_name} ({user.user_principal_name})")

    # Get user events by user ID
    # print(60 * "=")
    # print("Getting events for user by user ID...")
    # print(60 * "=")
    # user_id = "69149650-b87e-44cf-9413-db5c1a5b6d3f"  # Example user ID
    
    # # Example with date range (ISO 8601 format)
    # start_date = "2025-07-01T00:00:00Z"  # Start of July 2025
    # end_date = "2025-07-31T23:59:59Z"    # End of July 2025
    
    # events = await ops.get_calendar_events_by_user_id(user_id, start_date, end_date)
    # if events:
    #     for event in events:
    #         print(60 * "=")
    #         print(f"Subject: {event.subject}")
    #         print(f"Start: {event.start}")
    #         print(f"End: {event.end}")
    #         print(f"Location: {event.location}")
    #         print(f"Attendees: {event.attendees}")
    # else:
    #     print("No events found in the specified date range.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


