import streamlit as st
import base64


@st.dialog(" ", width="small")
def welcomeDialogue():
    st.header("LangGraph AI Agent -- :red[Gemini]", text_alignment="center")
    st.write(f"Why is your favorite?")


# Helper function to display a PDF in Streamlit using an iframe.
def display_pdf(file):
    # 1. Read the file as bytes
    bytes_data = file.getvalue()

    # 2. Encode bytes to base64 so it can be embedded in HTML
    base64_pdf = base64.b64encode(bytes_data).decode("utf-8")

    # 3. Create the HTML iframe (width/height control the viewer size)
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'

    # 4. Render the HTML
    st.markdown(pdf_display, unsafe_allow_html=True)


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
                        st.write(f"***:green[{file.name}]***")
                        # st.markdown(f"### `{file.name}`")
                        # Display uploaded pdf file
                        display_pdf(file)

        # 3. Return the payload so app.py can pass it to the agent
        return user_message

    return None
