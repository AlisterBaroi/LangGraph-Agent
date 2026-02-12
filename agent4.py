import os
import operator
from typing import Annotated, TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
MODEL_NAME = "gemini-2.0-flash"

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is missing from .env file")

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)
search_tool = DuckDuckGoSearchRun()


# --- STATE DEFINITION ---
class AgentState(TypedDict):
    query: str
    intent: str
    research_data: str
    draft_content: str
    compliance_issues: List[str]
    human_feedback: str
    messages: Annotated[List, operator.add]


# --- NODES ---


def node_guard_input(state: AgentState):
    query = state["query"]
    banned_keywords = ["explosives", "illegal", "dark web"]
    if any(word in query.lower() for word in banned_keywords):
        return {"compliance_issues": ["Policy Violation: Banned Topic Detected"]}
    return {"compliance_issues": []}


def node_block_request(state: AgentState):
    return {
        "messages": [
            AIMessage(content="I cannot fulfill this request due to safety guidelines.")
        ]
    }


def node_router(state: AgentState):
    query = state["query"].lower()
    if any(
        word in query
        for word in ["find", "search", "latest", "internet", "news", "trends"]
    ):
        return {"intent": "research"}
    return {"intent": "generate"}


def node_research_agent(state: AgentState):
    print(f"--- 🔍 Agent is Researching: {state['query']} ---")

    # 1. Stricter Prompt to prevent "Chatty" responses
    refine_prompt = f"""
    Convert this user query into a single, specific web search string. 
    Return ONLY the search string. Do not add quotes or explanations.
    User Query: {state['query']}
    """
    search_query = llm.invoke(refine_prompt).content.strip().replace('"', "")

    print(f"    Searching DDG for: '{search_query}'")

    try:
        results = search_tool.invoke(search_query)
        print(f"    ✅ Search successful. Retrieved {len(results)} chars.")
    except Exception as e:
        results = f"Search failed: {e}. Falling back to internal knowledge."
        print(f"    ❌ Search failed: {e}")

    return {"research_data": results}


def node_rag_agent(state: AgentState):
    print("--- ✍️ Agent is Writing Draft... ---")
    context = state.get("research_data", "No external research needed.")
    feedback = state.get("human_feedback", "")

    prompt = f"""
    You are an Enterprise Analyst. Write a professional report based ONLY on the context provided.
    User Request: {state['query']}
    Context: {context}
    Previous Feedback (if any): {feedback}
    Format: Use Markdown with clear headings.
    """
    response = llm.invoke(prompt)
    return {"draft_content": response.content}


def node_guard_output(state: AgentState):
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
    pass


def node_finalize_output(state: AgentState):
    return {"messages": [AIMessage(content=state["draft_content"])]}


def node_update_instructions(state: AgentState):
    return {}


# --- EDGES ---
def check_safety(state: AgentState):
    return "blocked" if state["compliance_issues"] else "safe"


def route_request(state: AgentState):
    return state["intent"]


workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("guard_input", node_guard_input)
workflow.add_node("block_request", node_block_request)
workflow.add_node("router", node_router)
workflow.add_node("research_agent", node_research_agent)
workflow.add_node("rag_agent", node_rag_agent)
workflow.add_node("guard_output", node_guard_output)
workflow.add_node("human_review", node_human_review)
workflow.add_node("finalize_output", node_finalize_output)
workflow.add_node("update_instructions", node_update_instructions)

# Edges
workflow.add_edge(START, "guard_input")
workflow.add_conditional_edges(
    "guard_input", check_safety, {"blocked": "block_request", "safe": "router"}
)
workflow.add_edge("block_request", END)
workflow.add_conditional_edges(
    "router", route_request, {"research": "research_agent", "generate": "rag_agent"}
)

# Main Flow
workflow.add_edge("research_agent", "rag_agent")
workflow.add_edge("rag_agent", "guard_output")
workflow.add_edge("guard_output", "human_review")
workflow.add_edge("human_review", "finalize_output")  # <--- THIS WAS MISSING!
workflow.add_edge("finalize_output", END)

# Compile
memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["finalize_output"])
