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
    # Text input
    if prompt and prompt.text:
        st.write(":orange[User:]", prompt.text)

    # Audio input
    if prompt and prompt.audio:
        st.audio(prompt.audio)
        st.write("Audio file:", prompt.audio.name)

    # Image/PDF input
    # if prompt and prompt["files"].type == "application/pdf":
    #     st.write(prompt["files"].name)

    if prompt and prompt["files"]:
        st.image(prompt["files"][0])
