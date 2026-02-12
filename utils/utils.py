import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader


# Check Gemini API Key & cache it
@st.cache_data
def checkAPIKey() -> str:
    load_dotenv()  # Load variables from .env
    if not os.environ.get("GOOGLE_API_KEY"):  # Check if API key exists
        exc = "GOOGLE_API_KEY Missing -> Please add GOOGLE_API_KEY for Gemini at './.env' file."
        print(exc)
        return st.write(Exception(exc))
    print("GOOGLE_API_KEY verified!")


# Extract Text from PDF
def extract_text_from_pdf(file) -> str:
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"
