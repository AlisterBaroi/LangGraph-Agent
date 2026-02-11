import os, getpass
from dotenv import load_dotenv
from typing import Annotated, Literal, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Load variables from .env
load_dotenv()

# 0 Setup api key ==
if not os.environ.get("GOOGLE_API_KEY"):
    print("GEMENI_API_KEY Missing\nExiting")
    exit()


# 1 Defining tools. Test: A weather tool for agent to call ==
@tool
def get_weather(city: str):
    # Weather API here for real app.
    """Get the current weather for a specific city."""
    return f"The weather in {city} is sunny and 25°C."


# Create list of all tools
tools = [get_weather]


# 2 Define state: Track conversation history ==
class AgentState(TypedDict):
    # Auto-appends new messages to history
    messages: Annotated[list, add_messages]


# 3 Init model: Binding tools to model so it knows their existance ==
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
llm_with_tools = llm.bind_tools(tools)


# 4 Define graph nodes ==
# Main node to call LLM
def chatbot(state: AgentState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# Decide if agent needs to call a tool or is it done?
def should_continue(state: AgentState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]

    # If LLM calls a tool call, route to 'tools' node
    if last_message.tool_calls:
        return "tools"
    # Else stop
    return END


# 6 Build graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", chatbot)
workflow.add_node(
    # Note to self: ToolNode is a prebuilt LangGraph node
    "tools",
    ToolNode(tools),
)

# Add edges (connection logic)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")  # Loop back to agent after tool use

# Compile graph
app = workflow.compile()


# 7 RUNNING TESTS

# Example 1: A simple question (No tool needed)
print("--- User: Hi! ---")
final_state = app.invoke({"messages": [("user", "Hi! I am testing you.")]})
print(f"Agent: {final_state['messages'][-1].content}")

# Example 2: A question requiring a tool
print("\n--- User: What's the weather in London? ---")
final_state = app.invoke({"messages": [("user", "What is the weather in London?")]})
print(f"Agent: {final_state['messages'][-1].content}")
