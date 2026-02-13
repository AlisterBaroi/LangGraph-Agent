import uuid
import streamlit as st
from components.components import promptFunc
from agent import app  # Import the compiled graph

# from utils.utils import checkAPIKey

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reject_mode" not in st.session_state:
    st.session_state.reject_mode = False

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Verify Gemini API key
# checkAPIKey(streamlit=True)

# Page Settings & title
st.set_page_config(page_title="LangGraph AI Agent", page_icon="🤖", layout="centered")
st.subheader(
    "LangGraph AI Agent -- :red[Gemini]", anchor=False, text_alignment="center"
)
st.write(
    "I'm a :red[Web Search Agent]. I can use search to find information for you. Ask me to web search on any topic."
)
st.divider()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []


def main():
    # 1. Display Chat History
    for message in st.session_state.messages:
        role = "user" if message[0] == "user" else "assistant"
        with st.chat_message(role):
            st.write(message[1])

    # 2. Handle User Input
    user_input = promptFunc()

    if user_input:
        text_msg = user_input["text"]
        files = user_input["files"]

        # If files are attached, mention them in the text
        if files:
            file_names = [f.name for f in files]
            text_msg += f"\n(User attached files: {file_names})"

        # Add user message to history
        st.session_state.messages.append(("user", text_msg))

        # 3. Invoke Agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Pass the full history to the agent
                inputs = {"messages": st.session_state.messages}
                final_state = app.invoke(inputs)

                # Get the final response
                agent_response = final_state["messages"][-1].content
                st.write(agent_response)

        # Add agent response to history
        st.session_state.messages.append(("assistant", agent_response))


if __name__ == "__main__":
    main()
