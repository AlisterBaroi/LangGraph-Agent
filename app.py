import streamlit as st
import uuid
import time
from langchain_core.messages import AIMessage, HumanMessage
from agent import app

# --- CONFIG ---
st.set_page_config(page_title="Enterprise Agent", layout="centered")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reject_mode" not in st.session_state:
    st.session_state.reject_mode = False

config = {"configurable": {"thread_id": st.session_state.thread_id}}


def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.01)


# --- MAIN UI ---
st.title("🛡️ Governance Agent")

# 1. History
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)
        # Only show download button if it's actually a report (longer content)
        if role == "assistant" and len(msg.content) > 500:
            st.download_button(
                "📄 Download Report",
                msg.content,
                "report.md",
                key=f"dl_{hash(msg.content)}",
            )

# 2. Check Graph State
snapshot = app.get_state(config)
next_nodes = snapshot.next or ()
is_paused = bool("finalize" in next_nodes)

# 3. Review UI
if is_paused:
    last_draft = snapshot.values.get("draft_content", "")

    st.info("⚠️ Review Required: The agent has generated a draft.")
    with st.expander("📝 Preview Draft", expanded=True):
        st.markdown(last_draft)

    col1, col2 = st.columns(2)

    # UI STATE:
    # If in reject mode, "Approve" is disabled. "Reject" is disabled (or changed to "Cancel" logic if you prefer).
    approve_disabled = st.session_state.reject_mode

    with col1:
        if st.button(
            "✅ Approve",
            type="primary",
            use_container_width=True,
            disabled=approve_disabled,
        ):
            with st.spinner("Finalizing..."):
                for event in app.stream(None, config=config):
                    pass
                final = app.get_state(config)
                last_msg = final.values["messages"][-1]
                st.session_state.messages.append(last_msg)
                st.rerun()

    with col2:
        # If already rejecting, maybe show "Cancel Revision"?
        # For now, let's keep it simple: Reject button enables the mode.
        if st.button(
            "❌ Reject & Edit",
            use_container_width=True,
            disabled=st.session_state.reject_mode,
        ):
            st.session_state.reject_mode = True
            st.rerun()

    if st.session_state.reject_mode:
        st.warning(
            "✍️ **Revision Mode Active**: Type your feedback in the chat bar below to rewrite the draft."
        )

# 4. Chat Input
# Chat is enabled if: (Not paused) OR (Paused AND In Reject Mode)
disable_chat = is_paused and not st.session_state.reject_mode

user_input = st.chat_input("Type your request here...", disabled=disable_chat)

if user_input:
    # A. Handling Rejection Feedback
    if st.session_state.reject_mode:
        st.session_state.reject_mode = False

        # Log feedback
        st.session_state.messages.append(
            HumanMessage(content=f"Feedback: {user_input}")
        )
        with st.chat_message("user"):
            st.write(f"Feedback: {user_input}")

        # REWIND GRAPH to Generator Node with new feedback
        app.update_state(config, {"human_feedback": user_input}, as_node="generator")

        with st.spinner("Revising draft based on feedback..."):
            for event in app.stream(None, config=config):
                pass
        st.rerun()

    # B. Normal Request
    else:
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Agent is working..."):
                for event in app.stream({"query": user_input}, config=config):
                    pass

            final = app.get_state(config)
            if not final.next:
                # Finished
                last_msg = final.values["messages"][-1]
                st.write_stream(stream_text(last_msg.content))
                st.session_state.messages.append(last_msg)
            else:
                # Paused (Review)
                st.rerun()
