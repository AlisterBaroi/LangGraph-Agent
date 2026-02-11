import os
import streamlit as st
from dotenv import load_dotenv


# Check Gemini API Key & cache it
@st.cache_data
def checkAPIKey() -> str:
    load_dotenv()  # Load variables from .env
    if not os.environ.get("GOOGLE_API_KEY"):  # Check if API key exists
        exc = "GOOGLE_API_KEY Missing -> Please add GOOGLE_API_KEY for Gemini at './.env' file."
        print(exc)
        return st.write(Exception(exc))
    print("GOOGLE_API_KEY verified!")
