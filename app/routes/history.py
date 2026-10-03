"""
PocketSmart AI — Recommendation History Routes
"""
import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import decode_token, get_token_from_request
from app.models.recommendation import get_user_history, get_history_entry

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_user_context(request: Request) -> dict:
    token = get_token_from_request(request)
    if not token:
        return {"user": None, "authenticated": False}
    payload = decode_token(token)
    if not payload:
        return {"user": None, "authenticated": False}
    return {
        "user": {"id": payload.get("sub"), "name": payload.get("name"), "email": payload.get("email")},
        "authenticated": True,
    }


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return RedirectResponse(url="/login", status_code=302)

    user_id = ctx["user"]["id"]
    history = get_user_history(user_id)

    return templates.TemplateResponse("history.html", {
        "request": request,
        **ctx,
        "history": history,
    })


@router.get("/history/{entry_id}")
async def get_history_entry_detail(entry_id: str, request: Request):
    """Return a specific history entry as JSON — only for the owning user."""
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    user_id = ctx["user"]["id"]
    entry = get_history_entry(entry_id, user_id)

    if not entry:
        return JSONResponse({"error": "History entry not found"}, status_code=404)

    return JSONResponse(entry.model_dump(mode='json'))
