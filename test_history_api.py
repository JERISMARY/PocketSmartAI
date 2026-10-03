import sys
import httpx

def test_flow():
    with httpx.Client(base_url="http://localhost:8000") as client:
        # Register
        resp = client.post("/register", data={
            "name": "Test User",
            "email": "test12345@example.com",
            "password": "password123",
            "confirm_password": "password123"
        })
        print("Register Status:", resp.status_code)
        
        # Create a jewelry plan
        resp = client.post("/jewelry-planner", data={
            "outfit_description": "Blue dress",
            "budget": "1000",
            "occasions": ["casual"],
            "preferences": ["necklace"]
        })
        print("Jewelry Plan Status:", resp.status_code)
        
        # Get history page to get an entry ID
        resp = client.get("/history")
        print("History Page Status:", resp.status_code)
        
        # Find entry ID in HTML
        html = resp.text
        import re
        match = re.search(r"viewHistoryEntry\('([^']+)'\)", html)
        if not match:
            print("No history entry found in HTML!")
            return
            
        entry_id = match.group(1)
        print("Found Entry ID:", entry_id)
        
        # Call the endpoint
        resp = client.get(f"/history/{entry_id}")
        print("History Detail API Status:", resp.status_code)
        print("History Detail API Response:", resp.text)

if __name__ == "__main__":
    test_flow()
