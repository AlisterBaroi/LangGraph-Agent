import os, base64
import streamlit as st
from dotenv import load_dotenv


# Check Gemini API Key & cache it (streamlit version)
@st.cache_data
def checkAPIKey(streamlit: bool) -> str:
    load_dotenv()  # Load variables from .env

    if not os.environ.get("GOOGLE_API_KEY"):  # Check if API key exists
        excG = "GOOGLE_API_KEY Missing -> Please add GOOGLE_API_KEY for Gemini at './.env' file."
        print(excG)
        return st.write(Exception(excG)) if streamlit else exit()
    print("GOOGLE_API_KEY: Verified!")

    if not os.environ.get("MODEL_NAME"):  # Check if Model is set
        excM = (
            "MODEL_NAME Missing -> Please specify Gemini MODEL_NAME at './.env' file."
        )
        print(excM)
        return st.write(Exception(excM)) if streamlit else exit()
    print("GEMINI MODEL: Set!")


# Display a PDF in an HTML iframe.
def display_pdf(file):
    bytes_data = file.getvalue()  # Read the file as bytes
    # Encode bytes to base64 so it can be embedded in HTML
    base64_pdf = base64.b64encode(bytes_data).decode("utf-8")
    # Create the HTML iframe (width/height control the viewer size)
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)  # Render the HTML
