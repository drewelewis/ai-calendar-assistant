# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import uuid
import logging
from typing import Annotated, Dict, List, Optional, Any
import datetime
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager
from plugins.graph_plugin import GraphPlugin
from plugins.azure_maps_plugin import AzureMapsPlugin
from prompts.graph_prompts import prompts
from utils.teams_utilities import TeamsUtilities

# Import telemetry components
from telemetry.config import initialize_telemetry, get_telemetry
from telemetry.decorators import trace_async_method, measure_performance, TelemetryContext
from telemetry.token_tracking import add_token_span_attributes, record_token_metrics
from telemetry.console_output import console_info, console_debug, console_telemetry_event

load_dotenv(override=True)

class MultiAgentOrchestrator:
    """
    Multi-Agent AI Calendar Assistant Orchestrator
    
    This orchestrator manages multiple specialized agents:
    - Proxy Agent: Main conversation handler and task router
    - Calendar Agent: Handles calendar operations and scheduling
    - Directory Agent: Manages user searches and organizational data
    - Location Agent: Handles location-based searches and mapping
    """
    
    def __init__(self, session_id: str = None):
        # Validate session_id is provided
        if not session_id:
            error_msg = "❌ Session ID is required for MultiAgentOrchestrator initialization"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        self.session_id = session_id
        
        # Initialize telemetry
        self._initialize_telemetry()
        
        # Load environment variables
        self._load_environment()
        
        # Initialize CosmosDB if available
        self._initialize_cosmos()
        
        # Initialize Teams utilities
        self.teams_utils = TeamsUtilities()
        
        # Create the kernel
        self.kernel = Kernel()
        
        # Add Azure OpenAI service
        self._setup_openai_service()
        
        # Create specialized agents
        self.agents = self._create_agents()
        
        # Create agent group chat
        self.group_chat = self._create_group_chat()
        
        self.logger.info(f"✅ Multi-Agent Orchestrator initialized for session: {self.session_id}")
    
    def _initialize_telemetry(self):
        """Initialize telemetry and logging."""
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant-multi-agent")
        service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")
        
        telemetry_success = initialize_telemetry(
            service_name=service_name,
            service_version=service_version
        )
        
        if telemetry_success:
            self.telemetry = get_telemetry()
            self.metrics = self.telemetry.create_custom_metrics() if self.telemetry else {}
            self.logger = self.telemetry.get_logger() if self.telemetry else logging.getLogger(__name__)
        else:
            self.telemetry = None
            self.metrics = {}
            self.logger = logging.getLogger(__name__)
    
    def _load_environment(self):
        """Load and validate environment variables."""
        self.endpoint = os.getenv("OPENAI_ENDPOINT")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_version = os.getenv("OPENAI_API_VERSION")
        self.deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_database = os.getenv("COSMOS_DATABASE", "AIAssistant")
        self.cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
        
        # Validate required OpenAI environment variables
        if not all([self.endpoint, self.api_key, self.deployment_name]):
            error_msg = ("Missing required OpenAI environment variables. Please ensure OPENAI_ENDPOINT, "
                        "OPENAI_API_KEY, and OPENAI_MODEL_DEPLOYMENT_NAME are set in the .env file.")
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _initialize_cosmos(self):
        """Initialize CosmosDB for chat history persistence."""
        if self.cosmos_endpoint:
            try:
                with TelemetryContext(operation="cosmosdb_init", cosmos_endpoint=self.cosmos_endpoint):
                    self.cosmos_manager = CosmosDBChatHistoryManager(
                        self.cosmos_endpoint, 
                        self.cosmos_database, 
                        self.cosmos_container
                    )
                    self.logger.info("✅ CosmosDB initialized successfully")
            except Exception as e:
                self.logger.error(f"⚠ Warning: Failed to initialize CosmosDB: {e}")
                self.cosmos_manager = None
        else:
            self.logger.info("ℹ COSMOS_ENDPOINT not configured. Chat history will not be persisted.")
            self.cosmos_manager = None
    
    def _setup_openai_service(self):
        """Setup Azure OpenAI service for all agents."""
        self.service_id = "multi-agent-service"
        
        with TelemetryContext(operation="openai_service_init", endpoint=self.endpoint):
            self.kernel.add_service(AzureChatCompletion(
                deployment_name=self.deployment_name,
                endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version or "2023-05-15",
                service_id=self.service_id
            ))
            
            self.logger.info(f"✅ Azure OpenAI service configured with deployment: {self.deployment_name}")
        
        self.settings = self.kernel.get_prompt_execution_settings_from_service_id(service_id=self.service_id)
        self.settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    
    def _create_agents(self) -> Dict[str, ChatCompletionAgent]:
        """Create specialized agents for different tasks."""
        agents = {}
        
        # 1. Proxy Agent - Main conversation handler and task router
        proxy_instructions = f"""
You are the Proxy Agent for an AI Calendar Assistant. Your role is to:

1. **Welcome and Route**: Greet users and understand their needs
2. **Task Routing**: Determine which specialized agent should handle specific requests
3. **Conversation Management**: Maintain context and coordinate between agents
4. **Final Response**: Synthesize responses from specialized agents into coherent answers

**Routing Guidelines:**
- Calendar operations (scheduling, events, availability) → @CalendarAgent
- User searches, directory lookups, organizational data → @DirectoryAgent  
- Location searches, nearby places, maps → @LocationAgent
- General conversation, clarification, summary → Handle yourself

**Communication Style:**
- Professional but friendly tone
- Clear and concise responses
- Proactive in asking clarifying questions
- Acknowledge when routing to other agents

Session ID: {self.session_id}
Current Time: {datetime.datetime.now().isoformat()}
"""
        
        agents['proxy'] = ChatCompletionAgent(
            kernel=self.kernel,
            name="ProxyAgent",
            instructions=proxy_instructions,
            arguments=KernelArguments(settings=self.settings),
        )
        
        # 2. Calendar Agent - Handles calendar and scheduling operations
        calendar_kernel = Kernel()
        calendar_kernel.add_service(self.kernel.get_service(self.service_id))
        calendar_kernel.add_plugin(GraphPlugin(debug=False, session_id=self.session_id), plugin_name="graph")
        
        calendar_instructions = f"""
You are the Calendar Agent, specialized in calendar operations and scheduling. Your expertise includes:

**Core Capabilities:**
- Creating, updating, and managing calendar events
- Checking availability and scheduling conflicts
- Finding conference rooms and meeting spaces
- Managing attendees and meeting invitations
- Retrieving calendar information for users

**Available Functions:**
- get_calendar_events: Retrieve calendar events for users
- create_calendar_event: Schedule new meetings and events
- get_all_conference_rooms: Find available meeting rooms
- get_conference_room_events: Check room availability and bookings
- validate_user_mailbox: Troubleshoot calendar access issues

**Response Style:**
- Focus on calendar and scheduling solutions
- Provide clear meeting details and timing
- Suggest optimal meeting times and locations
- Handle timezone considerations carefully

Session ID: {self.session_id}
"""
        
        agents['calendar'] = ChatCompletionAgent(
            kernel=calendar_kernel,
            name="CalendarAgent", 
            instructions=calendar_instructions,
            arguments=KernelArguments(settings=self.settings),
        )
        
        # 3. Directory Agent - Handles user searches and organizational data
        directory_kernel = Kernel()
        directory_kernel.add_service(self.kernel.get_service(self.service_id))
        directory_kernel.add_plugin(GraphPlugin(debug=False, session_id=self.session_id), plugin_name="graph")
        
        directory_instructions = f"""
You are the Directory Agent, specialized in organizational data and user management. Your expertise includes:

**Core Capabilities:**
- Finding and searching for users in the organization
- Retrieving user profiles, preferences, and contact information
- Managing organizational hierarchy and reporting structures
- Discovering departments and team compositions
- Handling mailbox and user account information

**Available Functions:**
- user_search: Find users by various criteria
- get_user_by_id: Retrieve specific user information
- get_user_manager: Find reporting relationships
- get_direct_reports: Get team members and subordinates
- get_all_users: Organization-wide user queries
- get_users_by_department: Department-specific user searches
- get_all_departments: Discover organizational structure

**Response Style:**
- Provide comprehensive user and organizational information
- Respect privacy and appropriate information sharing
- Help with contact discovery and organizational navigation
- Suggest related searches when helpful

Session ID: {self.session_id}
"""
        
        agents['directory'] = ChatCompletionAgent(
            kernel=directory_kernel,
            name="DirectoryAgent",
            instructions=directory_instructions, 
            arguments=KernelArguments(settings=self.settings),
        )
        
        # 4. Location Agent - Handles location-based searches
        location_kernel = Kernel()
        location_kernel.add_service(self.kernel.get_service(self.service_id))
        location_kernel.add_plugin(AzureMapsPlugin(debug=False, session_id=self.session_id), plugin_name="azure_maps")
        
        location_instructions = f"""
You are the Location Agent, specialized in location-based searches and mapping. Your expertise includes:

**Core Capabilities:**
- Finding nearby points of interest (POIs)
- Searching for specific businesses and locations
- Category-based location searches (restaurants, gas stations, etc.)
- Brand-specific searches (Starbucks, McDonald's, etc.)
- Geographic area searches and mapping assistance

**Available Functions:**
- search_nearby_locations: General nearby POI searches
- search_by_category: Category-specific location searches
- search_by_brand: Brand-specific location searches  
- search_by_region: Large area geographic searches
- get_available_categories: Discover available search categories

**Response Style:**
- Provide specific location details with addresses
- Include distance and practical travel information
- Suggest multiple options when available
- Consider context like meeting locations or office proximity

Session ID: {self.session_id}
"""
        
        agents['location'] = ChatCompletionAgent(
            kernel=location_kernel,
            name="LocationAgent",
            instructions=location_instructions,
            arguments=KernelArguments(settings=self.settings),
        )
        
        self.logger.info(f"✅ Created {len(agents)} specialized agents")
        return agents
    
    def _create_group_chat(self) -> AgentGroupChat:
        """Create agent group chat for multi-agent conversations."""
        # Define agent list for the group chat
        agent_list = [
            self.agents['proxy'],
            self.agents['calendar'], 
            self.agents['directory'],
            self.agents['location']
        ]
        
        # Create the group chat
        group_chat = AgentGroupChat(
            agents=agent_list,
            selection_strategy=self._agent_selection_strategy
        )
        
        self.logger.info("✅ Agent group chat created")
        return group_chat
    
    async def _agent_selection_strategy(self, agents: List[ChatCompletionAgent], history: List[ChatMessageContent]) -> ChatCompletionAgent:
        """
        Custom agent selection strategy based on conversation context.
        
        Args:
            agents: List of available agents
            history: Conversation history
            
        Returns:
            ChatCompletionAgent: Selected agent for the next response
        """
        if not history:
            # Start with proxy agent for new conversations
            return self.agents['proxy']
        
        last_message = history[-1].content.lower() if history else ""
        
        # Route based on keywords and context
        if any(keyword in last_message for keyword in [
            'calendar', 'meeting', 'schedule', 'appointment', 'event', 
            'conference room', 'availability', 'book', 'conference'
        ]):
            return self.agents['calendar']
        
        elif any(keyword in last_message for keyword in [
            'user', 'find person', 'directory', 'employee', 'manager', 
            'department', 'team', 'who is', 'contact', 'reports'
        ]):
            return self.agents['directory']
        
        elif any(keyword in last_message for keyword in [
            'location', 'nearby', 'restaurant', 'coffee', 'gas station',
            'map', 'address', 'directions', 'close to', 'near'
        ]):
            return self.agents['location']
        
        else:
            # Default to proxy agent for general conversation
            return self.agents['proxy']
    
    @trace_async_method(operation_name="multi_agent.process_message", include_args=True)
    @measure_performance("multi_agent_request")
    async def process_message(self, message: str) -> str:
        """
        Process a user message through the multi-agent system.
        
        Args:
            message: User's input message
            
        Returns:
            str: Response from the appropriate agent(s)
        """
        # Record multi-agent request metric
        try:
            if 'chat_requests_total' in self.metrics:
                self.metrics['chat_requests_total'].add(1, {
                    "session_id": self.session_id,
                    "agent_type": "multi_agent"
                })
        except Exception as e:
            self.logger.warning(f"Failed to record multi-agent request metric: {e}")
        
        self.logger.info(f"Processing multi-agent request for session: {self.session_id}")
        
        # Console telemetry for request
        try:
            console_telemetry_event("multi_agent_request", {
                "session_id": self.session_id,
                "message_length": len(message),
                "has_cosmosdb": self.cosmos_manager is not None
            }, "multi_agent")
        except Exception as e:
            self.logger.warning(f"Failed to record console telemetry: {e}")
        
        # Create or hydrate thread
        with TelemetryContext(operation="thread_creation", session_id=self.session_id):
            if self.cosmos_manager:
                thread = await self.cosmos_manager.create_hydrated_thread(self.kernel, self.session_id)
                self.logger.debug("Thread hydrated from CosmosDB")
            else:
                # In newer semantic-kernel versions, we'll use AgentGroupChat directly
                thread = []  # Simple list to store chat history
                self.logger.debug("Created new empty thread")
        
        # Process with agent group chat
        with TelemetryContext(operation="multi_agent_response", message_length=len(message)):
            try:
                # Create user message
                user_message = ChatMessageContent(
                    role=AuthorRole.USER,
                    content=message
                )
                
                # Add to thread if it's a list
                if isinstance(thread, list):
                    thread.append(user_message)
                    # Get response from the agent group using the messages
                    response = await self.group_chat.invoke([user_message])
                else:
                    # For CosmosDB hydrated threads, use the existing method
                    await thread.add_chat_message(user_message)
                    response = await self.group_chat.invoke(thread)
                
                # Extract the response content
                response_content = response.content if hasattr(response, 'content') else str(response)
                
                self.logger.info(f"Generated multi-agent response for session: {self.session_id}")
                
            except Exception as e:
                self.logger.error(f"Error in multi-agent processing: {e}")
                response_content = "I apologize, but I encountered an error processing your request. Please try again."
        
        # Save chat history if CosmosDB is available
        if self.cosmos_manager:
            try:
                with TelemetryContext(operation="save_chat_history", session_id=self.session_id):
                    await self.cosmos_manager.save_chat_history(thread, self.session_id)
                    self.logger.info(f"Multi-agent chat history saved with session ID: {self.session_id}")
            except Exception as e:
                self.logger.error(f"Error saving multi-agent chat history: {e}")
        
        return response_content
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status information about all agents.
        
        Returns:
            dict: Status information for each agent
        """
        status = {
            "session_id": self.session_id,
            "total_agents": len(self.agents),
            "agents": {},
            "cosmos_available": self.cosmos_manager is not None,
            "telemetry_enabled": self.telemetry is not None
        }
        
        for name, agent in self.agents.items():
            status["agents"][name] = {
                "name": agent.name,
                "available": True,
                "instructions_length": len(agent.instructions) if hasattr(agent, 'instructions') else 0
            }
        
        return status
    
    async def reset_conversation(self):
        """Reset the conversation history for a fresh start."""
        if self.cosmos_manager:
            try:
                # Clear conversation history in CosmosDB
                await self.cosmos_manager.clear_conversation_history(self.session_id)
                self.logger.info(f"Conversation history cleared for session: {self.session_id}")
            except Exception as e:
                self.logger.error(f"Error clearing conversation history: {e}")

# Example usage and testing
async def main():
    """Example usage of Multi-Agent Orchestrator."""
    console_info("🚀 Starting Multi-Agent AI Calendar Assistant", "MultiAgent")
    
    try:
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(session_id="test-multi-agent-session")
        
        # Example conversations
        test_messages = [
            "Hello! I need help with scheduling a meeting.",
            "Can you find John Smith in our directory?", 
            "Where are some good coffee shops near our office?",
            "What's my calendar looking like for tomorrow?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            console_info(f"\n=== Example {i}: {message} ===", "MultiAgent")
            
            response = await orchestrator.process_message(message)
            console_info(f"Response: {response[:200]}{'...' if len(response) > 200 else ''}", "MultiAgent")
        
        # Get agent status
        status = await orchestrator.get_agent_status()
        console_info(f"\nAgent Status: {json.dumps(status, indent=2)}", "MultiAgent")
        
    except Exception as e:
        console_info(f"Multi-agent test failed: {e}", "MultiAgent")
        raise

if __name__ == "__main__":
    asyncio.run(main())
