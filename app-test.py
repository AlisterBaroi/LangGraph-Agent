from typing import TypedDict
from langgraph.graph import StateGraph, END

# Define the state for this conditional graph
class ConditionalState(TypedDict):
  input: str # User's query
  next: str  # The next node to route to

# Define the functions
def check_query(state: ConditionalState) -> dict:
    """Checks the query and returns a routing decision."""
    query = state.get("input", "").lower()
    if "pricing" in query:
        return {"next": "pricing"}
    else:
        return {"next": "general"}

def pricing_info(state: ConditionalState) -> dict:
    """Provides pricing information."""
    print("Here’s detailed pricing information.")
    return {}

def general_info(state: ConditionalState) -> dict:
    """Provides general information."""
    print("Here’s some general information.")
    return {}

# Set up the graph
graph = StateGraph(ConditionalState)
graph.add_node("check", check_query)
graph.add_node("pricing", pricing_info)
graph.add_node("general", general_info)

# Set the entry point and the conditional edges
graph.set_entry_point("check")
graph.add_conditional_edges(
    "check", # The source node for the decision
    lambda state: state["next"], # A function to extract the routing key from the state
    {
        # A map of routing keys to destination nodes
        "pricing": "pricing",
        "general": "general"
    }
    )

# Add edges from the final nodes to the end
graph.add_edge("pricing", END)
graph.add_edge("general", END)

# Compile and run
app = graph.compile()
app.invoke({"input": "I need to know about your pricing plans."})
