import os
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import AzureChatOpenAI

from dotenv import load_dotenv
from prompts.graph_prompts import prompts
from tools.graph_tools import GraphTools
 
load_dotenv(override=True)

class Agent:
    def __init__(self):
        self.state = Agent.GraphState(messages=[], recursions=0)
        self.graph_tools = GraphTools()
        self.all_tools = self.graph_tools.tools()
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv('OPENAI_ENDPOINT'),
            azure_deployment=os.getenv('OPENAI_MODEL_DEPLOYMENT_NAME'),
            api_version=os.getenv('OPENAI_VERSION'),
            streaming=False
        )
        self.llm_with_tools = self.llm.bind_tools(self.all_tools)
        self.memory = MemorySaver()
        self.max_recursions = 25
        self.system_message = prompts.master_prompt()
        self.graph = self.build_graph()

    class GraphState(TypedDict):
        messages: Annotated[list, add_messages]
        recursions: int

    def stream_graph_updates(self, role: str, content: str):
        config = {"configurable": {"thread_id": "1"}}
        
        # Import LangChain message types
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # Create proper LangChain message object
        if role == "user":
            message = HumanMessage(content=content)
        elif role == "assistant":
            message = AIMessage(content=content)
        elif role == "system":
            message = SystemMessage(content=content)
        else:
            # Default to HumanMessage
            message = HumanMessage(content=content)
        
        events = self.graph.stream(
            {
                "messages": [message],
                "recursions": 0
            },
            config,
            stream_mode="values",
        )
        for event in events:
            last_message = event["messages"][-1]
            # last_message.pretty_print()
        return last_message

    def chat_node(self, state):
        """Chat node that processes messages and handles tool calls."""
        # Extract the current list of messages from the state
        messages = state["messages"]
        recursions = state["recursions"]

        # Add system message if this is the first message
        if len(messages) == 1 and hasattr(messages[0], 'type') and messages[0].type == "human":
            from langchain_core.messages import SystemMessage
            system_msg = SystemMessage(content=self.system_message)
            messages = [system_msg] + messages

        # Check recursion limit
        if recursions >= self.max_recursions:
            print(f"  - Recursion limit of {self.max_recursions} reached. Ending conversation.")
            from langchain_core.messages import AIMessage
            return {
                "messages": [AIMessage(content=f"I've reached the maximum recursion limit of {self.max_recursions}. Please start a new conversation.")], 
                "recursions": recursions
            }

        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response], "recursions": recursions + 1}

    def should_continue(self, state):
        """Determine whether to continue with tools or end based on recursion limit and tool calls."""
        recursions = state["recursions"]
        
        # If we've hit the recursion limit, end the conversation
        if recursions >= self.max_recursions:
            return END
        
        # Check if the last message has tool calls
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        else:
            return END

    def build_graph(self):
        """Build the LangGraph state graph."""
        graph_builder = StateGraph(self.GraphState)
        graph_builder.add_node("chat_node", self.chat_node)
        graph_builder.add_edge(START, "chat_node")

        tool_node = ToolNode(tools=self.all_tools)
        graph_builder.add_node("tools", tool_node)
        graph_builder.add_conditional_edges(
            "chat_node",
            self.should_continue,
        )
        graph_builder.add_edge("tools", "chat_node")
        graph = graph_builder.compile(checkpointer=self.memory)
        return graph

    def clear_conversation_state(self):
        """Clear all conversation state from memory."""
        try:
            # Clear the memory saver by creating a new instance
            self.memory = MemorySaver()
            # Rebuild the graph with the new memory
            self.graph = self.build_graph()
            print("✓ Conversation state cleared successfully.")
        except Exception as e:
            print(f"⚠ Error clearing state: {e}")
            print("You may need to restart the application for a complete reset.")

    def invoke_graph(self, messages: list, config: dict = None):
        """
        Invoke the graph with the provided messages and configuration.
        
        Args:
            messages (list): List of messages to start the conversation. Can be dicts, 
                           OpenAIModels.Message objects, or LangChain Message objects.
            config (dict, optional): Configuration for the graph. Defaults to None.
        
        Returns:
            dict: The final state of the graph after processing the messages.
        """
        if config is None:
            config = {"configurable": {"thread_id": "1"}}
        
        # Import LangChain message types
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # Format messages to ensure they are LangChain Message objects
        formatted_messages = []
        for msg in messages:
            # Handle dict, OpenAIModels.Message, and LangChain Message object types
            if isinstance(msg, dict):
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    formatted_message = HumanMessage(content=content)
                elif role == "assistant":
                    formatted_message = AIMessage(content=content)
                elif role == "system":
                    formatted_message = SystemMessage(content=content)
                else:
                    # Default to HumanMessage for unknown roles
                    formatted_message = HumanMessage(content=content)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                # Handle OpenAIModels.Message objects (Pydantic models)
                role = msg.role
                content = msg.content
                if role == "user":
                    formatted_message = HumanMessage(content=content)
                elif role == "assistant":
                    formatted_message = AIMessage(content=content)
                elif role == "system":
                    formatted_message = SystemMessage(content=content)
                else:
                    # Default to HumanMessage for unknown roles
                    formatted_message = HumanMessage(content=content)
            else:
                # Already a LangChain Message object
                formatted_message = msg
            formatted_messages.append(formatted_message)
        
        messages = formatted_messages

        return self.graph.invoke(
            {"messages": messages, "recursions": 0},
            config
        )

    


def main():
    """Example usage of the Agent class."""
    agent = Agent()
    result = agent.invoke_graph([{"role": "user", "content": "Hello, how are you?"}])
    print(f"Final result: {result}")


if __name__ == "__main__":
    main()