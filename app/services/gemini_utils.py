"""
PocketSmart AI — Centralized Gemini Service
Uses the NEW google-genai SDK (from google import genai).

Key design rules:
- One client instance (lazy singleton)
- Quota-aware error handling
- Never expose API key
- Structured JSON output with fallback
- Multimodal support for jewelry planner
"""
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Lazy Gemini Client ───────────────────────────────────────────────────────
_gemini_client = None
_gemini_model_name = None


def _get_client():
    """Lazy-initialize Gemini client once using the new google-genai SDK."""
    global _gemini_client, _gemini_model_name
    if _gemini_client is None:
        from app.config import get_settings
        from google import genai

        settings = get_settings()
        if not settings.gemini_configured:
            raise GeminiNotConfiguredError("GEMINI_API_KEY is not set in .env")

        key = settings.gemini_api_key
        _gemini_client = genai.Client(api_key=key)
        _gemini_model_name = settings.gemini_model
        logger.info(f"Gemini client initialized with model: {_gemini_model_name}")

    return _gemini_client, _gemini_model_name


# ─── Custom Exceptions ────────────────────────────────────────────────────────
class GeminiNotConfiguredError(Exception):
    """Raised when the API key is missing or placeholder."""
    pass


class GeminiQuotaExceededError(Exception):
    """Raised when API quota is exhausted (HTTP 429)."""
    pass


class GeminiAPIError(Exception):
    """Generic Gemini API error."""
    pass


# ─── JSON Extraction ──────────────────────────────────────────────────────────
def _extract_json(text: str) -> Optional[dict]:
    """
    Try to extract the first JSON object from text.
    Handles markdown code blocks and raw JSON.
    """
    if not text:
        return None

    # 1. Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip()

    # 2. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Try to find JSON object within the text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning(f"Could not extract valid JSON from Gemini response. Raw text (first 500 chars): {text[:500]}")
    return None


# ─── Safe API Call ────────────────────────────────────────────────────────────
def _call_gemini(prompt: str, image_bytes: Optional[bytes] = None,
                 image_mime: Optional[str] = None) -> str:
    """
    Make a single Gemini API call with proper error handling.
    Uses the new google-genai SDK: client.models.generate_content(...)
    """
    client, model_name = _get_client()

    try:
        if image_bytes and image_mime:
            # Multimodal call with the new SDK
            from google.genai import types
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=image_mime)
            contents = [prompt, image_part]
            response = client.models.generate_content(model=model_name, contents=contents)
        else:
            response = client.models.generate_content(model=model_name, contents=prompt)

        if not response or not response.text:
            raise GeminiAPIError("Empty response received from Gemini API.")

        return response.text

    except (GeminiNotConfiguredError, GeminiQuotaExceededError, GeminiAPIError):
        raise  # Re-raise our own exceptions as-is

    except Exception as e:
        err_str = str(e).lower()

        # Quota / rate limit
        if any(k in err_str for k in ["429", "quota", "rate limit", "resource_exhausted"]):
            logger.error(f"Gemini quota exceeded: {e}")
            raise GeminiQuotaExceededError(
                "AI recommendations are temporarily unavailable because the Gemini API quota has been reached. Please try again later."
            )

        # Auth / key issues
        if any(k in err_str for k in ["401", "403", "invalid api key", "api_key", "permission", "unauthenticated"]):
            logger.error(f"Gemini auth error: {e}")
            raise GeminiAPIError("Gemini API key is invalid or missing permissions.")

        # Model not found
        if any(k in err_str for k in ["404", "model not found", "not_found", "models/"]):
            logger.error(f"Gemini model not found: {e}")
            raise GeminiAPIError(
                f"The Gemini model '{_gemini_model_name}' is not available. Check GEMINI_MODEL in .env."
            )

        logger.error(f"Gemini API error: {e}", exc_info=True)
        raise GeminiAPIError(f"Gemini API error: {str(e)}")


# ─── Prompt Templates ─────────────────────────────────────────────────────────
def _home_planner_prompt(data: dict) -> str:
    rooms = ", ".join(data.get("rooms", ["Living Room"]))
    items = []
    if data.get("num_lights", 0) > 0:
        items.append(f"{data['num_lights']} lights")
    if data.get("num_fans", 0) > 0:
        items.append(f"{data['num_fans']} fans")
    if data.get("num_tables", 0) > 0:
        items.append(f"{data['num_tables']} tables")
    if data.get("num_chairs", 0) > 0:
        items.append(f"{data['num_chairs']} chairs")
    if data.get("need_curtains"):
        items.append("curtains")
    if data.get("need_storage"):
        items.append("storage/shelving")
    if data.get("need_wall_decor"):
        items.append("wall decor")
    items_str = ", ".join(items) if items else "general furnishings"
    prefs = data.get("additional_preferences", "")

    return f"""You are a professional Indian interior budget planner. A user wants to furnish/decorate their home.

User Details:
- Home type: {data.get('home_type', 'Apartment')}
- Style preference: {data.get('style', 'modern')}
- Rooms to furnish: {rooms}
- Total budget: ₹{data.get('budget', 0):,.0f}
- Required items: {items_str}
- Additional preferences: {prefs if prefs else 'None'}

Your task:
1. Allocate the budget across categories (lighting, furniture, fans, decor, storage, etc.)
2. Recommend specific products with estimated prices from Amazon India, Flipkart, IKEA, or local markets
3. Keep total estimated cost WITHIN the user's budget
4. Prioritize essential items first
5. Provide a brief reason for each recommendation
6. Use realistic Indian market price estimates (label them as "Estimated Price")
7. If budget is tight, suggest affordable alternatives

IMPORTANT: Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
  "summary": "Brief 2-3 sentence overview of the plan",
  "budget_allocation": [
    {{"category": "Category Name", "allocated_budget": 5000}}
  ],
  "recommendations": [
    {{
      "name": "Product Name",
      "category": "Category",
      "estimated_price": 1499,
      "platform": "Amazon India",
      "reason": "Why this is recommended",
      "style": "Style description",
      "url": "",
      "quantity": 1
    }}
  ],
  "ai_notes": "Any important notes about the plan"
}}"""


def _party_planner_prompt(data: dict) -> str:
    extras = []
    if data.get("need_entertainment"):
        extras.append("entertainment/DJ")
    if data.get("need_accommodation"):
        extras.append("accommodation")
    extras_str = ", ".join(extras) if extras else "none required"

    return f"""You are a professional Indian event budget planner. A user wants to plan a party/event.

Event Details:
- Event type: {data.get('event_type', 'birthday')}
- Guest count: {data.get('guest_count', 20)} people
- Venue type: {data.get('venue_type', 'home')}
- Location: {data.get('location', 'India') or 'India'}
- Total budget: ₹{data.get('budget', 0):,.0f}
- Food preference: {data.get('food_preference', 'veg')}
- Decoration style: {data.get('decoration_style', 'simple')}
- Additional services: {extras_str}
- Additional preferences: {data.get('additional_preferences', 'None') or 'None'}

Your task:
1. Allocate budget across: food & catering, venue, decoration, entertainment, miscellaneous
2. Recommend specific vendors/services with estimated costs (Indian market rates)
3. Keep total within budget
4. Account for per-person costs where applicable
5. Suggest platforms: Swiggy Genie, Zomato Catering, OYO, local vendors
6. Label all prices as "Estimated Price" — do not claim live availability

IMPORTANT: Return ONLY a valid JSON object (no markdown):
{{
  "summary": "Brief overview of the event plan",
  "budget_allocation": [
    {{"category": "Food & Catering", "allocated_budget": 15000}}
  ],
  "recommendations": [
    {{
      "name": "Service/Item Name",
      "category": "Category",
      "estimated_price": 5000,
      "platform": "Local Caterer / Swiggy Genie",
      "reason": "Why recommended",
      "style": "Style/type description",
      "url": "",
      "quantity": 1
    }}
  ],
  "ai_notes": "Important notes or tips for this event"
}}"""


def _jewelry_planner_prompt(data: dict, has_image: bool = False) -> str:
    outfit_section = ""
    if has_image:
        outfit_section = """
IMAGE ANALYSIS INSTRUCTIONS:
An outfit image has been provided. Analyze ONLY:
- Dominant colors in the clothing
- General clothing style (traditional/western/fusion/formal/casual)
- Formality level
- Suitable jewelry styles based on what you observe
Do NOT identify the person or make assumptions beyond visible clothing.
"""
    elif data.get("outfit_description"):
        outfit_section = f"\nOutfit description: {data['outfit_description']}"

    jewelry_types = ", ".join(data.get("jewelry_types", ["necklace"]))

    return f"""You are a professional Indian jewelry stylist and budget advisor.
{outfit_section}
Client Request:
- Occasion: {data.get('occasion', 'casual')}
- Jewelry types needed: {jewelry_types}
- Preferred style: {data.get('preferred_style', 'contemporary')}
- Preferred metal/color: {data.get('preferred_metal', 'gold')}
- Total budget: ₹{data.get('budget', 0):,.0f}
- Additional preferences: {data.get('additional_preferences', 'None') or 'None'}

Your task:
1. Recommend jewelry pieces that match the occasion and style
2. If an image was provided, describe what you observed about the outfit and how it influenced your recommendations
3. Allocate budget across jewelry categories
4. Suggest specific pieces with estimated prices from Tanishq, Malabar Gold, CaratLane, Amazon, Flipkart
5. Explain why each piece suits the occasion/outfit
6. Keep total within budget
7. Label all prices as "Estimated Price"

IMPORTANT: Return ONLY a valid JSON object (no markdown):
{{
  "summary": "Style overview and why these pieces work",
  "outfit_analysis": "What the outfit looks like and how it influenced choices (or 'No image provided')",
  "budget_allocation": [
    {{"category": "Necklace", "allocated_budget": 5000}}
  ],
  "recommendations": [
    {{
      "name": "Jewelry Piece Name",
      "category": "Category (e.g., Necklace, Earrings)",
      "estimated_price": 3499,
      "platform": "Tanishq / CaratLane",
      "reason": "Why this matches the occasion and style",
      "style": "Style description",
      "url": "",
      "quantity": 1
    }}
  ],
  "ai_notes": "Styling tips or important notes"
}}"""


# ─── Public API ───────────────────────────────────────────────────────────────
def generate_home_recommendations(data: dict) -> dict:
    """Call Gemini for home interior recommendations."""
    prompt = _home_planner_prompt(data)
    raw = _call_gemini(prompt)
    result = _extract_json(raw)
    if result is None:
        raise GeminiAPIError("Could not parse recommendations from AI response. Please try again.")
    return result


def generate_party_recommendations(data: dict) -> dict:
    """Call Gemini for party/event recommendations."""
    prompt = _party_planner_prompt(data)
    raw = _call_gemini(prompt)
    result = _extract_json(raw)
    if result is None:
        raise GeminiAPIError("Could not parse recommendations from AI response. Please try again.")
    return result


def generate_jewelry_recommendations(data: dict, image_bytes: Optional[bytes] = None,
                                      image_mime: Optional[str] = None) -> dict:
    """Call Gemini for jewelry recommendations, optionally with outfit image."""
    has_image = bool(image_bytes)
    prompt = _jewelry_planner_prompt(data, has_image=has_image)
    raw = _call_gemini(prompt, image_bytes=image_bytes, image_mime=image_mime)
    result = _extract_json(raw)
    if result is None:
        raise GeminiAPIError("Could not parse recommendations from AI response. Please try again.")
    return result


def test_gemini_connection() -> dict:
    """Lightweight connectivity test. Returns status dict without exposing secrets."""
    from app.config import get_settings
    settings = get_settings()

    if not settings.gemini_configured:
        return {
            "configured": False,
            "model": settings.gemini_model,
            "status": "API key not configured",
            "ok": False,
        }

    try:
        raw = _call_gemini('Respond with exactly: {"test": "ok"}')
        result = _extract_json(raw)
        ok = result is not None and result.get("test") == "ok"
        return {
            "configured": True,
            "model": settings.gemini_model,
            "status": "Connected" if ok else "Unexpected response",
            "ok": ok,
        }
    except GeminiQuotaExceededError:
        return {"configured": True, "model": settings.gemini_model,
                "status": "Quota exceeded", "ok": False}
    except GeminiAPIError as e:
        return {"configured": True, "model": settings.gemini_model,
                "status": str(e), "ok": False}
    except Exception as e:
        return {"configured": True, "model": settings.gemini_model,
                "status": f"Error: {str(e)}", "ok": False}
