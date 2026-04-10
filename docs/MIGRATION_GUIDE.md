# Migration Guide: Semantic Kernel → Microsoft Agent Framework

## 📊 Migration Overview

This document outlines the migration from **Semantic Kernel 1.34.0** to **Microsoft Agent Framework 0.1.0+** for the AI Calendar Assistant.

### Current Architecture (Semantic Kernel)
```
MultiAgentOrchestrator
├── LLM Router (determines which agent)
├── ProxyAgent (general conversation)
├── CalendarAgent (Microsoft Graph - calendar)
├── DirectoryAgent (Microsoft Graph - people)
├── EmailAgent (Microsoft Graph - email)
├── LocationAgent (Azure Maps)
└── RiskAgent (Risk data)

Each agent has:
- ChatCompletionAgent instance
- Kernel with plugins (@kernel_function)
- ChatHistoryAgentThread for state
```

### Target Architecture (Agent Framework)
```
Workflow
├── RouterExecutor (determines path)
├── ProxyAgentExecutor (ChatAgent)
├── CalendarAgentExecutor (ChatAgent + Graph tools)
├── DirectoryAgentExecutor (ChatAgent + Graph tools)
├── EmailAgentExecutor (ChatAgent + Graph tools)
├── LocationAgentExecutor (ChatAgent + Maps tools)
└── RiskAgentExecutor (ChatAgent + Risk tools)

Each executor:
- Is an Executor subclass with @handler methods
- Contains a ChatAgent instance
- Defines tools as agent parameters
- Uses WorkflowContext for message passing
```

## 🔄 Key Migration Changes

### 1. Package Changes
| Before (Semantic Kernel) | After (Agent Framework) |
|--------------------------|-------------------------|
| `semantic-kernel==1.34.0` | `agent-framework>=0.1.0` |
| `from semantic_kernel import Kernel` | `from agent_framework import WorkflowBuilder` |
| `from semantic_kernel.agents import ChatCompletionAgent` | `from agent_framework import ChatAgent, Executor` |
| `from semantic_kernel.functions import kernel_function` | Tools defined as functions or agent parameters |
| `ChatHistoryAgentThread` | `WorkflowContext` |
| LLM router with manual dispatch | LLM router as ChatAgent in workflow |
| `_ROUTER_SYSTEM` prompt with manual parsing | Same prompt in RouterExecutor ChatAgent |

### 2. Plugin/Tool Migration

#### Before (Semantic Kernel `@kernel_function`)
```python
from semantic_kernel.functions import kernel_function
from typing import Annotated

class GraphPlugin:
    @kernel_function(description="Search for users")
    async def user_search(
        self,
        filter: Annotated[str, "OData filter"],
    ) -> Annotated[List[dict], "User results"]:
        # Implementation
        pass
```

#### After (Agent Framework - Tool Functions)
```python
from agent_framework import ToolFunction

async def user_search(filter: str) -> list[dict]:
    """Search for users in Microsoft 365.
    
    Args:
        filter: OData filter criteria
        
    Returns:
        List of user dictionaries
    """
    # Implementation
    pass

# Tools are passed to agent creation
tool_user_search = ToolFunction(
    name="user_search",
    description="Search for users in Microsoft 365 Directory using OData filters",
    function=user_search,
)
```

### 3. Agent Migration

#### Before (Semantic Kernel ChatCompletionAgent)
```python
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent

kernel = Kernel()
kernel.add_service(azure_chat_completion_service)
kernel.add_plugin(GraphPlugin(session_id=session_id), plugin_name="graph")

agent = ChatCompletionAgent(
    service_id="azure_openai",
    kernel=kernel,
    name="CalendarAgent",
    instructions="You are the Calendar Agent...",
)
```

#### After (Agent Framework with Executor)
```python
from agent_framework import Executor, ChatAgent, WorkflowContext, handler
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

class CalendarAgentExecutor(Executor):
    agent: ChatAgent
    
    def __init__(self, client: AzureOpenAIChatClient, session_id: str, id="calendar"):
        self.session_id = session_id
        self.agent = client.create_agent(
            name="CalendarAgent",
            instructions="You are the Calendar Agent...",
            tools=[tool_user_search, tool_create_event, ...]
        )
        super().__init__(id=id)
    
    @handler
    async def handle_message(
        self, 
        message: ChatMessage, 
        ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        # Run agent
        response = await self.agent.run([message])
        await ctx.send_message(response.messages)
```

### 4. Multi-Agent Orchestration Migration (LLM-Based Routing)

#### Before (Semantic Kernel - LLM Router)
```python
class MultiAgentOrchestrator:
    def __init__(self):
        self.agents = self._build_agents()  # Dict of agents
        self.threads = {}  # Session threads
    
    async def _route_message(self, message: str, recent_context: str = "") -> ChatCompletionAgent:
        """Ask the LLM which agent should handle the message"""
        # Create lightweight router prompt
        routing_history = ChatHistory()
        routing_history.add_system_message(_ROUTER_SYSTEM)  # LLM returns agent name
        
        # Include recent context for follow-ups
        user_prompt = f"Recent conversation:\n{recent_context}\n\nNew message: {message}" if recent_context else message
        routing_history.add_user_message(user_prompt)
        
        # Get LLM response (agent name)
        result = await service.get_chat_message_contents(routing_history, settings)
        agent_name = result[0].content.strip().lower().split()[0]
        
        return self.agents.get(agent_name, self.agents["proxy"])
    
    async def process_message(self, session_id, user_message):
        # 1. LLM determines which agent
        agent = await self._route_message(user_message, recent_context)
        
        # 2. Invoke selected agent
        async for message in agent.invoke_stream(thread):
            yield message
```

#### After (Agent Framework - LLM Router ChatAgent)
```python
from agent_framework import WorkflowBuilder, Executor, ChatAgent, ChatMessage, WorkflowContext, handler
from agent_framework.azure import AzureOpenAIChatClient

class LLMRouterExecutor(Executor):
    """Uses LLM to determine which agent should handle the message"""
    
    router_agent: ChatAgent
    
    def __init__(self, client: AzureOpenAIChatClient, id="router"):
        # Router agent returns just the agent name
        self.router_agent = client.create_agent(
            name="RouterAgent",
            instructions=_ROUTER_SYSTEM,  # Same prompt as before
            # Optimize for routing: low tokens, temperature=0
            model_config={"max_tokens": 10, "temperature": 0.0}
        )
        super().__init__(id=id)
    
    @handler
    async def route_message(
        self, 
        request: dict,  # Contains: message, recent_context
        ctx: WorkflowContext[ChatMessage]
    ) -> None:
        """Ask LLM which agent should handle this message"""
        message = request["message"]
        recent_context = request.get("recent_context", "")
        
        # Build routing prompt with context
        if recent_context:
            routing_prompt = f"Recent conversation:\n{recent_context}\n\nNew message: {message}"
        else:
            routing_prompt = message
        
        # Get LLM decision
        response = await self.router_agent.run([ChatMessage(role=Role.USER, text=routing_prompt)])
        agent_name = response.text.strip().lower().split()[0]
        
        # Route to target agent executor
        target_agent = agent_name if agent_name in ["calendar", "directory", "email", "location", "risk"] else "proxy"
        
        # Send message to appropriate agent
        await ctx.send_message(
            ChatMessage(role=Role.USER, text=message),
            target_id=target_agent
        )

# Build workflow with LLM router
workflow = (
    WorkflowBuilder()
    # Router is a ChatAgent that returns agent name
    .register_executor(lambda: LLMRouterExecutor(client), name="router")
    
    # All specialist agents
    .register_executor(lambda: CalendarAgentExecutor(client, session_id), name="calendar")
    .register_executor(lambda: DirectoryAgentExecutor(client, session_id), name="directory")
    .register_executor(lambda: EmailAgentExecutor(client, session_id), name="email")
    .register_executor(lambda: LocationAgentExecutor(client, session_id), name="location")
    .register_executor(lambda: RiskAgentExecutor(client, session_id), name="risk")
    .register_executor(lambda: ProxyAgentExecutor(client, session_id), name="proxy")
    
    # Router connects to all agents
    .add_edge("router", "calendar")
    .add_edge("router", "directory")
    .add_edge("router", "email")
    .add_edge("router", "location")
    .add_edge("router", "risk")
    .add_edge("router", "proxy")
    
    # Start with router
    .set_start_executor("router")
    .build()
)

# Run workflow with recent context
async for event in workflow.run_stream({
    "message": user_message,
    "recent_context": recent_conversation_text
}):
    # Handle events
    pass
```

### 5. Client/Service Configuration

#### Before (Semantic Kernel)
```python
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

service = AzureChatCompletion(
    deployment_name=os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME"),
    api_key=os.getenv("OPENAI_API_KEY"),
    endpoint=os.getenv("OPENAI_ENDPOINT"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    service_id="azure_openai",
)
```

#### After (Agent Framework)
```python
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

client = AzureOpenAIChatClient(
    endpoint=os.getenv("OPENAI_ENDPOINT"),
    deployment_name=os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME"),
    credential=DefaultAzureCredential(),  # Or use API key
)
```

### 6. Message/History Handling

#### Before (Semantic Kernel)
```python
from semantic_kernel.contents import ChatMessageContent, AuthorRole

history = ChatHistory()
history.add_user_message("Hello")
history.add_assistant_message("Hi there!")

# Thread manages history
thread = ChatHistoryAgentThread()
```

#### After (Agent Framework)
```python
from agent_framework import ChatMessage, Role

messages = [
    ChatMessage(role=Role.USER, text="Hello"),
    ChatMessage(role=Role.ASSISTANT, text="Hi there!"),
]

# No explicit thread - context managed by workflow
```

## 📝 Migration Steps

### Step 1: Update Dependencies ✅
- Updated `requirements.txt` and `pyproject.toml`
- Added `agent-framework` and `azure-ai-agents`
- Commented out `semantic-kernel`

### Step 2: Create Tool Functions
Convert all `@kernel_function` methods in plugins to standalone tool functions:
- [ ] `plugins/graph_plugin.py` (40+ functions)
- [ ] `plugins/risk_plugin.py` (5+ functions)  
- [ ] `plugins/azure_maps_plugin.py` (3+ functions)

### Step 3: Create Agent Executors
Convert agent creation functions to Executor classes:
- [ ] `agents/calendar_agent.py` → `CalendarAgentExecutor`
- [ ] `agents/directory_agent.py` → `DirectoryAgentExecutor`
- [ ] `agents/email_agent.py` → `EmailAgentExecutor`
- [ ] `agents/location_agent.py` → `LocationAgentExecutor`
- [ ] `agents/risk_agent.py` → `RiskAgentExecutor`
- [ ] `agents/proxy_agent.py` → `ProxyAgentExecutor`

### Step 4: Build Workflow Orchestrator
Replace `MultiAgentOrchestrator` class:
- [ ] Create `RouterExecutor` for routing logic
- [ ] Build workflow with `WorkflowBuilder`
- [ ] Configure edges between router and agents
- [ ] Implement streaming event handling

### Step 5: Update API Integration
Modify API endpoints to use workflows:
- [ ] `api/main.py` - `/chat` endpoint
- [ ] `api/main.py` - streaming responses
- [ ] Update session management
- [ ] Adapt CosmosDB history persistence

### Step 6: Update Testing
- [ ] Update test files for Agent Framework
- [ ] Validate tool calling
- [ ] Test multi-agent routing
- [ ] Verify history persistence

## 🎯 Migration Strategy

### Option A: Big Bang Migration (Risky)
Migrate everything at once. Not recommended for production.

### Option B: Phased Migration (Recommended)
1. **Phase 1**: Create Agent Framework structure alongside Semantic Kernel
2. **Phase 2**: Migrate one agent at a time (start with simplest - ProxyAgent)
3. **Phase 3**: Test each agent thoroughly before moving to next
4. **Phase 4**: Switch API to use Agent Framework workflow
5. **Phase 5**: Remove Semantic Kernel dependencies

### Option C: Feature Flag (Safest for Production)
- Add feature flag to switch between SK and Agent Framework
- Deploy with both implementations
- Gradually shift traffic to Agent Framework
- Remove SK after validation

## 🚨 Key Considerations

1. **LLM-Based Routing** (CRITICAL):
   - Your current router uses an LLM to decide which agent handles each message
   - The router LLM responds with a single word: agent name
   - Recent conversation context is passed to handle ambiguous follow-ups ("yes", "ok", etc.)
   - In Agent Framework: Router is a ChatAgent, not manual logic
   - Preserve the `_ROUTER_SYSTEM` prompt exactly as-is

2. **Breaking Changes**:
   - Tool call tracking will need updates
   - CosmosDB message format may differ
   - Telemetry decorators need adaptation

2. **Tool Function Signatures**:
   - Remove `Annotated` type hints (Agent Framework uses simpler signatures)
   - Tool descriptions move to `ToolFunction` wrapper
   - Consider async/sync compatibility

3. **Session Management**:
   - Agent Framework workflows are stateless by design
   - Need external session state management (CosmosDB)
   - Workflow instances per request vs. singleton pattern

4. **Streaming**:
   - Agent Framework has native streaming via `run_stream()`
   - Events are more granular (ExecutorInvoked, ExecutorCompleted, etc.)
   - Need to adapt FastAPI SSE integration

5. **Error Handling**:
   - Different error types (`ExecutorFailedEvent`, `WorkflowFailedEvent`)
   - Need to catch and handle in event loop
   - Telemetry integration updates

## 📚 Resources

- Agent Framework GitHub: https://github.com/microsoft/agent-framework
- Agent Framework Docs: https://microsoft.github.io/agent-framework/
- Migration Examples: Run `aitk-get_agent_model_code_sample` for patterns

## ✅ Next Steps

**Immediate Action**: Choose migration strategy and get approval

**Recommended Path**: Phased Migration (Option B)
1. Start with creating new Agent Framework infrastructure
2. Migrate ProxyAgent first (no tools, simplest)
3. Test thoroughly
4. Migrate remaining agents one by one
5. Switch API integration last

Would you like me to:
1. **Start the phased migration** (create new files alongside existing)?
2. **Create a feature flag implementation** (both SK and AF running)?
3. **Do a big bang migration** (replace everything)?

Let me know which approach you prefer!
