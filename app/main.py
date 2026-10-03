"""
PocketSmart AI — FastAPI Application
Entry: uvicorn app.main:app --reload
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import auth, home, home_planner, party, jewelry, history, pages

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Settings ─────────────────────────────────────────────────────────────────
settings = get_settings()

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PocketSmart AI",
    description="Your Smart Budget & Recommendation Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Static Files ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ─── Templates ────────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory="app/templates")

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(home_planner.router)
app.include_router(party.router)
app.include_router(jewelry.router)
app.include_router(history.router)
app.include_router(pages.router)

# ─── Global Exception Handler ─────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"500 error on {request.url}: {exc}")
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"error": "Internal server error"}, status_code=500)
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("=" * 60)
    logger.info(f"  {settings.app_name} starting up")
    logger.info(f"  Gemini model: {settings.gemini_model}")
    logger.info(f"  Gemini configured: {settings.gemini_configured}")
    logger.info(f"  Debug mode: {settings.debug}")
    logger.info("=" * 60)
    if not settings.gemini_configured:
        logger.warning("GEMINI_API_KEY is not configured! AI features will not work.")
        logger.warning("Please set GEMINI_API_KEY in your .env file.")
