import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import ENV_SECRET, IS_PRODUCTION, get_active_session, list_sessions
from .database import USE_POSTGRES, connect, init_db
from .skills_data import platform_stats
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

# In production the app signs sessions with a secret kept in the database. With
# no database there is nowhere durable to keep it (the local SQLite file is wiped
# on every cold start), so rather than run insecurely — or crash with an opaque
# 500 — we serve a page explaining how to finish the setup.
NEEDS_SETUP = IS_PRODUCTION and not ENV_SECRET and not USE_POSTGRES

if not NEEDS_SETUP:
    init_db()
elif not ENV_SECRET:
    logger.warning("No database connected — serving the setup page until one is added.")

SETUP_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finish setup — SkillBridge AI</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
       background:#0b0f1c;color:#eef0fb;font-family:system-ui,-apple-system,Segoe UI,sans-serif;padding:24px}
  .card{max-width:560px;width:100%;background:#151a2e;border:1px solid #2a3150;
        border-radius:18px;padding:32px}
  h1{margin:0 0 6px;font-size:1.5rem}
  .sub{color:#9aa3c7;margin:0 0 24px}
  ol{line-height:1.8;padding-left:20px;margin:0}
  li{margin-bottom:10px}
  b{color:#7dd3fc}
  .note{margin-top:24px;padding:14px 16px;background:#101528;border-radius:12px;
        color:#9aa3c7;font-size:0.92rem;line-height:1.6}
</style></head><body>
<div class="card">
  <h1>&#9889; Almost there</h1>
  <p class="sub">SkillBridge AI needs a database before it can start.</p>
  <ol>
    <li>Open this project on <b>vercel.com</b></li>
    <li>Click the <b>Storage</b> tab</li>
    <li>Click <b>Create Database</b> and choose <b>Neon &mdash; Serverless Postgres</b></li>
    <li>Pick the <b>Free</b> plan, then click <b>Connect</b> to link it to this project</li>
    <li>Go to <b>Deployments</b>, click the <b>&#8943;</b> menu on the newest one, and choose <b>Redeploy</b></li>
  </ol>
  <div class="note">
    That&rsquo;s the only step left. Once the database is connected, this page
    disappears and your site starts working &mdash; logins will stay signed in and
    your data will be saved permanently. No other settings are needed.
  </div>
</div></body></html>"""


@app.middleware("http")
async def setup_gate(request: Request, call_next):
    if NEEDS_SETUP and request.url.path != "/health":
        return HTMLResponse(SETUP_PAGE, status_code=503)
    return await call_next(request)


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

SITE_NAME = "SkillBridge AI"

# One description per page, used for the meta description and the social cards.
# Search results and shared links show these, so each one names what the page
# actually does rather than repeating the site tagline.
PAGE_DESCRIPTIONS = {
    "landing.html": (
        "Upload your CV, see which skills you're missing for your target role, "
        "and get a free step-by-step roadmap to close the gap."
    ),
    "login.html": "Sign in to SkillBridge AI to continue your career roadmap.",
    "register.html": (
        "Create a free SkillBridge AI account to analyse your CV and build a "
        "personalised learning roadmap."
    ),
    "dashboard.html": "Your skill-match score, progress and next steps at a glance.",
    "cv_upload.html": "Upload a PDF or DOCX CV and we'll extract and categorise your skills.",
    "skill_analysis.html": "Compare your skills against a target role and see exactly what's missing.",
    "roadmap.html": "A phased learning roadmap with free courses and practice for your missing skills.",
    "opportunities.html": "Roles matched to your skills, with job-board searches for your country.",
    "advisor.html": "Ask the career advisor what to learn next, how to improve your CV, and more.",
    "privacy.html": "How SkillBridge AI handles your CV, what we store, and how to delete it.",
    "terms.html": "The terms that apply when you use SkillBridge AI.",
}


def render(request: Request, template: str, **ctx):
    accounts = list_sessions(request)
    active = get_active_session(request)
    ctx.setdefault("accounts", accounts)
    ctx.setdefault("active_uid", active["uid"] if active else None)
    ctx.setdefault("asset_v", int(MAIN_JS_PATH.stat().st_mtime))
    ctx.setdefault("site_name", SITE_NAME)
    ctx.setdefault("page_description", PAGE_DESCRIPTIONS.get(template, ""))
    # Canonical/social URLs must be absolute and must not carry query strings,
    # which would otherwise fragment how a shared link is indexed.
    ctx.setdefault("canonical_url", str(request.url.replace(query=None, fragment=None)))
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
    return render(request, "landing.html", stats=platform_stats())


@app.get("/privacy")
def privacy_page(request: Request):
    return render(request, "privacy.html")


@app.get("/terms")
def terms_page(request: Request):
    return render(request, "terms.html")


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
