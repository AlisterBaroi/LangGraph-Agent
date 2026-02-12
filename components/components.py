import streamlit as st


def promptFunc():
    # prompt = st.chat_input("Say something")

    # if prompt:
    #     st.write(f"User has sent the following prompt: {prompt}")

    prompt = st.chat_input(
        "Say something and/or attach an image/pdf file or audio recording",
        accept_file=True,
        file_type=["jpg", "jpeg", "png", "pdf"],
        accept_audio=True,
    )
    # # Text input
    # if prompt and prompt.text:
    #     st.write(":orange[User:]", prompt.text)

    # # Audio input
    # if prompt and prompt.audio:
    #     st.audio(prompt.audio)
    #     st.write("Audio file:", prompt.audio.name)

    # # Image/PDF input
    # # if prompt and prompt["files"].type == "application/pdf":
    # #     st.write(prompt["files"].name)

    # if prompt and prompt["files"]:
    #     st.image(prompt["files"][0])
    if prompt:
        # 1. Prepare the payload to return to your agent
        user_message = {
            "text": prompt.text,
            "files": prompt.files,  # This is a list of UploadedFile objects
            "audio": prompt.audio,  # This is a single UploadedFile object or None
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
                        st.markdown(f"### 📑 PDF Attached: `{file.name}`")

        # 3. Return the payload so app.py can pass it to the agent
        return user_message

    return None
