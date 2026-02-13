import os
from dotenv import load_dotenv
from google import genai

# 1. Load API Key
load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file.")
    exit()

# 2. Initialize Client
try:
    client = genai.Client(api_key=api_key)
    print(f"--- 📡 Listing All Available Models ---")

    # 3. Simple List (No attribute filtering to avoid errors)
    pager = client.models.list()

    for model in pager:
        # Just print the name, which is always present
        print(f"✅ Found: {model.name}")

except Exception as e:
    print(f"❌ Error: {e}")
