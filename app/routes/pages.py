"""
PocketSmart AI — Static Pages Routes
About, Team, Careers, Contact, Pricing, Blog, Guides, FAQ, Support, Legal pages.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import decode_token, get_token_from_request

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


# ── Company Pages ─────────────────────────────────────────────────────────────
@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/about.html", {"request": request, **ctx})


@router.get("/team", response_class=HTMLResponse)
async def team_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/team.html", {"request": request, **ctx})


@router.get("/careers", response_class=HTMLResponse)
async def careers_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/careers.html", {"request": request, **ctx})


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/contact.html", {"request": request, **ctx})


# ── Product Pages ─────────────────────────────────────────────────────────────
@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/pricing.html", {"request": request, **ctx})


# ── Resource Pages ────────────────────────────────────────────────────────────
@router.get("/blog", response_class=HTMLResponse)
async def blog_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/blog.html", {"request": request, **ctx})


@router.get("/guides", response_class=HTMLResponse)
async def guides_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/guides.html", {"request": request, **ctx})


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/faq.html", {"request": request, **ctx})


@router.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/support.html", {"request": request, **ctx})


# ── Legal Pages ───────────────────────────────────────────────────────────────
@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/privacy.html", {"request": request, **ctx})


@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/terms.html", {"request": request, **ctx})


@router.get("/cookies", response_class=HTMLResponse)
async def cookies_page(request: Request):
    ctx = _get_user_context(request)
    return templates.TemplateResponse("pages/cookies.html", {"request": request, **ctx})
