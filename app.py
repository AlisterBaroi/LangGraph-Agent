import streamlit as st
from utils.utils import checkAPIKey
from components.components import promptFunc

# Verify Gemini API key
checkAPIKey()

# Page settings
st.set_page_config(page_title="LangGraph AI Agent", page_icon="👋", layout="centered")

# Page title
st.header("LangGraph AI Agent -- :red[Gemini]", text_alignment="center")


def main():
    promptFunc()


if __name__ == "__main__":
    main()
