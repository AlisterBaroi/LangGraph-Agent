import streamlit as st
from utils.utils import display_pdf


def promptFunc():
    # prompt = st.chat_input("Say something")

    # if prompt:
    #     st.write(f"User has sent the following prompt: {prompt}")

    prompt = st.chat_input(
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

        # 2. Display the user's inputs immediately in the chat UI
        with st.chat_message("user"):

            # Display text if present
            if prompt.text:
                st.write(prompt.text)

            # Display audio if present
            if prompt.audio:
                st.audio(prompt.audio)
                st.caption("🎤 Audio recorded")

            # Display files if present
            if prompt.files:
                for file in prompt.files:
                    file_type = file.type
                    # Image logic
                    if file_type.startswith("image/"):
                        st.image(file, caption=file.name, width=300)
                    # PDF logic
                    elif file_type == "application/pdf":
                        st.write(f"***:green[{file.name}]***")
                        display_pdf(file)

        # 3. Return the payload so app.py can pass it to the agent
        return user_message

    return None
