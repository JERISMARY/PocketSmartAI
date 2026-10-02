"""
PocketSmart AI — Party Planner Routes
"""
import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import decode_token, get_token_from_request
from app.models.planner import PartyPlannerInput
from app.services.recommendation_service import process_party_planner
from app.services.gemini_utils import (
    GeminiNotConfiguredError, GeminiQuotaExceededError, GeminiAPIError
)

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


@router.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("party_planner.html", {"request": request, **ctx})


@router.post("/generate-party")
async def generate_party(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        form = await request.form()

        data = {
            "budget": float(form.get("budget", 0)),
            "event_type": str(form.get("event_type", "birthday")),
            "guest_count": int(form.get("guest_count", 20) or 20),
            "venue_type": str(form.get("venue_type", "home")),
            "location": str(form.get("location", "") or ""),
            "food_preference": str(form.get("food_preference", "veg")),
            "decoration_style": str(form.get("decoration_style", "simple")),
            "need_entertainment": form.get("need_entertainment") == "on",
            "need_accommodation": form.get("need_accommodation") == "on",
            "additional_preferences": str(form.get("additional_preferences", "") or ""),
        }

        validated = PartyPlannerInput(**data)
        user_id = ctx["user"]["id"]
        result = process_party_planner(validated.model_dump(), user_id)

        return JSONResponse(result.model_dump())

    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=422)
    except GeminiNotConfiguredError as e:
        return JSONResponse({"error": str(e)}, status_code=503)
    except GeminiQuotaExceededError as e:
        return JSONResponse({"error": str(e)}, status_code=429)
    except GeminiAPIError as e:
        return JSONResponse({"error": str(e)}, status_code=502)
    except Exception as e:
        logger.error(f"Party planner error: {e}", exc_info=True)
        return JSONResponse({"error": "An unexpected error occurred. Please try again."}, status_code=500)
