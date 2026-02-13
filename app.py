# import streamlit as st
# from utils.utils import checkAPIKey
# from components.components import promptFunc

# # Verify Gemini API key
# checkAPIKey()

# # Page settings
# st.set_page_config(page_title="LangGraph AI Agent", page_icon="👋", layout="centered")

# # Page title
# st.header("LangGraph AI Agent -- :red[Gemini]", text_alignment="center")


# def main():
#     # This now returns a dict {text, files, audio} or None
#     user_input = promptFunc()

#     if user_input:
#         # Example: Extracting data to send to your LangGraph agent
#         text_msg = user_input["text"]
#         files = user_input["files"]
#         audio = user_input["audio"]

#         # --- PDF LOGIC (Your specific request) ---
#         if files:
#             for file in files:
#                 if file.type == "application/pdf":
#                     st.toast(f"Processing PDF: {file.name}", icon="⚙️")
#                     # TODO: Call your PDF extraction function here
#                     # pdf_text = extract_text_from_pdf(file)
#                     # text_msg += f"\n\nContext from PDF:\n{pdf_text}"

#         # Send to agent (Agent logic from previous steps goes here)
#         # response = app.invoke({"messages": [("user", text_msg)]})

#         # Placeholder response
#         with st.chat_message("assistant"):
#             st.write(f"I received your message: '{text_msg}'")
#             if files:
#                 st.write(f"I also received {len(files)} file(s).")
#             if audio:
#                 st.write("I also received an audio clip.")


# if __name__ == "__main__":
#     main()


import streamlit as st
from utils.utils import checkAPIKey
from components.components import promptFunc
from agent import app  # Import the compiled graph

# Verify Gemini API key
checkAPIKey()

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
