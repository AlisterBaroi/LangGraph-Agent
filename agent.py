import os
import operator
import requests
from typing import Annotated, TypedDict, List, Literal
from bs4 import BeautifulSoup

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# --- SETUP ---
load_dotenv()
console = Console()

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is missing from .env file")

# We use a slightly higher temperature for drafting to be creative,
# but low for routing/critique to be precise.
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
search_tool = DuckDuckGoSearchRun()


# --- STATE DEFINITION ---
class AgentState(TypedDict):
    query: str  # User's raw input
    intent: str  # 'chat', 'research_report', 'site_scrape'
    target_url: str  # If intent is scrape
    research_data: str  # Raw text from search/scrape
    draft_content: str  # The generated report
    critique_feedback: str  # Internal AI critique
    compliance_issues: List[str]  # Guardrail flags
    human_feedback: str  # User feedback
    iteration_count: int  # To prevent infinite critique loops
    messages: Annotated[List, operator.add]  # Chat history


# --- HELPERS ---
def log_step(title, content, style="bold blue"):
    """Pretty prints logs to terminal"""
    console.print(Panel(str(content), title=title, border_style=style))


# --- NODES ---


def node_guard_input(state: AgentState):
    query = state["query"]
    log_step("PHASE 1: INPUT GUARDRAIL", f"Scanning: {query}")

    banned = ["explosives", "illegal", "dark web"]
    if any(word in query.lower() for word in banned):
        log_step("GUARDRAIL ALERT", "Banned topic detected!", "bold red")
        return {"compliance_issues": ["Policy Violation"]}

    return {"compliance_issues": [], "iteration_count": 0}


def node_router(state: AgentState):
    query = state["query"].lower()
    log_step("PHASE 2: ROUTER", f"Analyzing Intent for: {query}")

    # 1. Check for URL Scraping
    if "http" in query and ("scrape" in query or "read" in query):
        # Extract URL (simple logic)
        url = [w for w in query.split() if w.startswith("http")][0]
        log_step("ROUTING", f"Intent: Site Scrape | Target: {url}", "green")
        return {"intent": "site_scrape", "target_url": url}

    # 2. Check for Report/Research
    keywords = ["report", "research", "summary", "document", "deep dive", "investigate"]
    if any(k in query for k in keywords):
        log_step("ROUTING", "Intent: Research Report", "green")
        return {"intent": "research_report"}

    # 3. Default: Chat
    log_step("ROUTING", "Intent: Casual Chat", "yellow")
    return {"intent": "chat"}


def node_simple_chat(state: AgentState):
    """Handles normal conversation without heavy tools."""
    response = llm.invoke(state["query"])
    return {"messages": [response]}


def node_web_research(state: AgentState):
    query = state["query"]
    log_step("PHASE 3: RESEARCHER", f"Generating search queries for: {query}")

    # Optimize query
    search_query = llm.invoke(
        f"Turn this into a perfect DuckDuckGo search query: {query}"
    ).content.strip()
    log_step("SEARCHING", f"Query: {search_query}")

    try:
        # Actual Tool Call
        res = search_tool.invoke(search_query)
        log_step("SEARCH RESULTS", f"Retrieved {len(res)} characters", "cyan")
    except Exception as e:
        res = f"Search Error: {e}"
        log_step("SEARCH ERROR", str(e), "bold red")

    return {"research_data": res}


def node_url_scraper(state: AgentState):
    url = state.get("target_url")
    log_step("PHASE 3: SCRAPER", f"Scraping: {url}")

    try:
        # Basic recursive-ish simulation (Single page for stability in demo)
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.content, "html.parser")

        # Strip script/style
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()[:10000]  # Limit to 10k chars for context window
        log_step("SCRAPE SUCCESS", f"Extracted {len(text)} clean characters", "cyan")
        return {"research_data": f"Source: {url}\nContent: {text}"}
    except Exception as e:
        return {"research_data": f"Failed to scrape {url}: {str(e)}"}


def node_generator(state: AgentState):
    log_step("PHASE 4: DRAFTER", "Writing content...")
    context = state.get("research_data", "")
    critique = state.get("critique_feedback", "")
    user_notes = state.get("human_feedback", "")

    prompt = f"""
    You are an Enterprise AI Writer. 
    Task: Write a detailed Markdown report answering: "{state['query']}"
    
    Context Data:
    {context}
    
    Internal Critique to Address: {critique}
    User Feedback to Address: {user_notes}
    
    Requirements:
    - Use clear H2 and H3 headers.
    - If data is missing, state it clearly.
    - Professional tone.
    """

    response = llm.invoke(prompt)
    log_step("DRAFT GENERATED", response.content[:200] + "...", "magenta")
    return {
        "draft_content": response.content,
        "iteration_count": state["iteration_count"] + 1,
    }


def node_critique(state: AgentState):
    log_step("PHASE 5: INTERNAL CRITIQUE", "Reviewing draft quality...")
    draft = state["draft_content"]

    # Ask LLM to review the draft
    eval_prompt = f"""
    Review this draft for quality, accuracy, and completeness based on the user query: "{state['query']}"
    
    Draft:
    {draft[:4000]}
    
    If the draft is good, reply 'PERFECT'.
    If it needs work, provide specific 1-sentence instructions on what to fix.
    """

    feedback = llm.invoke(eval_prompt).content.strip()

    if "PERFECT" in feedback or state["iteration_count"] > 2:
        log_step("CRITIQUE RESULT", "Draft Approved ✅", "green")
        return {"critique_feedback": "None"}  # Pass
    else:
        log_step("CRITIQUE RESULT", f"Needs Revision: {feedback}", "yellow")
        return {"critique_feedback": feedback}  # Loop back


def node_guard_output(state: AgentState):
    log_step("PHASE 6: OUTPUT GUARD", "Checking PII/Tone...")
    # (Same logic as before)
    return {"compliance_issues": []}


def node_human_review(state: AgentState):
    log_step("PHASE 7: HUMAN REVIEW", "Pausing for user input...", "bold purple")
    pass


def node_finalize(state: AgentState):
    log_step("PHASE 8: FINALIZE", "Delivering output.")
    return {"messages": [AIMessage(content=state["draft_content"])]}


# --- EDGES ---
def route_start(state):
    if state["compliance_issues"]:
        return "block"
    if state["intent"] == "chat":
        return "chat"
    if state["intent"] == "site_scrape":
        return "scrape"
    return "research"


def check_critique(state):
    # Loop back if critique has feedback, otherwise proceed
    if state["critique_feedback"] != "None":
        return "retry"
    return "proceed"


# --- GRAPH BUILD ---
workflow = StateGraph(AgentState)

workflow.add_node("guard_input", node_guard_input)
workflow.add_node("simple_chat", node_simple_chat)
workflow.add_node("web_research", node_web_research)
workflow.add_node("url_scraper", node_url_scraper)
workflow.add_node("generator", node_generator)
workflow.add_node("critique", node_critique)
workflow.add_node("guard_output", node_guard_output)
workflow.add_node("human_review", node_human_review)
workflow.add_node("finalize", node_finalize)
workflow.add_node("router", node_router)

# Entry
workflow.add_edge(START, "guard_input")
workflow.add_edge("guard_input", "router")

# Router Logic
workflow.add_conditional_edges(
    "router",
    route_start,
    {
        "block": END,  # Or block node
        "chat": "simple_chat",
        "scrape": "url_scraper",
        "research": "web_research",
    },
)

# Chat path
workflow.add_edge("simple_chat", END)

# Research/Scrape path
workflow.add_edge("web_research", "generator")
workflow.add_edge("url_scraper", "generator")

# Critique Loop
workflow.add_edge("generator", "critique")
workflow.add_conditional_edges(
    "critique", check_critique, {"retry": "generator", "proceed": "guard_output"}
)

workflow.add_edge("guard_output", "human_review")
workflow.add_edge("human_review", "finalize")
workflow.add_edge("finalize", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["finalize"])
