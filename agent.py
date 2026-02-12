import os
import operator
from typing import Annotated, TypedDict, List, Dict, Union, Literal

# LangChain / LangGraph Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
# We use flash for speed. If this errors again, try "gemini-1.0-pro"
MODEL_NAME = "gemini-2.0-flash"

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is missing from .env file")

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)


# --- STATE DEFINITION ---
# This is the "Shared Brain" of your agent
class AgentState(TypedDict):
    query: str  # The initial user request
    intent: str  # "research" or "generate"
    research_data: str  # Content gathered from web/docs
    draft_content: str  # The generated report
    compliance_issues: List[str]  # List of PII/Safety flags
    human_feedback: str  # Comments from the boss
    messages: Annotated[List, operator.add]  # Chat history


# --- NODES (The Logic Units) ---


def node_guard_input(state: AgentState):
    """Phase 1: Security Layer - Check if request is safe."""
    query = state["query"]

    # Simple rule-based guardrail for demo purposes
    banned_keywords = ["explosives", "competitor pricing", "illegal"]
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
    """Phase 3: Researcher - Simulates gathering external data."""
    print("--- 🔍 Agent is Researching... ---")

    # In a real app, this would call Tavily/Google Search.
    # We simulate it here to ensure your demo works immediately.
    simulated_research = f"Research Data found for: {state['query']}. [Source: Internal Knowledge Base + Web Snippets]"

    return {"research_data": simulated_research}


def node_rag_agent(state: AgentState):
    """Phase 3: Generator - Writes the draft."""
    print("--- ✍️ Agent is Writing Draft... ---")

    context = state.get("research_data", "No external research needed.")
    feedback = state.get("human_feedback", "")

    prompt = f"""
    You are an Enterprise Assistant. Write a professional report.
    User Query: {state['query']}
    Context: {context}
    Previous Feedback (if any): {feedback}
    """

    response = llm.invoke(prompt)
    return {"draft_content": response.content}


def node_guard_output(state: AgentState):
    """Phase 4: Output Safety - Redact PII."""
    draft = state["draft_content"]

    # Simulation: Redact the word "Secret" or hypothetical phone numbers
    # Real app would use a PII Presidio analyzer
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
    if state["compliance_issues"]:
        return "blocked"
    return "safe"


def route_request(state: AgentState):
    if state["intent"] == "research":
        return "research"
    return "generate"


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
memory = MemorySaver()

# We interrupt BEFORE the 'finalize_output' node to let human review
app = workflow.compile(checkpointer=memory, interrupt_before=["finalize_output"])

# --- RUNNER (For Testing in Terminal) ---
if __name__ == "__main__":
    import uuid

    # Thread ID is required for memory/checkpoints
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("--- 🚀 Starting Enterprise Agent Demo ---")
    user_input = "Search for the latest trends in AI agents and write a summary."

    # 1. Start the graph until it hits the interrupt
    print(f"User: {user_input}")
    for event in app.stream({"query": user_input}, config=config):
        for key, value in event.items():
            print(f"Finished Node: {key}")

    # 2. Inspect State at the Interrupt
    snapshot = app.get_state(config)
    print("\n--- ✋ PAUSED FOR HUMAN REVIEW ---")
    print(f"Current Draft: {snapshot.values.get('draft_content')}")

    # 3. Simulate Human Feedback
    decision = input("\nType 'approve' to finish, or provide feedback to rewrite: ")

    if decision.lower() == "approve":
        # Continue to Finalize
        print("--- Human Approved. Finalizing... ---")
        for event in app.stream(None, config=config):  # Resume
            for key, value in event.items():
                print(f"Finished Node: {key}")
                if "messages" in value:
                    print(f"\nFINAL OUTPUT:\n{value['messages'][-1].content}")

    else:
        # Loop back
        print("--- Human Rejected. Sending feedback... ---")
        # Update state with feedback
        app.update_state(config, {"human_feedback": decision})
        # Determine where to go next (Back to generation)
        # Note: In LangGraph, we can just call invoke/stream again,
        # but to explicitly route via our diagram, we might manually set next node
        # or use a conditional edge from 'human_review'.
        # For this simple linear script, we will just update state and re-run the generator node logic:

        # We redirect the graph execution to 'rag_agent'
        # (This is an advanced LangGraph feature: Time Travel / Forking)
        # For simplicity in this demo, we effectively 'resume' but pointing to the update node
        # if we had wired the conditional edge.

        # Let's keep it simple: We just print that we would loop back.
        print(
            "(In a full UI, this would trigger the 'update_instructions' -> 'rag_agent' loop)"
        )
