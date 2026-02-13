import streamlit as st
from utils.utils import display_pdf


@st.dialog(" ", width="small")
def welcomeDialogue():
    st.header("LangGraph AI Agent -- :red[Gemini]", text_alignment="center")
    st.write(f"Why is your favorite?")


# User prompt input with file uploads (image/PDF) & audio recordings
def promptFunc():
    prompt = st.chat_input(  # init prompt UI
        "Say something and/or attach an image/pdf file or audio recording",
        accept_file="multiple",
        file_type=["jpg", "jpeg", "png", "pdf"],
        accept_audio=True,
    )
    if prompt:
        # 1. Prepare the payload to return to your agent
        user_message = {
            "text": prompt.text,
            "files": prompt.files,  # List of UploadedFile objects
            "audio": prompt.audio,  # Single UploadedFile object or None
        }
        # 2. Display user inputs immediately in chat UI
        with st.chat_message("user"):
            if prompt.text:  # Display text if present
                st.write(prompt.text)
            if prompt.audio:  # Display audio if present
                st.audio(prompt.audio)
                st.caption("🎤 Audio recorded")
            if prompt.files:  # Display files if present
                for file in prompt.files:
                    file_type = file.type
                    if file_type.startswith("image/"):  # Image logic
                        st.image(file, caption=file.name, width=300)
                    elif file_type == "application/pdf":  # PDF logic
                        st.write(f"📄 ***:green[{file.name}]***")
                        display_pdf(file)
        # 3. Return payload so app.py can pass it to agent
        return user_message
    return None
