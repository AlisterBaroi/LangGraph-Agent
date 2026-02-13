import os
from dotenv import load_dotenv
from google import genai
from utils.utils import checkAPIKey

# Check for API Key
checkAPIKey(streamlit=False)

# 2. Initialize Client
try:
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    print(f"--- 📡 Listing All Available Models ---")

    # 3. Simple List (No attribute filtering to avoid errors)
    pager = client.models.list()

    for model in pager:
        # Just print the name, which is always present
        print(f"✅ Found: {model.name}")

except Exception as e:
    print(f"Error: {e}")
