# from utils.utils import checkAPIKey
# from typing import Annotated, Literal, TypedDict
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.tools import tool
# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode

# # Check Gemini API Key
# checkAPIKey()


# # 1 Defining tools. Test: A weather tool for agent to call ==
# @tool
# def get_weather(city: str):
#     # Weather API here for real app.
#     """Get the current weather for a specific city."""
#     return f"The weather in {city} is sunny and 25°C."


# # Create list of all tools
# tools = [get_weather]


# # 2 Define state: Track conversation history ==
# class AgentState(TypedDict):
#     # Auto-appends new messages to history
#     messages: Annotated[list, add_messages]


# # 3 Init model: Binding tools to model so it knows their existance ==
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
# llm_with_tools = llm.bind_tools(tools)


# # 4 Define graph nodes ==
# # Main node to call LLM
# def chatbot(state: AgentState):
#     return {"messages": [llm_with_tools.invoke(state["messages"])]}


# # Decide if agent needs to call a tool or is it done?
# def should_continue(state: AgentState) -> Literal["tools", END]:
#     messages = state["messages"]
#     last_message = messages[-1]

#     # If LLM calls a tool call, route to 'tools' node
#     if last_message.tool_calls:
#         return "tools"
#     # Else stop
#     return END


# # 6 Build graph
# workflow = StateGraph(AgentState)

# # Add nodes
# workflow.add_node("agent", chatbot)
# workflow.add_node(
#     # Note to self: ToolNode is a prebuilt LangGraph node
#     "tools",
#     ToolNode(tools),
# )

# # Add edges (connection logic)
# workflow.add_edge(START, "agent")
# workflow.add_conditional_edges("agent", should_continue)
# workflow.add_edge("tools", "agent")  # Loop back to agent after tool use

# # Compile graph
# app = workflow.compile()


# # 7 RUNNING TESTS

# # Example 1: A simple question (No tool needed)
# print("--- User: Hi! ---")
# final_state = app.invoke({"messages": [("user", "Hi! I am testing you.")]})
# print(f"Agent: {final_state['messages'][-1].content}")

# # Example 2: A question requiring a tool
# print("\n--- User: What's the weather in London? ---")
# final_state = app.invoke({"messages": [("user", "What is the weather in London?")]})
# print(f"Agent: {final_state['messages'][-1].content}")

from utils.utils import checkAPIKey
from typing import Annotated, Literal, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from ddgs import DDGS
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import datetime

# Check Gemini API Key
checkAPIKey(streamlit=False)


# --- 1. Define Tools ---
@tool
def web_search(query: str):
    """
    Finds information on the internet using DuckDuckGo.
    Useful for finding current events, stock prices, news, and real-time information.
    """
    print(f"\n--- [TOOL CALL] Web Search Query: '{query}' ---")

    try:
        # Using the direct DDGS library
        with DDGS() as ddgs:
            # backend="lite" is generally more robust for scripts
            results = list(ddgs.text(query, max_results=5, backend="lite"))

        if results:
            result_str = ""
            for i, res in enumerate(results, 1):
                title = res.get("title", "No Title")
                body = res.get("body", res.get("snippet", "No Content"))
                link = res.get("href", res.get("url", "No Link"))

                result_str += f"Result {i}: {title}\n{body}\nSource: {link}\n\n"

            print(f"--- [TOOL RESULT] Found {len(results)} results. ---")
            return result_str
        else:
            print("--- [TOOL RESULT] No results found. ---")
            return "No search results found."

    except Exception as e:
        error_msg = f"Error performing search: {str(e)}"
        print(f"--- [TOOL ERROR] {error_msg} ---")
        return error_msg


# List of tools
tools = [web_search]


# --- 2. Define State ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# --- 3. Initialize Model ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash"
)  # Updated to 2.0 Flash as you mentioned
llm_with_tools = llm.bind_tools(tools)

# --- 4. Define Nodes ---


def chatbot(state: AgentState):
    """The main chatbot node that calls the LLM."""
    last_msg = state["messages"][-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    print(f"\n--- [AGENT NODE] Processing Input: {user_text[:100]}... ---")

    # --- DYNAMIC SYSTEM PROMPT ---
    # We create the system message INSIDE the node so it always has the exact current time.
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sys_msg = SystemMessage(
        content=f"""
        You are a professional research assistant acting as a specialized search engine (when queried/intented by the users prompt to do web search, else just be a casual chat). Your goal is to provide deeply researched, structured answers.
        1. Analyze the user query and identify key entities and concepts.
        2. Execute multiple searches to gather diverse perspectives on the topic.
        3. Synthesize the findings into a structured report: Summary, Key Findings, Detailed Analysis, and Conclusion.
        4. If information is conflicting, note the discrepancy and the different sources.
        5 Use citation markers [1: link here], [2: link here] to reference findings (with links).
        
        Current Date and Time (for reference): {current_time}
        """
    )

    # Prepend the system message to the conversation history
    # This ensures the model sees the date immediately.
    messages = [sys_msg] + state["messages"]

    response = llm_with_tools.invoke(messages)

    print(f"--- [AGENT NODE] LLM Response: {response.content[:100]}... ---")
    if response.tool_calls:
        print(
            f"--- [AGENT NODE] Agent decided to call tool: {response.tool_calls[0]['name']} ---"
        )

    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", END]:
    """Router to decide if we need to call a tool or end the conversation."""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        print("--- [ROUTER] Decision: CONTINUE to 'tools' node ---")
        return "tools"

    print("--- [ROUTER] Decision: STOP (END) ---")
    return END


# --- 5. Build Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", chatbot)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()
