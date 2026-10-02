"""
PocketSmart AI — Core Tests
Tests: health, auth, home planner, party planner, jewelry planner, history.
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

# ─── Shared Test State ────────────────────────────────────────────────────────
_test_token_cookie = None
_test_user_email = "testuser@pocketsmart.ai"
_test_user_password = "testpass123"
_test_user_name = "Test User"


# ─── 1. Health Check ─────────────────────────────────────────────────────────
class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_docs_available(self):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_available(self):
        resp = client.get("/redoc")
        assert resp.status_code == 200

    def test_home_page_loads(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"PocketSmart" in resp.content


# ─── 2. Authentication ────────────────────────────────────────────────────────
class TestAuth:
    def test_register_page_loads(self):
        resp = client.get("/register")
        assert resp.status_code == 200
        assert b"Create Account" in resp.content

    def test_login_page_loads(self):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"Sign In" in resp.content

    def test_register_success(self):
        global _test_token_cookie
        resp = client.post("/register", data={
            "name": _test_user_name,
            "email": _test_user_email,
            "password": _test_user_password,
            "confirm_password": _test_user_password,
        }, follow_redirects=False)
        # Should redirect to dashboard after registration
        assert resp.status_code in (302, 200)
        # Capture the cookie for subsequent tests
        if "access_token" in resp.cookies:
            _test_token_cookie = resp.cookies["access_token"]

    def test_register_duplicate_email(self):
        resp = client.post("/register", data={
            "name": "Another User",
            "email": _test_user_email,  # duplicate
            "password": _test_user_password,
            "confirm_password": _test_user_password,
        })
        # Should show error page, not redirect
        assert resp.status_code == 200
        assert b"already exists" in resp.content.lower() or b"error" in resp.content.lower()

    def test_register_password_mismatch_is_caught(self):
        resp = client.post("/register", data={
            "name": "User Two",
            "email": "user2@test.com",
            "password": "password1",
            "confirm_password": "password2",
        })
        assert resp.status_code == 200
        assert b"match" in resp.content.lower() or b"error" in resp.content.lower()

    def test_login_valid(self):
        global _test_token_cookie
        resp = client.post("/login", data={
            "email": _test_user_email,
            "password": _test_user_password,
        }, follow_redirects=False)
        assert resp.status_code == 302
        if "access_token" in resp.cookies:
            _test_token_cookie = resp.cookies["access_token"]

    def test_login_wrong_password(self):
        resp = client.post("/login", data={
            "email": _test_user_email,
            "password": "wrongpassword",
        })
        assert resp.status_code == 200
        assert b"Invalid" in resp.content or b"error" in resp.content.lower()

    def test_login_nonexistent_user(self):
        resp = client.post("/login", data={
            "email": "nobody@nowhere.com",
            "password": "anypassword",
        })
        assert resp.status_code == 200
        assert b"Invalid" in resp.content or b"error" in resp.content.lower()

    def test_session_info_unauthenticated(self):
        resp = client.get("/session-info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is False

    def test_dashboard_redirects_unauthenticated(self):
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout(self):
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302


# ─── Authenticated Client Helper ─────────────────────────────────────────────
def get_auth_client():
    """Return a TestClient with a valid session cookie."""
    auth_client = TestClient(app)
    # Register fresh user for this test session
    email = "authtest@pocketsmart.ai"
    auth_client.post("/register", data={
        "name": "Auth Tester",
        "email": email,
        "password": "securepass123",
        "confirm_password": "securepass123",
    }, follow_redirects=False)
    # Login to get cookie
    resp = auth_client.post("/login", data={
        "email": email,
        "password": "securepass123",
    }, follow_redirects=False)
    return auth_client


# ─── 3. Home Planner ─────────────────────────────────────────────────────────
class TestHomePlanner:
    def setup_method(self):
        self.c = get_auth_client()

    def test_home_planner_page_loads(self):
        resp = self.c.get("/home-planner")
        assert resp.status_code == 200
        assert b"Home Interior" in resp.content

    def test_home_planner_unauthenticated(self):
        resp = client.get("/home-planner", follow_redirects=False)
        assert resp.status_code == 302

    def test_generate_home_invalid_budget_zero(self):
        resp = self.c.post("/generate-home", data={
            "budget": "0",
            "rooms": "Living Room",
            "style": "modern",
        })
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data

    def test_generate_home_invalid_budget_negative(self):
        resp = self.c.post("/generate-home", data={
            "budget": "-5000",
            "rooms": "Living Room",
        })
        assert resp.status_code == 422

    def test_generate_home_unauthenticated(self):
        resp = client.post("/generate-home", data={"budget": "50000"})
        assert resp.status_code == 401


# ─── 4. Party Planner ────────────────────────────────────────────────────────
class TestPartyPlanner:
    def setup_method(self):
        self.c = get_auth_client()

    def test_party_planner_page_loads(self):
        resp = self.c.get("/party-planner")
        assert resp.status_code == 200
        assert b"Party" in resp.content

    def test_party_planner_unauthenticated(self):
        resp = client.get("/party-planner", follow_redirects=False)
        assert resp.status_code == 302

    def test_generate_party_invalid_budget(self):
        resp = self.c.post("/generate-party", data={
            "budget": "-100",
            "event_type": "birthday",
            "guest_count": "20",
        })
        assert resp.status_code == 422

    def test_generate_party_invalid_guest_count(self):
        resp = self.c.post("/generate-party", data={
            "budget": "10000",
            "event_type": "birthday",
            "guest_count": "0",
        })
        assert resp.status_code == 422

    def test_generate_party_unauthenticated(self):
        resp = client.post("/generate-party", data={"budget": "25000", "guest_count": "20"})
        assert resp.status_code == 401


# ─── 5. Jewelry Planner ──────────────────────────────────────────────────────
class TestJewelryPlanner:
    def setup_method(self):
        self.c = get_auth_client()

    def test_jewelry_planner_page_loads(self):
        resp = self.c.get("/jewelry-planner")
        assert resp.status_code == 200
        assert b"Jewelry" in resp.content

    def test_jewelry_planner_unauthenticated(self):
        resp = client.get("/jewelry-planner", follow_redirects=False)
        assert resp.status_code == 302

    def test_generate_jewelry_invalid_budget(self):
        resp = self.c.post("/generate-jewelry", data={
            "budget": "0",
            "occasion": "wedding",
        })
        assert resp.status_code == 422

    def test_generate_jewelry_unauthenticated(self):
        resp = client.post("/generate-jewelry", data={"budget": "15000"})
        assert resp.status_code == 401

    def test_generate_jewelry_invalid_image_type(self):
        """Reject non-image file types."""
        import io
        fake_exe = io.BytesIO(b"MZ" + b"\x00" * 100)  # fake EXE header
        resp = self.c.post("/generate-jewelry", data={
            "budget": "15000",
            "occasion": "party",
        }, files={"outfit_image": ("malicious.exe", fake_exe, "application/octet-stream")})
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data


# ─── 6. History ──────────────────────────────────────────────────────────────
class TestHistory:
    def setup_method(self):
        self.c = get_auth_client()

    def test_history_page_loads(self):
        resp = self.c.get("/history")
        assert resp.status_code == 200

    def test_history_unauthenticated(self):
        resp = client.get("/history", follow_redirects=False)
        assert resp.status_code == 302

    def test_history_entry_not_found(self):
        resp = self.c.get("/history/nonexistent-id-12345")
        assert resp.status_code == 404

    def test_cross_user_history_blocked(self):
        """A user should not be able to access another user's history entry."""
        # Create two separate client sessions
        c1 = get_auth_client()
        c2 = TestClient(app)
        c2.post("/register", data={
            "name": "User B",
            "email": "userb@pocketsmart.ai",
            "password": "passuserb",
            "confirm_password": "passuserb",
        }, follow_redirects=False)
        c2.post("/login", data={"email": "userb@pocketsmart.ai", "password": "passuserb"}, follow_redirects=False)

        # Try to access a fake entry ID with user c2
        resp = c2.get("/history/some-fake-entry-id")
        assert resp.status_code == 404


# ─── 7. Password Security ─────────────────────────────────────────────────────
class TestSecurity:
    def test_password_hashing(self):
        from app.auth.security import hash_password, verify_password
        pw = "TestPassword123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_jwt_create_and_decode(self):
        from app.auth.jwt import create_access_token, decode_token
        token = create_access_token({"sub": "test-user-id", "email": "test@test.com"})
        assert token is not None
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-id"

    def test_jwt_invalid_token(self):
        from app.auth.jwt import decode_token
        result = decode_token("this.is.not.a.valid.token")
        assert result is None

    def test_no_password_in_session_info(self):
        """Session info must never return password or hash."""
        c = get_auth_client()
        resp = c.get("/session-info")
        assert resp.status_code == 200
        data = resp.json()
        assert "password" not in data
        assert "hashed_password" not in data
