"""
PocketSmart AI — User Models
In-memory user store for demo. Replace with a real database in production.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import uuid


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


# ─── In-Memory User Store ────────────────────────────────────────────────────
# Keyed by email (lowercase). Replace with SQLite/PostgreSQL for production.
_users_db: dict[str, UserInDB] = {}

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
    return user

def user_exists(email: str) -> bool:
    return email.lower() in _users_db
