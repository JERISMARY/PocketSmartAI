"""
PocketSmart AI — User Models
In-memory user store for demo. Replace with a real database in production.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import uuid
import json
import os
from pathlib import Path


class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    """Schema for login."""
    email: str
    password: str


class UserOut(BaseModel):
    """Safe user data returned in responses (no password)."""
    id: str
    name: str
    email: str
    created_at: datetime


class UserInDB(BaseModel):
    """Internal user record including hashed password."""
    id: str
    name: str
    email: str
    hashed_password: str
    created_at: datetime


# ─── Persistent File Store ────────────────────────────────────────────────────
# Keyed by email (lowercase).
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"

_users_db: dict[str, UserInDB] = {}

def _load_users():
    global _users_db
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _users_db = {email: UserInDB(**user_data) for email, user_data in data.items()}
        except Exception as e:
            print(f"Error loading users: {e}")
            _users_db = {}

def _save_users():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({email: user.model_dump(mode='json') for email, user in _users_db.items()}, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

# Load initially
_load_users()

def get_user_by_email(email: str) -> Optional[UserInDB]:
    return _users_db.get(email.lower())

def create_user(name: str, email: str, hashed_password: str) -> UserInDB:
    user = UserInDB(
        id=str(uuid.uuid4()),
        name=name,
        email=email.lower(),
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
    )
    _users_db[email.lower()] = user
    _save_users()
    return user

def user_exists(email: str) -> bool:
    return email.lower() in _users_db
