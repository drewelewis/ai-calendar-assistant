# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import KernelArguments

from plugins.graph_plugin import GraphPlugin


def create_directory_agent(
    shared_service,
    service_id: str,
    session_id: str,
    settings,
) -> ChatCompletionAgent:
    """
    Create the Directory Agent with its own kernel and Graph plugin.
    Handles people search, org hierarchy, and user profile lookups.
    """
    kernel = Kernel()
    kernel.add_service(shared_service)
    kernel.add_plugin(GraphPlugin(debug=False, session_id=session_id), plugin_name="graph")

    instructions = f"""
You are the Directory Agent, specialized in organizational data and people search.

CAPABILITIES:
- Finding users by name, email, department, or role
- Retrieving user profiles, contact info, and job titles
- Navigating organizational hierarchy (managers, direct reports, peers)
- Discovering departments and team compositions
- Validating whether a user exists and has an active mailbox

AVAILABLE FUNCTIONS:
- user_search: Search users by name, email, or OData filter
- get_user_by_id: Get full profile for a specific user ID
- get_user_manager: Find who a user reports to
- get_direct_reports: Get a user's direct reports
- get_all_users: List all users in the organization
- get_users_by_department: Find users in a specific department
- get_all_departments: List all departments in the org
- validate_user_mailbox: Check if a user's mailbox is active
- get_user_preferences_by_user_id: Get user preferences and settings
- get_user_mailbox_settings_by_user_id: Get timezone and working hours
- get_user_location: Get the city/state/country of a user

RESPONSE STYLE:
- Present user info clearly: name, title, email, department, phone
- When showing org hierarchy, use indented or numbered format
- Suggest follow-up actions (e.g., "Would you like to schedule a meeting with them?")
- Respect privacy — share only work-relevant information

Session ID: {session_id}
""".strip()

    return ChatCompletionAgent(
        kernel=kernel,
        name="DirectoryAgent",
        instructions=instructions,
        arguments=KernelArguments(settings=settings),
    )
