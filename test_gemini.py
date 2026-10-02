"""
PocketSmart AI — Gemini API Key Diagnostic
Run this from the project root: python test_gemini.py
"""
import os
from pathlib import Path

# Load .env manually
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

api_key = os.environ.get("GEMINI_API_KEY", "NOT SET")
model   = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

print("=" * 60)
print("  PocketSmart AI — Gemini Diagnostic")
print("=" * 60)
print(f"  Model:   {model}")
print(f"  Key set: {'YES' if api_key != 'NOT SET' else 'NO'}")

# Check key format
if api_key.startswith("AQ."):
    print("  Key fmt: ✅ Looks like a valid Google AI Studio key")
elif api_key.startswith("AQsf."):
    print("  Key fmt: ❌ INVALID — starts with 'AQ.' — this is NOT a Gemini API key")
    print()
    print("  >>> FIX: Go to https://aistudio.google.com/apikey")
    print("           Click 'Get API Key' → Copy the key (starts with 'AIza')")
    print("           Paste it into .env as: GEMINI_API_KEY=AIzaXXXXXXXX...")
    print("=" * 60)
    exit(1)
else:
    print(f"  Key fmt: ⚠️  Unknown format — first 8 chars: {api_key[:8]}...")

print()
print("  Testing connection to Gemini...")

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    gemini_client = genai.GenerativeModel(model)
    response = gemini_client.generate_content('Say exactly: {"test": "ok"}')
    print(f"  ✅ SUCCESS! Gemini responded: {response.text[:80]}")
except Exception as e:
    err = str(e)
    print(f"  ❌ FAILED: {err}")
    print()
    if "404" in err or "not found" in err.lower():
        print("  >>> FIX: Model not found. Check GEMINI_MODEL in .env")
        print(f"          Try: GEMINI_MODEL=gemini-1.5-flash")
    elif "403" in err or "invalid" in err.lower() or "api key" in err.lower():
        print("  >>> FIX: Invalid API key.")
        print("          Go to: https://aistudio.google.com/apikey")
        print("          Get a new key and paste it into .env")
    elif "429" in err or "quota" in err.lower():
        print("  >>> FIX: Quota exceeded. Wait a minute and try again.")

print("=" * 60)
