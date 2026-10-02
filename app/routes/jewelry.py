"""
PocketSmart AI — Jewelry Planner Routes
Supports optional multipart image upload for outfit analysis.
"""
import logging
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.auth.jwt import decode_token, get_token_from_request
from app.models.planner import JewelryPlannerInput
from app.services.recommendation_service import process_jewelry_planner, validate_image
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


@router.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("jewelry_planner.html", {"request": request, **ctx})


@router.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    outfit_image: Optional[UploadFile] = File(None),
):
    ctx = _get_user_context(request)
    if not ctx["authenticated"]:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        form = await request.form()

        # Parse jewelry_types (multi-select checkboxes)
        jewelry_types = form.getlist("jewelry_types")
        if not jewelry_types:
            jewelry_types = ["necklace"]

        data = {
            "budget": float(form.get("budget", 0)),
            "occasion": str(form.get("occasion", "casual")),
            "jewelry_types": jewelry_types,
            "preferred_style": str(form.get("preferred_style", "contemporary")),
            "preferred_metal": str(form.get("preferred_metal", "gold")),
            "outfit_description": str(form.get("outfit_description", "") or ""),
            "additional_preferences": str(form.get("additional_preferences", "") or ""),
        }

        validated = JewelryPlannerInput(**data)

        # Handle optional image
        image_bytes = None
        image_mime = None
        if outfit_image and outfit_image.filename:
            content_type = outfit_image.content_type or "application/octet-stream"
            img_data = await outfit_image.read()

            err = validate_image(content_type, len(img_data))
            if err:
                return JSONResponse({"error": err}, status_code=422)

            image_bytes = img_data
            image_mime = content_type
            logger.info(f"Image uploaded: {outfit_image.filename} ({len(img_data)} bytes)")

        user_id = ctx["user"]["id"]
        result = process_jewelry_planner(
            validated.model_dump(),
            user_id,
            image_bytes=image_bytes,
            image_mime=image_mime,
        )

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
        logger.error(f"Jewelry planner error: {e}", exc_info=True)
        return JSONResponse({"error": "An unexpected error occurred. Please try again."}, status_code=500)
