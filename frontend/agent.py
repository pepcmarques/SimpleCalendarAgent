"""
LangGraph agent for calendar event management using ChatOllama.
"""

from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from frontend.tools import all_tools


# Agent state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful calendar assistant that helps users manage their events.
You can help users:
- List their events
- Get details of specific events
- Create new events
- Update existing events
- Delete events

IMPORTANT: When you use a tool and receive results, you MUST include the full tool output in your response to the user. 
Do not summarize or paraphrase the tool results - show them exactly as returned.

When creating or updating events, use ISO format for dates and times (e.g., '2026-03-05T10:00:00').
Always be helpful and confirm actions with the user.

Today's date is provided by the user's system. If the user mentions relative dates like "tomorrow" or "next Monday", 
ask them to provide the specific date in YYYY-MM-DD format, or make a reasonable assumption and confirm with them.
"""


def create_agent(model_name: str = "llama3.2"):
    """Create a LangGraph agent with calendar tools."""
    
    # Initialize the LLM with tools
    llm = ChatOllama(model=model_name, temperature=0)
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Define the agent node
    def agent_node(state: AgentState) -> dict:
        """Process messages and decide on actions."""
        messages = state["messages"]
        
        # Add system message if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Define the routing function
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM made tool calls, route to the tool node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, end the conversation turn
        return END
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(all_tools))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    # Tools always go back to the agent
    workflow.add_edge("tools", "agent")
    
    # Compile and return the graph
    return workflow.compile()


class CalendarAgent:
    """Wrapper class for the calendar agent with conversation history."""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.graph = create_agent(model_name)
        self.messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    
    def chat(self, user_message: str) -> str:
        """Send a message to the agent and get a response."""
        # Add user message to history
        self.messages.append(HumanMessage(content=user_message))
        
        # Run the graph
        result = self.graph.invoke({"messages": self.messages})
        
        # Update message history
        self.messages = result["messages"]
        
        # Collect tool results and final AI response
        tool_results = []
        ai_response = ""
        
        for message in result["messages"]:
            if isinstance(message, ToolMessage) and message.content:
                tool_results.append(message.content)
        
        # Get the last AI message
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage) and message.content:
                ai_response = message.content
                break
        
        # If we have tool results that aren't reflected in the AI response, include them
        if tool_results:
            # Check if the important data from tool results is in the AI response
            last_tool_result = tool_results[-1]
            # If the AI response is short or doesn't contain key info, prepend tool results
            if len(ai_response) < 100 or ("ID" in last_tool_result and "ID" not in ai_response):
                return f"{last_tool_result}\n\n{ai_response}"
        
        return ai_response if ai_response else "I'm sorry, I couldn't process that request."
    
    def reset(self) -> None:
        """Reset the conversation history."""
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]
