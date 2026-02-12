import streamlit as st
from utils.utils import checkAPIKey
from components.components import promptFunc, welcomeDialogue

# Verify Gemini API key
checkAPIKey()

# Initialise a session state variable to control the welcome dialogue display
if "dialogue_shown" not in st.session_state:
    st.session_state.dialogue_shown = False
# Show welcome dialogue only once
if not st.session_state.dialogue_shown:
    welcomeDialogue()
    st.session_state.dialogue_shown = True

# Page settings
st.set_page_config(page_title="LangGraph AI Agent", page_icon="👋", layout="centered")

# Page title
st.subheader("LangGraph AI Agent -- :red[Gemini]", text_alignment="center")
st.write(
    ":orange[Hi User] 👋, I can help with :green[flight booking], :green[weather forecasting], and many more. Where should we start?"
)


def main():
    # This now returns a dict {text, files, audio} or None
    user_input = promptFunc()

    if user_input:
        # Example: Extracting data to send to your LangGraph agent
        text_msg = user_input["text"]
        files = user_input["files"]
        audio = user_input["audio"]

        # --- PDF LOGIC (Your specific request) ---
        if files:
            for file in files:
                if file.type == "application/pdf":
                    st.toast(f"Processing PDF: {file.name}", icon=":material/cached:")
                    # TODO: Call your PDF extraction function here
                    # pdf_text = extract_text_from_pdf(file)
                    # text_msg += f"\n\nContext from PDF:\n{pdf_text}"

        # Send to agent (Agent logic from previous steps goes here)
        # response = app.invoke({"messages": [("user", text_msg)]})

        # Placeholder response
        with st.chat_message("assistant"):
            st.write(f"I received your message: '{text_msg}'")
            if files:
                st.write(f"I also received {len(files)} file(s).")
            if audio:
                st.write("I also received an audio clip.")


if __name__ == "__main__":
    main()
