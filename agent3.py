import os
import operator
from typing import Annotated, TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun  # <--- NEW IMPORT
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
# Using model
MODEL_NAME = "gemini-2.0-flash"

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is missing from .env file")

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)

# Initialize the Search Tool
search_tool = DuckDuckGoSearchRun()  # <--- INITIALIZE TOOL


# --- STATE DEFINITION ---
class AgentState(TypedDict):
    query: str  # The initial user request
    intent: str  # "research" or "generate"
    research_data: str  # Content gathered from web/docs
    draft_content: str  # The generated report
    compliance_issues: List[str]  # List of PII/Safety flags
    human_feedback: str  # Comments from the boss
    messages: Annotated[List, operator.add]  # Chat history


# --- NODES ---


def node_guard_input(state: AgentState):
    """Phase 1: Security Layer - Check if request is safe."""
    query = state["query"]
    banned_keywords = ["explosives", "illegal", "dark web"]
    if any(word in query.lower() for word in banned_keywords):
        return {"compliance_issues": ["Policy Violation: Banned Topic Detected"]}

    return {"compliance_issues": []}


def node_block_request(state: AgentState):
    """Terminal node for unsafe requests."""
    return {
        "messages": [
            AIMessage(content="I cannot fulfill this request due to safety guidelines.")
        ]
    }


def node_router(state: AgentState):
    """Phase 2: Router - Decide intent."""
    query = state["query"].lower()

    # Logic: If user asks to "find", "search", or "latest", go to Research.
    # Otherwise assume it's a drafting task.
    if any(word in query for word in ["find", "search", "latest", "internet"]):
        return {"intent": "research"}
    else:
        return {"intent": "generate"}


def node_research_agent(state: AgentState):
    """Phase 3: Researcher - USES DUCKDUCKGO SEARCH."""
    print(f"--- 🔍 Agent is Researching: {state['query']} ---")

    # 1. OPTIONAL: Use Gemini to convert chatty user text into a better search query
    # e.g. "What's up with AI?" -> "latest artificial intelligence trends 2025"
    refine_prompt = f"Convert this user query into a concise, effective web search string: {state['query']}"
    search_query = llm.invoke(refine_prompt).content.strip()

    print(f"    Searching DDG for: '{search_query}'")

    try:
        # 2. Execute Search
        results = search_tool.invoke(search_query)
        print(f"    ✅ Search successful. Retrieved {len(results)} chars.")
    except Exception as e:
        results = f"Search failed: {e}. Falling back to internal knowledge."
        print(f"    ❌ Search failed: {e}")

    return {"research_data": results}


def node_rag_agent(state: AgentState):
    """Phase 3: Generator."""
    print("--- ✍️ Agent is Writing Draft... ---")
    context = state.get("research_data", "No external research needed.")
    feedback = state.get("human_feedback", "")

    prompt = f"""
    You are an Enterprise Analyst. Write a professional report based ONLY on the context provided.
    User Request: {state['query']}
    
    Context (Search Results): 
    {context}
    
    Previous Manager Feedback (if any): {feedback}
    
    Format: Use Markdown with clear headings.
    """

    response = llm.invoke(prompt)
    return {"draft_content": response.content}


def node_guard_output(state: AgentState):
    """Phase 4: Output Safety - Redact PII."""
    draft = state["draft_content"]
    if "Confidential" in draft or "Secret" in draft:
        redacted = draft.replace("Confidential", "[REDACTED]").replace(
            "Secret", "[REDACTED]"
        )
        return {
            "draft_content": redacted,
            "compliance_issues": ["Redacted sensitive terms"],
        }
    return {"compliance_issues": []}


def node_human_review(state: AgentState):
    """Phase 5: The Boss - This node effectively just holds state for the interrupt."""
    pass  # The logic happens in the Conditional Edge or UI


def node_finalize_output(state: AgentState):
    """Final Step: Deliver content."""
    return {"messages": [AIMessage(content=state["draft_content"])]}


def node_update_instructions(state: AgentState):
    """Loop Step: Process feedback."""
    print(f"--- 🔄 Looping back with feedback: {state['human_feedback']} ---")
    # We append feedback to the state so the RAG agent sees it next time
    return {}  # State is already updated by the user input mechanism


# --- CONDITIONAL EDGES (The Routing Logic) ---
def check_safety(state: AgentState):
    return "blocked" if state["compliance_issues"] else "safe"


def route_request(state: AgentState):
    return state["intent"]


# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("guard_input", node_guard_input)
workflow.add_node("block_request", node_block_request)
workflow.add_node("router", node_router)
workflow.add_node("research_agent", node_research_agent)
workflow.add_node("rag_agent", node_rag_agent)
workflow.add_node("guard_output", node_guard_output)
workflow.add_node("human_review", node_human_review)
workflow.add_node("finalize_output", node_finalize_output)
workflow.add_node("update_instructions", node_update_instructions)

# 2. Add Edges
workflow.add_edge(START, "guard_input")

# Guardrail Logic
workflow.add_conditional_edges(
    "guard_input", check_safety, {"blocked": "block_request", "safe": "router"}
)
workflow.add_edge("block_request", END)

# Router Logic
workflow.add_conditional_edges(
    "router", route_request, {"research": "research_agent", "generate": "rag_agent"}
)

# Execution Flow
workflow.add_edge("research_agent", "rag_agent")
workflow.add_edge("rag_agent", "guard_output")
workflow.add_edge("guard_output", "human_review")

# 3. Compile with Checkpointer (Crucial for Human-in-the-Loop)
# MEMORY & COMPILE
memory = MemorySaver()

# We interrupt BEFORE the 'finalize_output' node to let human review
app = workflow.compile(checkpointer=memory, interrupt_before=["finalize_output"])

# --- TEST RUNNER (Optional, for terminal testing) ---
if __name__ == "__main__":
    import uuid

    # Thread ID is required for memory/checkpoints
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("--- 🚀 Starting Agent with DuckDuckGo Search ---")
    user_input = "Search for the latest stock price of NVIDIA"
    # user_input = "Search for the latest trends in AI agents and write a summary."

    # 1. Start the graph until it hits the interrupt
    print(f"User: {user_input}")
    for event in app.stream({"query": user_input}, config=config):
        pass

    # 2. Inspect State at the Interrupt
    snapshot = app.get_state(config)
    print("\n--- ✋ PAUSED FOR HUMAN REVIEW ---")
    print(f"Draft:\n{snapshot.values.get('draft_content')}")
