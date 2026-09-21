# SkillBridge AI – AI Career Navigator for Pakistani Youth

## Problem Statement

Many graduates in Pakistan face unemployment because they are unsure which skills employers require, what skills they are missing for their desired careers, and where to find suitable job opportunities. As a result, there is a significant gap between graduates' abilities and industry expectations.

## Proposed Solution

**SkillBridge AI** is an AI-powered career guidance platform that helps students and graduates identify skill gaps, create personalized learning plans, and discover relevant career opportunities.

Users can upload their CV or manually enter their skills. The platform analyzes their profile, compares it with the requirements of their chosen career, and provides practical recommendations to improve their employability.

## Key Features

* AI-based CV and skill extraction (PDF/DOCX parsing + categorization).
* Comparison of user skills with job market requirements.
* Detection of missing skills (Skill Gap Analysis) with match percentage.
* Personalized learning roadmap with recommended courses, YouTube tutorials, and practice platforms.
* Job, internship, and freelance opportunity recommendations based on user skills (Pakistani market focus).
* AI Career Assistant for career guidance and interview preparation.
* Dashboard showing skill match percentage, learning progress, and career readiness.
* Downloadable PDF roadmap report.

## Target Users

* University students
* Fresh graduates
* Job seekers
* Career changers

## Expected Impact

SkillBridge AI helps reduce the gap between education and industry by providing personalized career guidance, helping graduates learn in-demand skills, and improving their chances of employment in Pakistan.

---

## Tech Stack (built entirely with tools already installed on this machine)

* **Backend:** Python 3.14, FastAPI, Uvicorn
* **Database:** SQLite (zero-config, file-based — no server install required)
* **Auth:** JWT (PyJWT) + bcrypt password hashing, HttpOnly cookies
* **CV Parsing:** pypdf (PDF), python-docx (DOCX)
* **PDF Reports:** ReportLab
* **Data Layer:** pandas / numpy available for future analytics
* **Frontend:** Server-rendered HTML (Jinja2) + vanilla JS + Chart.js (CDN) — no Node build step required
* **AI Engine:** Rule-based skill-extraction, gap-analysis, roadmap, and chatbot engine (`app/skills_engine.py`), fully offline. Swap in OpenAI/Gemini later by replacing `chatbot_reply()` with an API call — the rest of the app is unaffected.

## Project Structure

```
skillbridge-ai/
  backend/
    requirements.txt
    app/
      main.py                # FastAPI app, page routes
      database.py             # SQLite schema + connection
      auth.py                  # JWT + password hashing
      models.py                # Pydantic request schemas
      skills_data.py           # Roles, skills dictionary, resources, opportunities
      resume_parser.py         # PDF/DOCX text + skill extraction
      skills_engine.py         # Gap analysis, roadmap, matching, chatbot logic
      routers/
        auth_router.py
        profile_router.py
        skills_router.py
        opportunities_router.py
        chatbot_router.py
        reports_router.py
      templates/                # Jinja2 HTML pages
      static/css, static/js       # Styles + client-side logic
    data/skillbridge.db          # created automatically on first run
    uploads/
```

## Running Locally

```bash
cd skillbridge-ai/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000** in your browser.

## Development

Install the dev tooling once, then lint and test from the repo root:

```bash
pip install -r requirements-dev.txt
python -m ruff check .     # lint
python -m pytest -q        # smoke tests
```

`tests/smoke_test.py` walks the whole product — sign-up, sign-in, CV upload and
skill extraction, gap analysis, roadmap, progress, opportunities, the advisor and
the PDF reports — against a throwaway SQLite database, so it never touches real
data. Run both before committing.

## Deployment Notes

* Any host that runs Python (Render, Railway, PythonAnywhere, Fly.io, a VPS) works. SQLite ships with the app for local use, but a host with an ephemeral filesystem (Vercel) needs a real database — set a Postgres connection string and the app uses it automatically.
* A `backend/Dockerfile` is included for hosts that deploy from a container (Render, Railway, Fly.io, etc.). It binds to `$PORT`, which those platforms set automatically.
* Before going live, copy `backend/.env.example` to `.env` (or set the equivalents in your host's dashboard):
  * `POSTGRES_URL` / `DATABASE_URL` — **required in production.** Any Postgres connection string; the app finds it whatever prefix the host uses. Without one, a deployed app serves a setup page instead of running on storage it would lose.
  * `SKILLBRIDGE_SECRET` — *optional.* Signs session JWTs. If unset, the app generates a strong random secret on first run and stores it in the database, so sessions stay valid across restarts. Set it only to control the value yourself: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
  * `SKILLBRIDGE_SECURE_COOKIES=true` — only needed outside Vercel. Marks the login cookie `Secure` so it is never sent over plain HTTP; on Vercel this turns on automatically.
* `GET /health` returns `{"status": "ok"}` — point your host's health check at it.
* SQLite runs in WAL mode for better concurrent read/write behavior under multiple requests; for real horizontal scaling (multiple server instances), swap `sqlite3` in `database.py` for MongoDB/Postgres — the router layer only touches `database.py`, so the rest of the app is unaffected.
* To add real generative AI (OpenAI/Gemini) for CV parsing or the chatbot, add your API key as an env var and call it inside `resume_parser.py` / `skills_engine.chatbot_reply()`.
