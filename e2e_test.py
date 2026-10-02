"""
End-to-End API Test Script for PocketSmart AI
Run this while the server is running on localhost:8000
"""
import urllib.request
import urllib.parse
import json
import http.cookiejar

# Setup a cookie jar to hold our JWT session
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

BASE_URL = "http://localhost:8000"

print("Starting E2E API Test...")

# 1. Register a test user
print("\n[1] Registering test user...")
register_data = urllib.parse.urlencode({
    "name": "E2E Tester",
    "email": "e2e@pocketsmart.ai",
    "password": "securepassword123",
    "confirm_password": "securepassword123"
}).encode("utf-8")

try:
    req = urllib.request.Request(f"{BASE_URL}/register", data=register_data)
    resp = urllib.request.urlopen(req)
    print(f"Register status: {resp.status}")
except Exception as e:
    print(f"Register error: {e}")

# 2. Login to get the session cookie
print("\n[2] Logging in...")
login_data = urllib.parse.urlencode({
    "email": "e2e@pocketsmart.ai",
    "password": "securepassword123"
}).encode("utf-8")

try:
    req = urllib.request.Request(f"{BASE_URL}/login", data=login_data)
    resp = urllib.request.urlopen(req)
    print(f"Login status: {resp.status}")
    print(f"Cookies captured: {len(cookie_jar)}")
except Exception as e:
    print(f"Login error: {e}")

# 3. Test Gemini API via Home Planner
print("\n[3] Triggering Gemini Integration (Home Planner)...")
# Send the data exactly as a form submission, which is what the frontend does
form_boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
form_data = (
    f"--{form_boundary}\r\n"
    f"Content-Disposition: form-data; name=\"budget\"\r\n\r\n"
    f"50000\r\n"
    f"--{form_boundary}\r\n"
    f"Content-Disposition: form-data; name=\"home_type\"\r\n\r\n"
    f"Apartment\r\n"
    f"--{form_boundary}\r\n"
    f"Content-Disposition: form-data; name=\"rooms\"\r\n\r\n"
    f"Living Room\r\n"
    f"--{form_boundary}\r\n"
    f"Content-Disposition: form-data; name=\"style\"\r\n\r\n"
    f"modern\r\n"
    f"--{form_boundary}--"
).encode('utf-8')

req = urllib.request.Request(f"{BASE_URL}/generate-home", data=form_data)
req.add_header('Content-Type', f'multipart/form-data; boundary={form_boundary}')

try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    print(f"Status Code: {resp.status}")
    print("Response JSON Keys:", list(data.keys()))
    if "error" in data:
        print(f"GEMINI ERROR: {data['error']}")
    else:
        print("GEMINI SUCCESS! Budget summary:")
        print(json.dumps(data.get("budget_summary"), indent=2))
        print(f"Recommendations count: {len(data.get('recommendations', []))}")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f"HTTP ERROR: {e.code}")
    print(f"Response: {err_body}")
except Exception as e:
    print(f"Request failed: {e}")
