import os
from google import genai
from utils.utils import checkAPIKey

# Check for API Key
checkAPIKey(streamlit=False)

try:
    # Initialize Client
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    print(f"--- 📡 Listing All Available Models ---")
    # Simple List (No attribute filtering to avoid errors)
    pager = client.models.list()
    for model in pager:
        # Just print models, that are present
        print(f"✅ Found: {model.name}")

except Exception as e:
    print(f"Error: {e}")
