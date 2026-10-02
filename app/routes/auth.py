"""
PocketSmart AI — Authentication Routes
Handles register, login, logout via HTML forms + JWT cookies.
"""
import logging
from datetime import timedelta
from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.security import hash_password, verify_password
from app.auth.jwt import create_access_token, get_current_user_id
from app.models.user import (
    UserCreate, get_user_by_email, create_user, user_exists
)
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    error = None
    try:
        email = email.strip().lower()
        user = get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            error = "Invalid email or password."
        else:
            settings = get_settings()
            token = create_access_token(
                {"sub": user.id, "email": user.email, "name": user.name},
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
            )
            resp = RedirectResponse(url="/dashboard", status_code=302)
            resp.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                max_age=settings.access_token_expire_minutes * 60,
                samesite="lax",
            )
            logger.info(f"User logged in: {user.email}")
            return resp
    except Exception as e:
        logger.error(f"Login error: {e}")
        error = "An unexpected error occurred. Please try again."

    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    error = None
    try:
        email = email.strip().lower()
        name = name.strip()

        # Validate
        if not name or len(name) < 2:
            error = "Name must be at least 2 characters."
        elif "@" not in email:
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif user_exists(email):
            error = "An account with this email already exists."
        else:
            hashed = hash_password(password)
            user = create_user(name=name, email=email, hashed_password=hashed)
            logger.info(f"New user registered: {user.email}")

            settings = get_settings()
            token = create_access_token(
                {"sub": user.id, "email": user.email, "name": user.name},
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
            )
            resp = RedirectResponse(url="/dashboard", status_code=302)
            resp.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                max_age=settings.access_token_expire_minutes * 60,
                samesite="lax",
            )
            return resp
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        error = "An unexpected error occurred. Please try again."

    return templates.TemplateResponse("register.html", {"request": request, "error": error})


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("access_token")
    return resp


@router.get("/session-info")
async def session_info(request: Request):
    """Return safe session data (no password, no secrets)."""
    from app.models.user import get_user_by_email
    from app.auth.jwt import decode_token, get_token_from_request

    token = get_token_from_request(request)
    if not token:
        return {"authenticated": False}

    payload = decode_token(token)
    if not payload:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user_id": payload.get("sub"),
        "name": payload.get("name"),
        "email": payload.get("email"),
    }
