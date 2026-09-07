import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import SECRET_KEY, get_active_session, list_sessions
from .database import init_db
from .routers import (
    auth_router,
    chatbot_router,
    opportunities_router,
    profile_router,
    reports_router,
    skills_router,
)

logger = logging.getLogger("skillbridge")

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="SkillBridge AI")

init_db()

if SECRET_KEY == "skillbridge-ai-dev-secret-change-me":
    logger.warning(
        "SKILLBRIDGE_SECRET is not set — using the built-in development secret. "
        "Set the SKILLBRIDGE_SECRET environment variable to a strong random value before deploying "
        "publicly, otherwise anyone can forge login sessions."
    )

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(skills_router.router)
app.include_router(opportunities_router.router)
app.include_router(chatbot_router.router)
app.include_router(reports_router.router)


MAIN_JS_PATH = BASE_DIR / "static" / "js" / "main.js"


def render(request: Request, template: str, **ctx):
    accounts = list_sessions(request)
    active = get_active_session(request)
    ctx.setdefault("accounts", accounts)
    ctx.setdefault("active_uid", active["uid"] if active else None)
    ctx.setdefault("asset_v", int(MAIN_JS_PATH.stat().st_mtime))
    return templates.TemplateResponse(request, template, ctx)


def is_authenticated(request: Request) -> bool:
    return get_active_session(request) is not None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def landing(request: Request):
    return render(request, "landing.html")


@app.get("/login")
def login_page(request: Request):
    return render(request, "login.html")


@app.get("/register")
def register_page(request: Request):
    return render(request, "register.html")


@app.get("/dashboard")
def dashboard_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")
    return render(request, "dashboard.html")


@app.get("/cv-upload")
def cv_upload_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")
    return render(request, "cv_upload.html")


@app.get("/skill-analysis")
def skill_analysis_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")
    return render(request, "skill_analysis.html")


@app.get("/roadmap")
def roadmap_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")
    return render(request, "roadmap.html")


@app.get("/opportunities")
def opportunities_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")
    return render(request, "opportunities.html")


@app.get("/advisor")
def advisor_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")
    return render(request, "advisor.html")
