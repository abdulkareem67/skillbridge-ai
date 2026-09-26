"""Regression tests for bugs found in a full read-through of the code.

Each test names the bug it guards against. Several of these only showed up on
production (Postgres, non-English names), which the rest of the suite never
exercises, so they fake just enough of that world to reproduce them.
"""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parent.parent / "backend" / "app" / "static" / "js"


def _register(client, name="Fix Test", location=None):
    # Every test client shares one IP, and this file creates enough accounts to
    # trip the per-IP sign-up throttle for the tests that run after it.
    from app.database import connect

    conn = connect()
    try:
        conn.execute("DELETE FROM login_attempts WHERE bucket LIKE 'register-ip:%'")
        conn.commit()
    finally:
        conn.close()

    body = {"name": name, "email": f"fix-{uuid.uuid4().hex[:10]}@example.com", "password": "a-strong-pw-1"}
    if location:
        body["location"] = location
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 200, r.text
    return body


# --------------------------------------------------------------------------- #
# Onboarding step 1 did nothing: `const t = city.value` shadowed the t() helper
# --------------------------------------------------------------------------- #
def test_no_script_shadows_the_translation_helper():
    for path in JS_DIR.glob("*.js"):
        source = path.read_text(encoding="utf-8")
        assert not re.search(r"\b(const|let|var)\s+t\s*=", source), f"{path.name} redeclares t()"


# --------------------------------------------------------------------------- #
# Data export 500'd on Postgres, which returns timestamps as datetime objects
# --------------------------------------------------------------------------- #
class _DatetimeRows:
    """Wraps a SQLite connection so created_at comes back as a datetime, as it
    does from Postgres. Everything else passes straight through."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cur = self._conn.execute(sql, params)
        return _DatetimeCursor(cur)

    def __getattr__(self, name):
        return getattr(self._conn, name)


class _DatetimeCursor:
    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = cur.lastrowid

    @staticmethod
    def _convert(row):
        if row is None:
            return None
        row = dict(row)
        if isinstance(row.get("created_at"), str):
            row["created_at"] = datetime.now(timezone.utc)
        return row

    def fetchone(self):
        return self._convert(self._cur.fetchone())

    def fetchall(self):
        return [self._convert(r) for r in self._cur.fetchall()]


def test_export_survives_postgres_style_timestamps(fresh_client):
    from app.database import get_db
    from app.main import app

    _register(fresh_client)
    fresh_client.post("/api/chatbot/message", json={"message": "hello"})

    def datetime_db():
        for conn in get_db():
            yield _DatetimeRows(conn)

    app.dependency_overrides[get_db] = datetime_db
    try:
        r = fresh_client.get("/api/profile/export")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 200, r.text
    assert r.json()["account"]["created_at"]


# --------------------------------------------------------------------------- #
# Improved-CV PDF 500'd for non-Latin names and for names containing "<"
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", ["عبدالرحیم شہزاد", "Ali <b", "Tom & Jerry", "Zoë O'Brien"])
def test_cv_pdf_works_for_any_name(fresh_client, name):
    _register(fresh_client, name=name)
    fresh_client.post("/api/profile/skills/manual", json={"skills": ["Python", "C++ <templates>"]})
    fresh_client.post("/api/profile/target-role", json={"role": "Software Engineer"})

    for url in ("/api/reports/improved-cv-pdf", "/api/reports/roadmap-pdf"):
        r = fresh_client.get(url)
        assert r.status_code == 200, (url, r.text[:200])
        assert r.content[:4] == b"%PDF"
        disposition = r.headers["content-disposition"]
        assert "filename*=UTF-8''" in disposition
        disposition.encode("latin-1")  # a header must be Latin-1 safe


# --------------------------------------------------------------------------- #
# "Milwaukee" and "Ukraine" were placed in the UK (they contain "uk")
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("location, market", [
    ("Milwaukee", "GLOBAL"),
    ("Ukraine", "GLOBAL"),
    ("Leeds, UK", "GB"),
    ("Lahore, Pakistan", "PK"),
    ("Abu Dhabi", "AE"),
    ("usa", "US"),
])
def test_location_matches_whole_words(location, market):
    from app.markets import market_for_location

    assert market_for_location(location) == market


# --------------------------------------------------------------------------- #
# CV parsing invented skills from ordinary words
# --------------------------------------------------------------------------- #
def test_everyday_words_are_not_skills():
    from app.resume_parser import extract_skills_from_text

    prose = (
        "I hold a DL (driving licence), handled the rest of the paperwork, keep lean habits, "
        "filed my tax return in spring, and express ideas clearly. Dosage: 5 ml."
    )
    found = {s["skill_name"] for s in extract_skills_from_text(prose)}
    for wrong in ("Deep Learning", "REST APIs", "Lean Manufacturing", "Taxation",
                  "Spring Boot", "Node.js", "Machine Learning"):
        assert wrong not in found, wrong


def test_real_skills_are_still_found():
    from app.resume_parser import extract_skills_from_text

    cv = "Built REST APIs with Express.js; ML models in PyTorch; Lean Manufacturing; income tax filing; Bash scripting"
    found = {s["skill_name"] for s in extract_skills_from_text(cv)}
    assert {"REST APIs", "Node.js", "Machine Learning", "PyTorch", "Lean Manufacturing", "Taxation", "Bash Scripting"} <= found
    # "bash" means Bash Scripting, not Linux as well.
    assert "Linux" not in found


def test_short_aliases_still_work_when_typed_as_a_skill(fresh_client):
    _register(fresh_client)
    r = fresh_client.post("/api/profile/skills/manual", json={"skills": ["rest", "tax"]})
    assert set(r.json()["added"]) == {"REST APIs", "Taxation"}


# --------------------------------------------------------------------------- #
# Pakistan-only wording shown to everyone
# --------------------------------------------------------------------------- #
def test_advisor_names_the_users_own_job_boards(fresh_client):
    _register(fresh_client, location="London")
    reply = fresh_client.post("/api/chatbot/message", json={"message": "How do I apply for jobs?"}).json()["reply"]
    assert "Reed" in reply
    assert "Rozee" not in reply


def test_advisor_still_names_local_boards_in_pakistan(fresh_client):
    _register(fresh_client, location="Karachi")
    reply = fresh_client.post("/api/chatbot/message", json={"message": "How do I apply for jobs?"}).json()["reply"]
    assert "Rozee.pk" in reply


def test_scripts_do_not_assume_a_country():
    for path in JS_DIR.glob("*.js"):
        source = path.read_text(encoding="utf-8")
        assert "Pakistan" not in source, path.name


# --------------------------------------------------------------------------- #
# Data and smaller fixes
# --------------------------------------------------------------------------- #
def test_no_roadmap_repeats_a_skill():
    from app.skills_data import ROLES

    for role, phases in ROLES.items():
        skills = phases["beginner"] + phases["intermediate"] + phases["advanced"]
        assert len(skills) == len(set(skills)), role


def test_certifications_fit_the_role():
    from app.skills_engine import recommend_certifications

    assert "PMP" not in recommend_certifications("UI/UX Designer")
    assert "CompTIA Security+" not in recommend_certifications("QA / Test Engineer")


def test_clearing_the_chat_deletes_it(fresh_client):
    _register(fresh_client)
    fresh_client.post("/api/chatbot/message", json={"message": "hello"})
    assert fresh_client.get("/api/chatbot/history").json()["history"]

    assert fresh_client.delete("/api/chatbot/history").status_code == 200
    assert fresh_client.get("/api/chatbot/history").json()["history"] == []


def test_lang_query_parameter_is_honoured(client):
    # The hreflang links point at ?lang=<code>; an unknown one falls back safely.
    assert 'lang="en"' in client.get("/?lang=en").text
    assert 'lang="en"' in client.get("/?lang=xx").text


# --------------------------------------------------------------------------- #
# Mobile layout
# --------------------------------------------------------------------------- #
CSS = (Path(__file__).resolve().parent.parent / "backend" / "app" / "static" / "css" / "style.css").read_text(encoding="utf-8")


def test_classes_the_templates_rely_on_are_defined():
    # These were used in markup but missing from the stylesheet, so hidden
    # headings and raw buttons showed on screen.
    for cls in (".visually-hidden", ".chat-copy-btn", ".nav-menu-account", ".chart-box"):
        assert cls + " " in CSS or cls + "{" in CSS or cls + "," in CSS, cls


@pytest.mark.parametrize("cls, prop", [("page", "padding"), ("section", "margin")])
def test_container_helpers_do_not_zero_its_sides(cls, prop):
    # These classes sit on the same element as .container. A shorthand like
    # `.page { padding: 32px 0 80px }` or `.section { margin: 64px 0 }` wipes
    # the container's side padding / auto-centering: content hit the screen
    # edge on phones, and landing sections hugged the left on wide screens.
    assert not re.search(r"\." + cls + r"\s*\{[^}]*\b" + prop + r":\s*[^;]*\b0\b", CSS), f".{cls} {prop}"


def test_phone_menu_carries_settings_and_logout(client, account):
    body = client.get("/cv-upload").text
    menu = body[body.index('id="nav-links"'): body.index('class="nav-actions"')]
    assert 'href="/settings"' in menu
    assert "logout()" in menu
