import streamlit as st
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(
    page_title="Documentation - LangGraph Search Agent",
    page_icon="📚",
    layout="centered",
)
# Mermaid Diagram Code
mermaid_code = """
            graph TD
                %% Nodes
                START((Start)) --> NODE_AGENT

                subgraph "Agent Runtime Loop"
                    direction TB
                    NODE_AGENT["<b>Agent Node:</b><br/>(Gemini 2.5 Flash)<br/>1. Inject Date & System Prompt<br/>2. Decide: Search or Answer?"]:::ai
                    ROUTER{"<b>Router:</b><br/>Tool Call?"}:::decision
                    NODE_TOOLS["<b>Tool Node:</b><br/>(DuckDuckGo Search)<br/>Returns: Search Results"]:::tool
                end

                END((End))

                %% Flows
                NODE_AGENT --> ROUTER
                ROUTER -- "Yes" --> NODE_TOOLS
                ROUTER -- "No (Final Answer)" --> END

                NODE_TOOLS -- "Search Data" --> NODE_AGENT
            """
# --- Header ---
st.header(":red[Documentation] --")
st.markdown(
    """
A stateful AI Agent built with **LangGraph**, **Streamlit**, and **Google Gemini 2.5 Flash**. This agent is capable of browsing the web using DuckDuckGo to provide real-time, researched answers to user queries.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agent-orange)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-magenta)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
<hr>
    """,
    unsafe_allow_html=True,
)

# --- 1. WHAT & WHY ---
col1, col2 = st.columns(2)

with col1:
    st.header("🧐 What is this?")
    st.write(
        """
        This is a :red[**Stateful AI Research Assistant**]. Unlike standard chatbots that rely solely 
        on pre-trained knowledge, this agent is an autonomous system capable of **browsing the live web**.
        
        It is designed to act as a specialized search engine: it takes a user query, plans a research 
        strategy, executes live searches using :red[DuckDuckGo], and synthesizes the findings into a 
        structured, cited report.
        """
    )

with col2:
    st.header("🚀 Why use it?")
    st.write(
        """
        * :red[**Real-Time Knowledge**:] Bridges the gap between the LLM's training cutoff and the present moment. It knows today's news, stock prices, and events.
        * :red[**Grounded in Fact**:] The agent is prompted to use citations and avoid hallucination by strictly adhering to search results.
        * :red[**Transparent Reasoning**:] Using LangGraph, we can visualize exactly when the agent decides to search versus when it decides to answer.
        """
    )

st.divider()

# --- 2. ARCHITECTURE (The "How") ---
st.header("⚙️ Architecture & Workflow")
st.write(
    """
    The agent is built on a **Cyclic Graph** architecture. This allows the AI to "loop" — 
    thinking, acting (searching), and observing results repeatedly until it has a complete answer. Below is the architecturte shown as mermaid diagram, mermaid code, as well as action flow
    """
)

tab1, tab2, tab3 = st.tabs(
    ["**Mermaid Diagram**", "**Mermaid Code**", "**Action Flow**"]
)

with tab1:
    iframe_src = "https://mermaid.live/view#pako:eNplU2FvmzAQ_SuWpU4gpbQkEMCKMmUliSZ1yUTYh21MkwNu4g3syBh1XZT_vgOHUW2WkPBx7917d8cZ57JgmOCDoqcjSuNMIDg3N2gD8drcdukiSS1rp6nSto1ub-dos42X3xfr5SbNhEmqm73hyPDiwIRGSSM0rxh6lPKUYZPUnoIrlmsuBUrfDdGB8GuGZ_u54WhFkNndfj7bq7u5tWYVFxyNHR-tSlof7S7sOui9-AGcKKaaoTdo91JrVqGPSlYn3aWMHRSznAMZ2jGq8iOSCi1E_czU2wx_I4RQ3htpT7L9lC6Tc6ckkY1malCRSlmiB1qWgLwAsgDiGuy8xndu0u32cWfcdJh_zMRN_rN91vKqybhJmG6UqP8KTVjdlLo2KjXwmCpMFH3B5Sa2rKUobLuPwPhWpXy-jm9obTc64818Mu8Qhql9hnHjYbid-v-zNhJZKy5oeW2ffcWAiL76ADeQqxEYDn1doFOER7B5vMBEq4aNcMVURdsrPrdcGdZHVrEME3gt2BOFTrSrdAHYiYovUlY9UsnmcOwvzamATYg5hY0cMqBlTD1IWEtM_I4AkzP-hYkbTJ3AC8MwiLyJG7nudIRfMPFCJwr88cTz7kMv8v3Iv4zw767mvRNM_SAMI3ccBBN3Mp6MMCu4luqD-Z1yKZ74AV_-AFEWAMM"
    components.iframe(iframe_src, width=1920, height=550)


with tab2:
    # Render the diagram using a trick to embed Mermaid JS
    # Note: For production, a static image or specialized component is better,
    # but this works for docs pages.
    st.markdown(
        f"""
        <div class="mermaid">
        {mermaid_code}
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Fallback/Static explanation if JS fails or for clarity
with tab3:
    # with st.expander("📝 Click to see detailed step-by-step workflow"):
    st.markdown(
        """
        1.  **User Input**: The user sends a query (e.g., "Latest news on AI").
        2.  **Agent Node**: 
            * The system injects the **Current Date/Time** into the prompt.
            * Gemini 2.5 Flash analyzes the query.
        3.  **Router**:
            * If Gemini wants to know more, it calls the `web_search` tool.
            * If Gemini has enough info, it generates the final answer.
        4.  **Tool Node**: 
            * Executes the search using `ddgs` (DuckDuckGo).
            * Returns raw text snippets to the Agent.
        5.  **Loop**: The flow goes back to the **Agent Node**, which now sees the search results and synthesizes an answer.
        """
    )

st.divider()

# --- 3. TECH STACK ---
st.header("💻 Technology Stack")

t1, t2, t3 = st.columns(3)

with t1:
    st.subheader("Core Framework")
    st.markdown(
        """
        - :red[**LangGraph**:] For orchestrating the cyclic state machine and controlling the agent's flow.
        - :red[**LangChain**:] For interface definitions and tool binding.
        """
    )

with t2:
    st.subheader("Intelligence")
    st.markdown(
        """
        - :red[**Google Gemini 2.5 Flash**:] The brain of the operation. Chosen for its speed, huge context window, and native tool-calling abilities.
        - :red[**DuckDuckGo**:] The eyes of the agent, providing privacy-focused web search results.
        """
    )

with t3:
    st.subheader("Interface & Ops")
    st.markdown(
        """
        - :red[**Streamlit**:] The frontend UI for chat and interaction.
        - :red[**Rich**:] Used for beautiful, colored terminal logs.
        """
    )

st.divider()

# --- Footer ---
st.caption("Built with ❤️ by [:green[Alister Baroi]](https://github.com/alisterbaroi).")
