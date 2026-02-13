import os
import operator
import requests
import time
from typing import Annotated, TypedDict, List, Literal
from bs4 import BeautifulSoup

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage
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

# High creativity for drafting
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.4)
# Zero temp for logic/routing
llm_logic = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

search_tool = DuckDuckGoSearchRun()


# --- STATE DEFINITION ---
class AgentState(TypedDict):
    query: str
    intent: str
    target_url: str
    research_data: str
    draft_content: str
    critique_feedback: str
    compliance_issues: List[str]
    human_feedback: str
    iteration_count: int
    messages: Annotated[List[BaseMessage], operator.add]


# --- HELPERS ---
def log_step(title, content, style="bold blue"):
    console.print(Panel(str(content), title=title, border_style=style))


# --- NODES ---


def node_parse_input(state: AgentState):
    if not state["messages"] or not isinstance(state["messages"][-1], HumanMessage):
        return {"messages": [HumanMessage(content=state["query"])]}
    return {}


def node_guard_input(state: AgentState):
    query = state["query"]
    log_step("PHASE 1: INPUT GUARDRAIL", f"Scanning: {query}")
    banned = ["explosives", "illegal", "dark web"]
    if any(word in query.lower() for word in banned):
        return {"compliance_issues": ["Policy Violation"]}
    return {"compliance_issues": [], "iteration_count": 0}


def node_router(state: AgentState):
    query = state["query"]
    log_step("PHASE 2: ROUTER", f"Analyzing: {query}")

    if "http" in query and ("scrape" in query or "read" in query):
        url = [w for w in query.split() if w.startswith("http")][0]
        return {"intent": "site_scrape", "target_url": url}

    # Enhanced Classification Prompt
    prompt = f"""
    Classify the user intent. Return ONLY the category name.
    
    1. 'quick_search': User wants a specific fact, number, date, or status. 
       Examples: "What is NVDA price?", "Who is the CEO of Google?", "Weather in London".
    
    2. 'research_report': User wants a deep dive, summary, document, or analysis.
       Examples: "Write a report on AI", "Summarize this topic", "Deep dive into NVDA".
       
    3. 'chat': Casual conversation.
    
    User Query: "{query}"
    """
    intent = llm_logic.invoke(prompt).content.strip().lower()

    if "quick" in intent or "search" in intent:
        log_step("ROUTING", "Intent: Quick Search", "cyan")
        return {"intent": "quick_search"}
    elif "report" in intent or "research" in intent:
        log_step("ROUTING", "Intent: Research Report", "green")
        return {"intent": "research_report"}

    log_step("ROUTING", "Intent: Casual Chat", "yellow")
    return {"intent": "chat"}


def node_simple_chat(state: AgentState):
    log_step("PHASE 3: CHAT", "Generating response...")
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def node_web_research(state: AgentState):
    query = state["query"]
    log_step("PHASE 3: RESEARCHER", f"Query: {query}")

    search_query = (
        llm_logic.invoke(f"Create a specific DuckDuckGo search query for: {query}")
        .content.strip()
        .replace('"', "")
    )
    log_step("SEARCHING", f"Query: {search_query}")

    try:
        res = search_tool.invoke(search_query)
        log_step("SEARCH SUCCESS", f"Retrieved {len(res)} chars", "cyan")
    except Exception as e:
        res = f"Search Failed: {e}"
    return {"research_data": res}


def node_url_scraper(state: AgentState):
    url = state.get("target_url")
    log_step("PHASE 3: SCRAPER", f"Scraping: {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()[:8000]
        return {"research_data": f"Source: {url}\nContent: {text}"}
    except Exception as e:
        return {"research_data": f"Failed to scrape {url}: {str(e)}"}


def node_generator(state: AgentState):
    log_step("PHASE 4: GENERATOR", "Writing content...")
    context = state.get("research_data", "")
    feedback = state.get("human_feedback", "")
    intent = state.get("intent", "research_report")

    # DYNAMIC PROMPT SELECTION
    if feedback:
        log_step("REVISION", f"Applying user feedback: {feedback}", "bold magenta")
        system_instruction = f"""
        CRITICAL INSTRUCTION: You are revising a previous output. 
        The user REJECTED the last draft. 
        You MUST incorporate this feedback: "{feedback}"
        Do not ignore this. Change the tone, length, or content as requested.
        """
    elif intent == "quick_search":
        system_instruction = "You are a helpful assistant. Answer the user's question directly and concisely based on the context. Do NOT write a full report with headers."
    else:
        system_instruction = "You are an Enterprise AI Analyst. Write a detailed Markdown report with headers (Executive Summary, Key Findings, etc)."

    prompt = f"""
    {system_instruction}
    
    User Query: "{state['query']}"
    
    Context Data:
    {context}
    """

    response = llm.invoke(prompt)
    return {
        "draft_content": response.content,
        "iteration_count": state["iteration_count"] + 1,
    }


def node_critique(state: AgentState):
    # Skip critique for quick searches or if user already gave feedback
    if state.get("intent") == "quick_search" or state.get("human_feedback"):
        return {"critique_feedback": "None"}

    log_step("PHASE 5: CRITIQUE", "Reviewing...")
    draft = state["draft_content"]
    eval_prompt = f"Review this report for the query '{state['query']}'. If good, say PERFECT. Else give 1 sentence fix."
    feedback = llm_logic.invoke(eval_prompt).content.strip()

    if "PERFECT" in feedback or state["iteration_count"] > 1:
        log_step("CRITIQUE", "Approved ✅", "green")
        return {"critique_feedback": "None"}
    else:
        log_step("CRITIQUE", f"Revision needed: {feedback}", "yellow")
        return {"critique_feedback": feedback}


def node_guard_output(state: AgentState):
    return {"compliance_issues": []}


def node_human_review(state: AgentState):
    log_step("PHASE 7: HUMAN REVIEW", "Waiting for approval...", "bold purple")
    pass


def node_finalize(state: AgentState):
    return {"messages": [AIMessage(content=state["draft_content"])]}


# --- EDGES ---
def route_start(state):
    if state["compliance_issues"]:
        return "block"
    if state["intent"] == "chat":
        return "chat"
    if state["intent"] == "site_scrape":
        return "scrape"
    # Both quick_search and research_report go to research first
    return "research"


def check_critique(state):
    if state["critique_feedback"] != "None":
        return "retry"
    return "proceed"


# --- GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("parse_input", node_parse_input)
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

workflow.add_edge(START, "parse_input")
workflow.add_edge("parse_input", "guard_input")
workflow.add_edge("guard_input", "router")

workflow.add_conditional_edges(
    "router",
    route_start,
    {
        "block": END,
        "chat": "simple_chat",
        "scrape": "url_scraper",
        "research": "web_research",
    },
)

workflow.add_edge("simple_chat", END)
workflow.add_edge("web_research", "generator")
workflow.add_edge("url_scraper", "generator")
workflow.add_edge("generator", "critique")
workflow.add_conditional_edges(
    "critique", check_critique, {"retry": "generator", "proceed": "guard_output"}
)
workflow.add_edge("guard_output", "human_review")
workflow.add_edge("human_review", "finalize")
workflow.add_edge("finalize", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["finalize"])
