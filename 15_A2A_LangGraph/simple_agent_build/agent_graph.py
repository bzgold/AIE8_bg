"""LangGraph agent with a single node that calls the A2A agent."""
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from simple_agent_build.a2a_tool import call_a2a_agent


class AgentState(TypedDict):
    """State for the simple agent."""
    messages: Annotated[list, add_messages]


def build_agent_graph():
    """Build a LangGraph with one node that calls the A2A agent.
    
    Graph structure:
    - Entry point: agent node
    - Agent node: Calls A2A agent and returns response
    - End: Terminal state
    
    Returns:
        Compiled LangGraph agent
    """
    
    async def agent_node(state: AgentState) -> AgentState:
        """Agent node that forwards queries to the A2A agent."""
        messages = state["messages"]
        
        # Extract the user's query from the last message
        user_query = None
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                user_query = msg.content
                break
        
        if not user_query:
            return {
                "messages": [{"role": "assistant", "content": "I didn't receive a valid query."}]
            }
        
        # Call the A2A research agent
        try:
            response = await call_a2a_agent(user_query)
            return {"messages": [{"role": "assistant", "content": response}]}
        except Exception as e:
            error_msg = f"Failed to get response from research agent: {str(e)}"
            return {"messages": [{"role": "assistant", "content": error_msg}]}
    
    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    
    return workflow.compile()


async def run_agent(query: str) -> str:
    """Run the agent with a query and return the response.
    
    Args:
        query: User query to process
        
    Returns:
        Agent's response
    """
    graph = build_agent_graph()
    
    # Prepare input
    inputs = {"messages": [HumanMessage(content=query)]}
    
    # Run the graph and get the final state
    final_state = None
    async for state in graph.astream(inputs, stream_mode="values"):
        final_state = state
    
    if final_state and final_state.get("messages"):
        last_message = final_state["messages"][-1]
        if hasattr(last_message, 'content'):
            return last_message.content
        elif isinstance(last_message, dict) and 'content' in last_message:
            return last_message['content']
    
    return "No response generated."

