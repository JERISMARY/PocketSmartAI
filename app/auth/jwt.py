"""
PocketSmart AI — JWT Utilities
Create, decode, and validate JWT access tokens.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from jose import JWTError, jwt
from fastapi import Request, HTTPException, status

from app.config import get_settings

logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT with an expiry."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT. Returns payload or None."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode error: {e}")
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT from cookie or Authorization header."""
    # 1. Try HTTP-only cookie first
    token = request.cookies.get("access_token")
    if token:
        return token
    # 2. Fall back to Bearer token in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def get_current_user_id(request: Request) -> Optional[str]:
    """Return user_id from JWT, or None if unauthenticated."""
    token = get_token_from_request(request)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub")


def require_auth(request: Request) -> str:
    """Dependency: require authenticated user. Returns user_id."""
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id
