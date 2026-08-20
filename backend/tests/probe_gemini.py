import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    for m in client.models.list():
        print(m.name)
except Exception as e:
    print(f"List error: {e}")

try:
    res = client.models.generate_content(model="gemini-3.6-flash", contents="hello")
    print(f"gemini-3.6-flash worked: {res.text.strip()}")
except Exception as e:
    print(f"gemini-3.6-flash failed: {e}")
