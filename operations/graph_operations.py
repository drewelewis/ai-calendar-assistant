from datetime import datetime
import os
import traceback
import asyncio
from typing import List
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

# Replace with your values
tenant_id = os.getenv("ENTRA_GRAPH_APPLICATION_TENANT_ID")
client_id = os.getenv("ENTRA_GRAPH_APPLICATION_CLIENT_ID")
client_secret = os.getenv("ENTRA_GRAPH_APPLICATION_CLIENT_SECRET")

credential = ClientSecretCredential(tenant_id, client_id, client_secret)

# scopes = ["https://graph.microsoft.com/.default"] # Or specific scopes like "Chat.ReadWrite"
# Add chat.readAll for read access to all chats to scope
scope = ["https://graph.microsoft.com/.default"]
graph_client = GraphServiceClient(credential, scope)

class GraphOperations:
    def __init__(self, user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"], calendar_response_fields=["subject", "start", "end", "location", "attendees"]):
        """
        Initialize the GraphOperations class.
        This class provides methods to interact with Microsoft Graph API.
        """
        self.user_response_fields = user_response_fields
        self.calendar_response_fields = calendar_response_fields

    def _get_client(self) -> GraphServiceClient:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        # scopes = ["https://graph.microsoft.com/.default"] # Or specific scopes like "Chat.ReadWrite"
        # Add chat.readAll for read access to all chats to scope
        scope = ["https://graph.microsoft.com/.default"]
        graph_client = GraphServiceClient(credential, scope)
        return graph_client
    
    # Get Current Date and Time
    def get_current_datetime(self) -> str:
        return datetime.now().isoformat()

    # Get a user by user ID
    async def get_user_by_user_id(self, user_id: str) -> User | None:
        try:
            graph_client = self._get_client()
            # Configure the request with proper query parameters

            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                    
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            query_params.filter = f"id eq '{user_id}'"
            # Limit results for testing
            query_params.top = 1
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await graph_client.users.get(request_configuration=request_configuration)

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
    async def get_users_manager_by_user_id(self, user_id: str) -> DirectoryObject  | None:
        try:
            graph_client = self._get_client()
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
            response = await graph_client.users.get(request_configuration=request_configuration)

            if hasattr(response, 'value') and response.value:
                # response.value is a list, get the first (and should be only) user
                user = response.value[0]
                
                # Fetch manager details if available
                try:
                    manager = await graph_client.users.by_user_id(user_id).manager.get()
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
    async def get_direct_reports_by_user_id(self, user_id: str) -> List[User]:
        """
        Get direct reports for a specific user.
        
        Args:
            user_id (str): The ID of the user to get direct reports for
            
        Returns:
            List[User]: List of User objects representing direct reports, empty list if none found
        """
        try:
            graph_client = self._get_client()
            
            # Fetch direct reports details
            direct_reports_response = await graph_client.users.by_user_id(user_id).direct_reports.get()
            
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
    async def get_all_users(self, max_results) -> List[User]:
        try:
            graph_client = self._get_client()
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
            response = await graph_client.users.get(request_configuration=request_configuration)
        
            if hasattr(response, 'value'):
                users = response.value
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Get all departments
    # Get all users in the Microsoft 365 Tenant Entra Directory
    async def get_all_departments(self, max_results) -> List[str]:
        try:
            departments = set()  # Use a set to avoid duplicates
            graph_client = self._get_client()
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
            response = await graph_client.users.get(request_configuration=request_configuration)
        
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
    async def get_users_by_department(self, department: str, max_results) -> List[User]:
        if not department:
            return []
        try:
            graph_client = self._get_client()
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Add filter for department
            if department:
                query_params.filter = f"department eq '{department}'"
                print(f"Applied filter: {query_params.filter}")
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Limit results for testing
            query_params.top = max_results
            
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            response = await graph_client.users.get(request_configuration=request_configuration)
        
            if hasattr(response, 'value'):
                users = response.value
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.get_users_by_department: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
        
    async def search_users(self, filter, max_results) -> List[User]:
        try:
            graph_client = self._get_client()
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
            
            # Add filter if provided
            if filter:
                query_params.filter = filter
                print(f"Applied filter: {filter}")
            
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.user_response_fields
            # Limit results for testing
            query_params.top = max_results
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            response = await graph_client.users.get(request_configuration=request_configuration)
        
            if hasattr(response, 'value'):
                users = response.value
                return users
            else:
                return []
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.search_users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []

    # Calendar Operations
    # Get calendar events for a user by user ID with optional date range
    async def get_calendar_events_by_user_id(self, user_id: str, start_date: str = None, end_date: str = None) -> DirectoryObject  | None:
        try:
            graph_client = self._get_client()
            # Configure the request with proper query parameters
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()
                        
            # Select specific fields to reduce response size and ensure we get what we need
            query_params.select = self.calendar_response_fields
            query_params.filter = f"id eq '{user_id}'"
            # Limit results for testing
            query_params.top = 1
            request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            user_response = await graph_client.users.get(request_configuration=request_configuration)

            if hasattr(user_response, 'value') and user_response.value:
                # response.value is a list, get the first (and should be only) user
                user = user_response.value[0]

                # Fetch event details if available
                try:
                    from msgraph.generated.users.item.calendar.events.events_request_builder import EventsRequestBuilder
                    
                    # Configure query parameters to order by start date
                    events_query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters()
                    events_query_params.orderby = ["start/dateTime"]
                    events_query_params.select = self.calendar_response_fields
                    
                    # Add date range filter if provided
                    filters = []
                    if start_date:
                        filters.append(f"start/dateTime ge '{start_date}'")
                    if end_date:
                        filters.append(f"end/dateTime le '{end_date}'")
                    
                    if filters:
                        events_query_params.filter = " and ".join(filters)
                    
                    events_request_config = EventsRequestBuilder.EventsRequestBuilderGetRequestConfiguration(
                        query_parameters=events_query_params
                    )
                    
                    event_response = await graph_client.users.by_user_id(user_id).calendar.events.get(request_configuration=events_request_config)
                    if hasattr(event_response, 'value') and event_response.value:
                        events = event_response.value
                    else:
                        events = []
                except Exception as events_error:
                    print(f"Could not fetch events for user {user_id}: {events_error}")
                    events = None

                return events
            else:
                return None
            
        except Exception as e:
            print(f"An error occurred with GraphOperations.users: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return []
    
    # Create calendar event for a list of attendees and optional attendees
    async def create_calendar_event(self, user_id: str, subject: str, start: str, end: str, location: str = None, attendees: List[str] = None, optional_attendees: List[str] = None) -> Event:
        try:
            graph_client = self._get_client()
            
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
            created_event = await graph_client.users.by_user_id(user_id).calendar.events.post(event)
            return created_event
            
        except Exception as e:
            print(f"An error occurred while creating calendar event: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None
      
# # Example usage:

if __name__ == "__main__":
    ops = GraphOperations(
        user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "manager"],
        calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
    )
    # print(60 * "=")
    # print("Get User by User ID")
    # print(60 * "=")
    # user_id = "69149650-b87e-44cf-9413-db5c1a5b6d3f"  # Example user ID
    # user = asyncio.run(ops.get_user_by_user_id(user_id))
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
    # users = asyncio.run(ops.get_all_users(100))
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
    # user = asyncio.run(ops.get_users_manager_by_user_id("69149650-b87e-44cf-9413-db5c1a5b6d3f"))
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
    # direct_reports = asyncio.run(ops.get_direct_reports_by_user_id("5d6bc6b4-4294-4994-8206-8be6ee865407"))
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
    # departments = asyncio.run(ops.get_all_departments(100))
    # print(f"Found {len(departments)} departments:")
    # for dept in departments:
    #     print(f"  - {dept}")

    # # Get all users by department
    # print(60 * "=")
    # print("Getting all users in the Information Technology department...")
    # print(60 * "=")
    # it_users = asyncio.run(ops.get_users_by_department("Information Technology", 100))
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
    
    # events = asyncio.run(ops.get_calendar_events_by_user_id(user_id, start_date, end_date))
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

