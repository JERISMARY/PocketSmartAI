"""
PocketSmart AI — Home Page & Dashboard Routes
"""
import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import get_current_user_id
from app.models.user import get_user_by_email
from app.models.recommendation import get_user_history
from app.auth.jwt import decode_token, get_token_from_request

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_user_context(request: Request) -> dict:
    """Extract user info from JWT for template context."""
    token = get_token_from_request(request)
    if not token:
        return {"user": None, "authenticated": False}
    payload = decode_token(token)
    if not payload:
        return {"user": None, "authenticated": False}
    return {
        "user": {
            "id": payload.get("sub"),
            "name": payload.get("name"),
            "email": payload.get("email"),
        },
        "authenticated": True,
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("index.html", {"request": request, **ctx})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return RedirectResponse(url="/login", status_code=302)

    user_id = ctx["user"]["id"]
    history = get_user_history(user_id)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        **ctx,
        "history": history[:5],  # recent 5
        "total_plans": len(history),
    })


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/api/gemini-status")
async def gemini_status(request: Request):
    """Development endpoint — tests Gemini connectivity without exposing secrets."""
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return {"error": "Authentication required"}

    from app.services.gemini_utils import test_gemini_connection
    result = test_gemini_connection()
    return result
