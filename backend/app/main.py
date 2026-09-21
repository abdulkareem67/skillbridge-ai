import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import DEFAULT_DEV_SECRET, IS_PRODUCTION, SECRET_KEY, get_active_session, list_sessions
from .database import connect, init_db
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

if SECRET_KEY == DEFAULT_DEV_SECRET:
    if IS_PRODUCTION:
        # Fail closed: refuse to run publicly with the well-known repo secret,
        # which anyone could use to forge login sessions.
        raise RuntimeError(
            "SKILLBRIDGE_SECRET is not set. Add it in your Vercel project settings "
            "(Settings -> Environment Variables) with a strong random value, e.g. "
            "`python -c \"import secrets; print(secrets.token_urlsafe(48))\"`, then redeploy."
        )
    logger.warning(
        "SKILLBRIDGE_SECRET is not set — using the built-in development secret. "
        "Fine for local development, but set SKILLBRIDGE_SECRET before deploying publicly."
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
    )
    if IS_PRODUCTION:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
    return response

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
    """A valid session cookie is not enough — the account it names must still
    exist in the database. On an ephemeral SQLite host the users table can be
    wiped while an old cookie lives on, and without this check that stale
    cookie would wave someone straight into the dashboard."""
    session = get_active_session(request)
    if session is None:
        return False
    try:
        conn = connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM users WHERE id = ?", (int(session["uid"]),)
            ).fetchone()
        finally:
            conn.close()
    except Exception:
        return False
    return row is not None


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
