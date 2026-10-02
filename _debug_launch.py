"""
PocketSmart AI — Self-running debug + launch helper
Run this from project root: python _debug_launch.py
"""
import subprocess
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

print("=" * 60)
print("  PocketSmart AI — Debug Launch Helper")
print(f"  Working dir: {PROJECT_ROOT}")
print("=" * 60)

# 1. Python version
print(f"\n[1] Python: {sys.version}")

# 2. Check .env
env_path = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(env_path):
    print("[2] .env file: FOUND")
else:
    print("[2] .env file: MISSING — create it from .env.example")

# 3. Try importing required packages
packages = [
    "fastapi", "uvicorn", "pydantic", "pydantic_settings",
    "jinja2", "passlib", "jose", "google.generativeai",
    "multipart", "dotenv"
]

print("\n[3] Checking imports:")
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f"    ✓ {pkg}")
    except ImportError as e:
        print(f"    ✗ {pkg} — MISSING: {e}")
        missing.append(pkg)

if missing:
    print(f"\n[!] Missing packages detected. Installing from requirements.txt...")
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req_path],
        capture_output=True, text=True
    )
    print(result.stdout[-2000:] if result.stdout else "")
    if result.returncode != 0:
        print("PIP ERRORS:", result.stderr[-1000:])
else:
    print("\n[3] All packages available!")

# 4. Try importing the app
print("\n[4] Testing app import:")
try:
    sys.path.insert(0, PROJECT_ROOT)
    from app.main import app
    print("    ✓ app.main imported successfully")
except Exception as e:
    print(f"    ✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Test config
print("\n[5] Testing configuration:")
try:
    from app.config import get_settings
    s = get_settings()
    print(f"    App name: {s.app_name}")
    print(f"    Gemini model: {s.gemini_model}")
    print(f"    Gemini configured: {s.gemini_configured}")
    print(f"    Token expire: {s.access_token_expire_minutes} min")
except Exception as e:
    print(f"    ✗ Config error: {e}")

# 6. Start server
print("\n[6] Starting server on http://localhost:8000 ...")
print("    Press Ctrl+C to stop.\n")
import uvicorn
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info"
)
