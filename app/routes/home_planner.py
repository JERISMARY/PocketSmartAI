"""
PocketSmart AI — Home Interior Planner Routes
"""
import logging
import json
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import get_current_user_id, decode_token, get_token_from_request
from app.models.planner import HomePlannerInput
from app.services.recommendation_service import process_home_planner
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


@router.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("home_planner.html", {"request": request, **ctx})


@router.post("/generate-home")
async def generate_home(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        form = await request.form()

        # Parse rooms (checkboxes — multiple values)
        rooms = form.getlist("rooms")
        if not rooms:
            rooms = ["Living Room"]

        data = {
            "budget": float(form.get("budget", 0)),
            "home_type": str(form.get("home_type", "Apartment")),
            "rooms": rooms,
            "style": str(form.get("style", "modern")),
            "num_lights": int(form.get("num_lights", 0) or 0),
            "num_fans": int(form.get("num_fans", 0) or 0),
            "num_tables": int(form.get("num_tables", 0) or 0),
            "num_chairs": int(form.get("num_chairs", 0) or 0),
            "need_curtains": form.get("need_curtains") == "on",
            "need_storage": form.get("need_storage") == "on",
            "need_wall_decor": form.get("need_wall_decor") == "on",
            "additional_preferences": str(form.get("additional_preferences", "") or ""),
        }

        # Pydantic validation
        validated = HomePlannerInput(**data)

        user_id = ctx["user"]["id"]
        result = process_home_planner(validated.model_dump(), user_id)

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
        logger.error(f"Home planner error: {e}", exc_info=True)
        return JSONResponse({"error": "An unexpected error occurred. Please try again."}, status_code=500)
