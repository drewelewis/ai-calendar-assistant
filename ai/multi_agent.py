# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import datetime
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory

from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager
from agents import (
    create_calendar_agent,
    create_directory_agent,
    create_email_agent,
    create_location_agent,
    create_risk_agent,
    create_proxy_agent,
)
from prompts.graph_prompts import prompts
from utils.teams_utilities import TeamsUtilities
from utils.thread_utilities import ThreadUtilities

# Import telemetry components
from telemetry.config import initialize_telemetry, get_telemetry
from telemetry.decorators import trace_async_method, measure_performance, TelemetryContext
from telemetry.token_tracking import add_token_span_attributes, record_token_metrics
from telemetry.console_output import console_info, console_debug, console_telemetry_event

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Module-level CosmosDB singleton — created once, reused across all requests
# ---------------------------------------------------------------------------
_shared_cosmos_manager: Optional[CosmosDBChatHistoryManager] = None

# ---------------------------------------------------------------------------
# Routing prompt â€” kept short and deterministic (very low token budget reply)
# ---------------------------------------------------------------------------
_ROUTER_SYSTEM = """\
You are a request router. Given a user message, reply with EXACTLY ONE word â€” \
the name of the agent best suited to handle it.

Agents and their domains:
- calendar   : scheduling meetings, recurring meetings, standups, reminders, calendar events, availability, conference rooms, Teams/Zoom meetings
- directory  : finding people, user profiles, org chart, departments, managers, direct reports
- email      : reading email, checking inbox, searching mail, sending email, email summaries
- location   : nearby places, restaurants, coffee shops, hotels, POI searches, maps, addresses
- risk       : client risk profiles, financial exposure, credit risk, portfolio analysis, compliance
- proxy      : greetings, general questions, clarification, anything else

Reply with only the single word agent name â€” no punctuation, no explanation.\
"""


class MultiAgentOrchestrator:
    """
    Multi-Agent AI Calendar Assistant Orchestrator.

    Uses LLM-based routing: a lightweight router call classifies each incoming
    message and dispatches it to the appropriate specialist agent.

    Agents:
    - ProxyAgent    : General conversation and Q&A (no plugins)
    - CalendarAgent : Calendar/scheduling via Microsoft Graph
    - DirectoryAgent: People/org search via Microsoft Graph
    - LocationAgent : POI / nearby search via Azure Maps
    - RiskAgent     : Client risk analysis via Risk plugin
    """

    def __init__(self, session_id: str = None):
        if not session_id:
            raise ValueError("session_id is required for MultiAgentOrchestrator")

        self.session_id = session_id

        self._initialize_telemetry()
        self._load_environment()
        self._initialize_cosmos()

        self.teams_utils = TeamsUtilities()
        self.thread_utils = ThreadUtilities()

        # Shared kernel holds the Azure OpenAI service used by all agents
        self.kernel = Kernel()
        self._setup_openai_service()

        # Build all specialist agents (each gets its own kernel + plugins)
        self.agents: Dict[str, ChatCompletionAgent] = self._build_agents()

        self.logger.info(f"âœ… MultiAgentOrchestrator ready â€” session: {self.session_id}")

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _initialize_telemetry(self):
        service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant-multi-agent")
        service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")

        ok = initialize_telemetry(service_name=service_name, service_version=service_version)
        if ok:
            self.telemetry = get_telemetry()
            self.metrics = self.telemetry.create_custom_metrics() if self.telemetry else {}
            self.logger = self.telemetry.get_logger() if self.telemetry else logging.getLogger(__name__)
        else:
            self.telemetry = None
            self.metrics = {}
            self.logger = logging.getLogger(__name__)

    def _load_environment(self):
        self.endpoint = os.getenv("OPENAI_ENDPOINT")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_version = os.getenv("OPENAI_API_VERSION")
        self.deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_database = os.getenv("COSMOS_DATABASE", "CalendarAssistant")
        self.cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")

        if not all([self.endpoint, self.api_key, self.deployment_name]):
            raise ValueError(
                "Missing required env vars: OPENAI_ENDPOINT, OPENAI_API_KEY, "
                "OPENAI_MODEL_DEPLOYMENT_NAME"
            )

    def _initialize_cosmos(self):
        global _shared_cosmos_manager
        if self.cosmos_endpoint:
            if _shared_cosmos_manager is not None:
                # Reuse the existing singleton — avoids a new CosmosClient +
                # list_databases() round-trip on every request (~200-400 ms)
                self.cosmos_manager = _shared_cosmos_manager
                self.logger.debug("CosmosDB singleton reused")
            else:
                try:
                    with TelemetryContext(operation="cosmosdb_init"):
                        _shared_cosmos_manager = CosmosDBChatHistoryManager(
                            self.cosmos_endpoint,
                            self.cosmos_database,
                            self.cosmos_container,
                        )
                        self.cosmos_manager = _shared_cosmos_manager
                        self.logger.info("✅ CosmosDB initialised (singleton created)")
                except Exception as e:
                    self.logger.error(f"CosmosDB init failed: {e}")
                    self.cosmos_manager = None
        else:
            self.logger.info("COSMOS_ENDPOINT not set — chat history disabled")
            self.cosmos_manager = None

    def _setup_openai_service(self):
        self.service_id = "multi-agent-service"

        self.kernel.add_service(AzureChatCompletion(
            deployment_name=self.deployment_name,
            endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version or "2025-01-01-preview",
            service_id=self.service_id,
        ))

        self.settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        self.settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        is_o1 = "o1" in (self.deployment_name or "").lower()
        max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "8000"))

        try:
            for attr in ("max_completion_tokens", "max_tokens"):
                if hasattr(self.settings, attr):
                    setattr(self.settings, attr, max_tokens)
                    break
            if not is_o1:
                if hasattr(self.settings, "temperature"):
                    self.settings.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
                if hasattr(self.settings, "top_p"):
                    self.settings.top_p = float(os.getenv("OPENAI_TOP_P", "0.9"))
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Could not set OpenAI params: {e}")

        self.logger.info(f"âœ… Azure OpenAI configured â€” deployment: {self.deployment_name}")

    def _build_agents(self) -> Dict[str, ChatCompletionAgent]:
        """Instantiate all specialist agents from /agents/."""
        shared_service = self.kernel.get_service(self.service_id)

        agents: Dict[str, ChatCompletionAgent] = {
            "proxy":     create_proxy_agent(shared_service, self.service_id, self.session_id, self.settings),
            "calendar":  create_calendar_agent(shared_service, self.service_id, self.session_id, self.settings),
            "directory": create_directory_agent(shared_service, self.service_id, self.session_id, self.settings),
            "email":     create_email_agent(shared_service, self.service_id, self.session_id, self.settings),
            "location":  create_location_agent(shared_service, self.service_id, self.session_id, self.settings),
            "risk":      create_risk_agent(shared_service, self.service_id, self.session_id, self.settings),
        }

        # Keep a reference to the maps plugin so we can close its aiohttp session on shutdown
        try:
            self._maps_plugin = agents["location"].kernel.plugins["azure_maps"]
        except Exception:
            self._maps_plugin = None

        self.logger.info(f"✅ {len(agents)} agents ready: {list(agents.keys())}")
        return agents

    # ------------------------------------------------------------------
    # LLM-based router
    # ------------------------------------------------------------------

    async def _route_message(self, message: str) -> ChatCompletionAgent:
        """
        Ask the LLM which agent should handle `message`.
        Returns the selected ChatCompletionAgent (defaults to proxy on any failure).
        """
        try:
            service: AzureChatCompletion = self.kernel.get_service(self.service_id)

            # Minimal settings: no tools, tiny token budget, temperature=0
            router_settings = self.kernel.get_prompt_execution_settings_from_service_id(
                self.service_id
            )
            router_settings.function_choice_behavior = None
            for attr in ("max_completion_tokens", "max_tokens"):
                if hasattr(router_settings, attr):
                    setattr(router_settings, attr, 10)
                    break
            is_o1 = "o1" in (self.deployment_name or "").lower()
            if not is_o1 and hasattr(router_settings, "temperature"):
                router_settings.temperature = 0.0

            routing_history = ChatHistory()
            routing_history.add_system_message(_ROUTER_SYSTEM)
            routing_history.add_user_message(message)

            result = await service.get_chat_message_contents(
                chat_history=routing_history,
                settings=router_settings,
                kernel=self.kernel,
            )

            agent_name = result[0].content.strip().lower().split()[0]
            selected = self.agents.get(agent_name)

            if selected:
                self.logger.info(f"LLM router â†’ {agent_name}")
                console_debug(f"LLM router selected: {agent_name}", module="Router")
                return selected

            self.logger.warning(f"Router returned unknown agent '{agent_name}', using proxy")
            return self.agents["proxy"]

        except Exception as e:
            self.logger.warning(f"LLM routing failed ({e}), defaulting to proxy")
            return self.agents["proxy"]

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    @trace_async_method(operation_name="multi_agent.process_message", include_args=True)
    @measure_performance("multi_agent_request")
    async def process_message(self, message: str) -> str:
        """Route a user message to the appropriate specialist agent and return its response."""
        self.logger.info(f"process_message â€” session: {self.session_id}")

        try:
            if "chat_requests_total" in self.metrics:
                self.metrics["chat_requests_total"].add(
                    1, {"session_id": self.session_id, "agent_type": "multi_agent"}
                )
        except Exception:
            pass

        try:
            console_telemetry_event(
                "multi_agent_request",
                {"session_id": self.session_id, "message_length": len(message)},
                "multi_agent",
            )
        except Exception:
            pass

        # --- Hydrate / create thread ---
        with TelemetryContext(operation="thread_creation", session_id=self.session_id):
            if self.cosmos_manager:
                thread = await self.cosmos_manager.create_hydrated_thread(
                    self.kernel, self.session_id
                )
                self.logger.debug("Thread hydrated from CosmosDB")
            else:
                thread = ChatHistoryAgentThread()
                self.logger.debug("New empty thread created")

        try:
            thread = await self.thread_utils.ensure_system_and_instruction_messages(
                thread, self.session_id, prompts, self.logger
            )
        except Exception as e:
            self.logger.warning(f"ensure_system_and_instruction_messages: {e}")

        # --- LLM routing ---
        with TelemetryContext(operation="llm_routing", message_length=len(message)):
            selected_agent = await self._route_message(message)

        # --- Dispatch to selected agent ---
        response_content = ""
        with TelemetryContext(
            operation="agent_response",
            agent_name=selected_agent.name,
            message_length=len(message),
        ):
            try:
                response = await selected_agent.get_response(
                    messages=message,
                    thread=thread,
                )

                # Unwrap the response
                if hasattr(response, "value"):
                    response_content = response.value
                elif hasattr(response, "content"):
                    response_content = response.content
                else:
                    response_content = str(response)

                if hasattr(response_content, "content"):
                    response_content = response_content.content
                elif not isinstance(response_content, str):
                    response_content = str(response_content)

                if hasattr(response, "thread"):
                    thread = response.thread

                self.logger.info(
                    f"{selected_agent.name} responded ({len(response_content)} chars)"
                )

            except Exception as e:
                self.logger.error(f"Agent {selected_agent.name} error: {e}", exc_info=True)
                response_content = (
                    "I'm having trouble processing your request right now. "
                    "Please try again or rephrase your question."
                )

        if not response_content:
            response_content = "I wasn't able to generate a response. Please try again."

        # --- Persist chat history ---
        if self.cosmos_manager:
            try:
                with TelemetryContext(operation="save_chat_history", session_id=self.session_id):
                    await self.cosmos_manager.save_chat_history(thread, self.session_id)
            except Exception as e:
                self.logger.error(f"Failed to save chat history: {e}")

        return response_content

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    async def get_agent_status(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_agents": len(self.agents),
            "agents": {
                name: {
                    "name": agent.name,
                    "available": True,
                    "instructions_length": (
                        len(agent.instructions) if hasattr(agent, "instructions") else 0
                    ),
                }
                for name, agent in self.agents.items()
            },
            "cosmos_available": self.cosmos_manager is not None,
            "telemetry_enabled": self.telemetry is not None,
        }

    async def close(self):
        """Release aiohttp sessions and other async resources."""
        if self._maps_plugin:
            try:
                await self._maps_plugin._cleanup()
            except Exception:
                pass

    async def reset_conversation(self):
        if self.cosmos_manager:
            try:
                await self.cosmos_manager.clear_conversation_history(self.session_id)
                self.logger.info(f"Conversation reset for session: {self.session_id}")
            except Exception as e:
                self.logger.error(f"reset_conversation error: {e}")


# ---------------------------------------------------------------------------
# Local smoke-test
# ---------------------------------------------------------------------------
async def main():
    session_id = os.getenv("CHAT_SESSION_ID", "test-session-001")
    console_info("ðŸš€ Starting Multi-Agent Orchestrator smoke test", "MultiAgent")

    orchestrator = MultiAgentOrchestrator(session_id=session_id)

    test_messages = [
        "Hello! What can you help me with?",
        "Find coffee shops near Times Square",
        "Who is the manager of the engineering department?",
        "What's my calendar looking like for tomorrow?",
        "Show me the risk profile for Meridian Capital",
    ]

    for i, msg in enumerate(test_messages, 1):
        console_info(f"\n=== Test {i}: {msg} ===", "MultiAgent")
        response = await orchestrator.process_message(msg)
        preview = response[:300] + ("..." if len(response) > 300 else "")
        console_info(f"Response: {preview}", "MultiAgent")

    status = await orchestrator.get_agent_status()
    console_info(f"\nAgent Status:\n{json.dumps(status, indent=2)}", "MultiAgent")


if __name__ == "__main__":
    asyncio.run(main())
