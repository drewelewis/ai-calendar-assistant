# LLM Router Migration Example

## Current Implementation (Semantic Kernel)

Your current router uses an LLM to decide which agent handles each message:

```python
# From ai/multi_agent.py

_ROUTER_SYSTEM = """\
You are a request router. Given a user message (and optional recent conversation context), \
reply with EXACTLY ONE word - the name of the agent best suited to handle it.

Agents and their domains:
- calendar   : scheduling meetings, recurring meetings, standups, reminders, calendar events
- directory  : finding people, user profiles, org chart, departments, managers, direct reports
- email      : reading email, checking inbox, searching mail, sending email, email summaries
- location   : nearby places, restaurants, coffee shops, hotels, POI searches, maps, addresses
- risk       : client risk profiles, financial exposure, credit risk, portfolio analysis, compliance
- proxy      : greetings, general questions, clarification, anything else

IMPORTANT: When the new message is ambiguous (e.g. "yes", "sure", "near my office"), \
use the recent conversation context to determine which agent was last active.

Reply with only the single word agent name - no punctuation, no explanation.\
"""

async def _route_message(self, message: str, recent_context: str = "") -> ChatCompletionAgent:
    service: AzureChatCompletion = self.kernel.get_service(self.service_id)
    
    # Optimized settings: no tools, 10 tokens, temperature=0
    router_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
    router_settings.function_choice_behavior = None
    router_settings.max_tokens = 10
    router_settings.temperature = 0.0
    
    routing_history = ChatHistory()
    routing_history.add_system_message(_ROUTER_SYSTEM)
    
    # Include recent context for follow-ups
    if recent_context:
        user_prompt = f"Recent conversation:\n{recent_context}\n\nNew message: {message}"
    else:
        user_prompt = message
    routing_history.add_user_message(user_prompt)
    
    # Get LLM decision
    result = await service.get_chat_message_contents(routing_history, settings=router_settings, kernel=self.kernel)
    agent_name = result[0].content.strip().lower().split()[0]
    
    # Return selected agent or default to proxy
    selected = self.agents.get(agent_name, self.agents["proxy"])
    return selected
```

## Migrated Implementation (Agent Framework)

### Option 1: Router as Executor with Embedded ChatAgent

```python
from agent_framework import Executor, ChatAgent, ChatMessage, Role, WorkflowContext, handler
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

# Keep the EXACT same router prompt
_ROUTER_SYSTEM = """\
You are a request router. Given a user message (and optional recent conversation context), \
reply with EXACTLY ONE word - the name of the agent best suited to handle it.

Agents and their domains:
- calendar   : scheduling meetings, recurring meetings, standups, reminders, calendar events
- directory  : finding people, user profiles, org chart, departments, managers, direct reports
- email      : reading email, checking inbox, searching mail, sending email, email summaries
- location   : nearby places, restaurants, coffee shops, hotels, POI searches, maps, addresses
- risk       : client risk profiles, financial exposure, credit risk, portfolio analysis, compliance
- proxy      : greetings, general questions, clarification, anything else

IMPORTANT: When the new message is ambiguous (e.g. "yes", "sure", "near my office"), \
use the recent conversation context to determine which agent was last active.

Reply with only the single word agent name - no punctuation, no explanation.\
"""

class LLMRouterExecutor(Executor):
    """Router uses LLM to determine which specialist agent should handle each message"""
    
    router_agent: ChatAgent
    session_id: str
    
    def __init__(self, client: AzureOpenAIChatClient, session_id: str, id="router"):
        self.session_id = session_id
        
        # Create router agent with optimized settings
        self.router_agent = client.create_agent(
            name="RouterAgent",
            instructions=_ROUTER_SYSTEM,
            # Optimize: minimal tokens, deterministic
            model_kwargs={
                "max_tokens": 10,
                "temperature": 0.0
            }
        )
        super().__init__(id=id)
    
    @handler
    async def route_message(
        self,
        request: dict,  # {"message": str, "recent_context": str}
        ctx: WorkflowContext[ChatMessage]
    ) -> None:
        """Use LLM to decide which agent should handle this message"""
        
        message = request["message"]
        recent_context = request.get("recent_context", "")
        
        # Build routing prompt (same pattern as before)
        if recent_context:
            routing_prompt = f"Recent conversation:\n{recent_context}\n\nNew message: {message}"
        else:
            routing_prompt = message
        
        # Get LLM decision
        try:
            response = await self.router_agent.run([
                ChatMessage(role=Role.USER, text=routing_prompt)
            ])
            
            # Parse agent name (same as before)
            agent_name = response.text.strip().lower().split()[0]
            
            # Validate and default to proxy
            valid_agents = ["calendar", "directory", "email", "location", "risk", "proxy"]
            target_agent = agent_name if agent_name in valid_agents else "proxy"
            
            print(f"🔀 LLM Router → {target_agent}")
            
            # Route to selected agent
            await ctx.send_message(
                ChatMessage(role=Role.USER, text=message),
                target_id=target_agent
            )
            
        except Exception as e:
            print(f"⚠️ Router error: {e}, defaulting to proxy")
            await ctx.send_message(
                ChatMessage(role=Role.USER, text=message),
                target_id="proxy"
            )
```

### Building the Workflow

```python
from agent_framework import WorkflowBuilder

# Azure OpenAI Client (using your existing config)
client = AzureOpenAIChatClient(
    endpoint=os.getenv("OPENAI_ENDPOINT"),
    deployment_name=os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME"),
    credential=DefaultAzureCredential(),  # Or use API key
)

# Build workflow with LLM router
workflow = (
    WorkflowBuilder()
    # Router is first - uses LLM to decide
    .register_executor(
        lambda: LLMRouterExecutor(client, session_id),
        name="router"
    )
    
    # All specialist agents (each gets their own tools)
    .register_executor(
        lambda: CalendarAgentExecutor(client, session_id),
        name="calendar"
    )
    .register_executor(
        lambda: DirectoryAgentExecutor(client, session_id),
        name="directory"
    )
    .register_executor(
        lambda: EmailAgentExecutor(client, session_id),
        name="email"
    )
    .register_executor(
        lambda: LocationAgentExecutor(client, session_id),
        name="location"
    )
    .register_executor(
        lambda: RiskAgentExecutor(client, session_id),
        name="risk"
    )
    .register_executor(
        lambda: ProxyAgentExecutor(client, session_id),
        name="proxy"
    )
    
    # Router can route to any agent
    .add_edge("router", "calendar")
    .add_edge("router", "directory")
    .add_edge("router", "email")
    .add_edge("router", "location")
    .add_edge("router", "risk")
    .add_edge("router", "proxy")
    
    # Workflow starts at router
    .set_start_executor("router")
    .build()
)
```

### Running the Workflow

```python
# Get recent conversation context from CosmosDB (for follow-ups)
recent_messages = await cosmos_manager.get_chat_history(session_id, last_n=5)
recent_context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])

# Run workflow with streaming
async for event in workflow.run_stream({
    "message": user_message,
    "recent_context": recent_context
}):
    if isinstance(event, WorkflowOutputEvent):
        # Agent completed, yield output
        yield event.data
    elif isinstance(event, AgentRunEvent):
        # Agent is streaming response
        yield event.data
    elif isinstance(event, ExecutorFailedEvent):
        # Handle errors
        print(f"❌ Error: {event.details.message}")
```

## Key Differences

| Aspect | Semantic Kernel | Agent Framework |
|--------|----------------|-----------------|
| Router Type | Manual LLM call | ChatAgent in Executor |
| Prompt Location | String constant | ChatAgent instructions |
| LLM Call | `get_chat_message_contents()` | `agent.run()` |
| Routing Logic | Manual dictionary lookup | `ctx.send_message(target_id=...)` |
| Settings | `PromptExecutionSettings` | `model_kwargs` in create_agent |
| Agent Selection | Return agent object | Send message to target_id |

## Benefits of Agent Framework Approach

1. **Unified Pattern**: Router is just another agent (consistent)
2. **Declarative Routing**: Edges define valid paths
3. **Native Streaming**: `run_stream()` built-in
4. **Type Safety**: WorkflowContext provides type hints
5. **Event-Driven**: Granular events for observability
6. **State Management**: Workflow handles message passing

## Migration Checklist

- [ ] Copy `_ROUTER_SYSTEM` prompt exactly as-is
- [ ] Create `LLMRouterExecutor` class
- [ ] Test router agent independently (should return agent names)
- [ ] Build workflow with router and all agents
- [ ] Pass recent context from CosmosDB for follow-ups
- [ ] Verify routing decisions match current behavior
- [ ] Test ambiguous messages ("yes", "ok") with context
- [ ] Validate default to proxy on errors

## Testing the Router

```python
# Test router independently before full workflow
async def test_router():
    client = AzureOpenAIChatClient(...)
    router = LLMRouterExecutor(client, "test-session")
    
    test_cases = [
        "Schedule a meeting tomorrow",      # Should route to: calendar
        "Who is the CEO?",                   # Should route to: directory
        "Check my inbox",                    # Should route to: email
        "Find coffee shops nearby",          # Should route to: location
        "What's the risk profile for ABC?",  # Should route to: risk
        "Hello!",                            # Should route to: proxy
        "yes",                               # With context: previous agent
    ]
    
    for message in test_cases:
        request = {"message": message, "recent_context": ""}
        # Test routing logic
        print(f"Message: {message}")
        # ... test router response
```
