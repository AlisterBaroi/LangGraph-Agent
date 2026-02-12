import streamlit as st
import uuid
from langchain_core.messages import AIMessage, HumanMessage
from agent import app  # Import the new backend

# --- CONFIG ---
st.set_page_config(page_title="Enterprise Agent", layout="centered")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "review_mode" not in st.session_state:
    st.session_state.review_mode = False
if "last_draft" not in st.session_state:
    st.session_state.last_draft = ""

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# --- SIDEBAR LOGS ---
with st.sidebar:
    st.header("⚙️ System Logs")
    # You could tail the terminal logs here if using a log file,
    # but for now we show graph state.
    try:
        cur_state = app.get_state(config)
        if cur_state.next:
            st.info(f"Node: {cur_state.next[0]}")
            st.json(cur_state.values.get("intent", "Init"))
        else:
            st.success("System Idle")
    except:
        pass

# --- MAIN CHAT ---
st.title("🛡️ Governance Agent")

# 1. Display History
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)
        # Check if this message was a report (simple heuristic: long length)
        if role == "assistant" and len(msg.content) > 500:
            st.download_button(
                label="📄 Download Report",
                data=msg.content,
                file_name="report.md",
                mime="text/markdown",
                key=f"dl_{hash(msg.content)}",
            )

# 2. Check for Interrupt (Human Review)
snapshot = app.get_state(config)
if snapshot.next and "finalize" in snapshot.next:
    st.session_state.review_mode = True
    st.session_state.last_draft = snapshot.values.get("draft_content")
else:
    st.session_state.review_mode = False

# 3. Input Area Logic
if st.session_state.review_mode:
    # --- REVIEW MODE UI ---
    st.info("⚠️ Review Required: The agent has generated a report.")

    with st.expander("📝 Preview Draft Report", expanded=True):
        st.markdown(st.session_state.last_draft)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            # Resume graph
            with st.spinner("Finalizing..."):
                for event in app.stream(None, config=config):
                    pass
                # Refresh to show final message
                final_state = app.get_state(config)
                last_msg = final_state.values["messages"][-1]
                st.session_state.messages.append(last_msg)
                st.rerun()

    with col2:
        if st.button("❌ Reject & Edit", use_container_width=True):
            # This is a UI state change only.
            # We want to clear the 'review mode' visual but keep the graph paused
            # so the user can type feedback in the main box.
            # However, to strictly follow your request:
            # "Reject clicked -> buttons disappear, chat enabled"
            st.session_state.rejecting = True
            st.rerun()

    # Disable chat input while waiting for button click
    # Unless they clicked "Reject", in which case we want input
    disable_input = True
    if st.session_state.get("rejecting"):
        disable_input = False
        st.warning("Please type your feedback below to revise the report.")

else:
    disable_input = False

# 4. Chat Input
user_input = st.chat_input(
    "Type your request here...",
    disabled=disable_input and not st.session_state.get("rejecting", False),
)

if user_input:
    # Case A: Handling Rejection Feedback
    if st.session_state.get("rejecting"):
        # Update state with feedback and loop back
        app.update_state(config, {"human_feedback": user_input}, as_node="generator")
        st.session_state.rejecting = False  # Reset
        with st.spinner("Revising report..."):
            for event in app.stream(None, config=config):
                pass
        st.rerun()

    # Case B: New Request
    else:
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("Agent is working..."):
            # Stream events
            # Note: We aren't doing token-by-token streaming here yet to keep it simple,
            # but we are streaming the Graph Events.
            for event in app.stream({"query": user_input}, config=config):
                pass

            # If it finished (Chat intent), append message
            final = app.get_state(config)
            if not final.next:
                last_msg = final.values["messages"][-1]
                st.session_state.messages.append(last_msg)
                st.rerun()
            else:
                # It paused for review
                st.rerun()
