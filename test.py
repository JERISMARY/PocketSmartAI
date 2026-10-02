import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API key not found")
    exit()

print("✅ API key found")

try:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Say hello"
    )

    print("✅ Gemini API working")
    print(response.text)

except Exception as e:
    print("❌ Gemini API failed")
    print(type(e).__name__)
    print(e)