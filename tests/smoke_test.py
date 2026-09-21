"""End-to-end smoke tests for the features that must keep working.

Covers CV upload, skill extraction, gap analysis, roadmap, opportunities, the
advisor, the dashboard, auth and the dark-mode hooks. These run against a
throwaway SQLite database (see conftest) and are meant as a regression net while
the UI is reworked, not as exhaustive unit tests.

Tests share one signed-in session and run top to bottom, so the sign-out test is
deliberately last.
"""
import io

from docx import Document

PROTECTED_PAGES = [
    "/dashboard",
    "/cv-upload",
    "/skill-analysis",
    "/roadmap",
    "/opportunities",
    "/advisor",
]


def _cv_bytes() -> bytes:
    """A small DOCX whose text contains skills the extractor should recognise."""
    document = Document()
    document.add_paragraph("Smoke Test — Software Engineer")
    document.add_paragraph("Skills: Python, JavaScript, SQL, Git, HTML, CSS")
    document.add_paragraph("Also: Communication, Teamwork, Problem Solving")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# Public pages
# --------------------------------------------------------------------------- #
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_public_pages_render(client):
    for path in ("/", "/login", "/register"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "<html" in response.text, path


def test_dark_mode_hooks_present(client):
    """The theme toggle and the attribute its JS flips must both survive."""
    body = client.get("/").text
    assert 'data-theme="dark"' in body
    assert 'id="theme-toggle"' in body


def test_protected_pages_redirect_when_signed_out(client):
    for path in PROTECTED_PAGES:
        response = client.get(path, follow_redirects=False)
        assert response.status_code in (302, 307), f"{path} was reachable signed out"


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
def test_register_signs_the_user_in(client, account):
    me = client.get("/api/profile/me")
    assert me.status_code == 200
    assert me.json()["email"] == account["email"]


def test_duplicate_email_is_rejected(client, account):
    response = client.post("/api/auth/register", json={**account, "name": "Someone Else"})
    assert response.status_code == 400


def test_protected_pages_render_when_signed_in(client, account):
    for path in PROTECTED_PAGES:
        assert client.get(path).status_code == 200, path


# --------------------------------------------------------------------------- #
# CV upload and skill extraction
# --------------------------------------------------------------------------- #
def test_cv_upload_extracts_skills(client, account):
    response = client.post(
        "/api/profile/cv-upload",
        files={"file": ("cv.docx", _cv_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["extracted_count"] > 0


def test_unsupported_cv_type_is_rejected(client, account):
    response = client.post("/api/profile/cv-upload", files={"file": ("cv.txt", b"Python", "text/plain")})
    assert response.status_code == 400


def test_skills_are_categorized(client, account):
    assert client.get("/api/skills/categorized").status_code == 200


def test_manual_skills_can_be_added(client, account):
    response = client.post("/api/profile/skills/manual", json={"skills": ["Docker"]})
    assert response.status_code == 200


# --------------------------------------------------------------------------- #
# Gap analysis, roadmap, progress
# --------------------------------------------------------------------------- #
def test_roles_are_available(client):
    roles = client.get("/api/skills/roles").json()["roles"]
    assert roles, "no career tracks configured"


def test_target_role_then_gap_analysis_and_roadmap(client, account):
    role = client.get("/api/skills/roles").json()["roles"][0]
    assert client.post("/api/profile/target-role", json={"role": role}).status_code == 200

    gap = client.get("/api/skills/gap-analysis")
    assert gap.status_code == 200, gap.text
    report = gap.json()
    assert report["role"] == role
    assert 0 <= report["match_percent"] <= 100
    # The CV we uploaded contains Python/SQL/Git, so a software role should match
    # something and still leave gaps — proving the comparison actually ran.
    assert report["matched_skills"]
    assert "missing_skills" in report

    roadmap = client.get("/api/skills/roadmap")
    assert roadmap.status_code == 200, roadmap.text
    assert roadmap.json()["role"] == role


def test_unknown_role_is_rejected(client, account):
    assert client.get("/api/skills/gap-analysis", params={"role": "Wizard"}).status_code == 400


def test_progress_can_be_saved_and_read(client, account):
    saved = client.post("/api/skills/progress", json={"skill_name": "Python", "status": "completed"})
    assert saved.status_code == 200
    assert client.get("/api/skills/progress").json().get("Python") == "completed"


def test_invalid_progress_status_is_rejected(client, account):
    response = client.post("/api/skills/progress", json={"skill_name": "Python", "status": "banana"})
    assert response.status_code == 422


def test_resume_tips_and_certifications(client, account):
    assert client.get("/api/skills/resume-tips").status_code == 200
    assert client.get("/api/skills/certifications").status_code == 200


# --------------------------------------------------------------------------- #
# Opportunities, advisor, reports
# --------------------------------------------------------------------------- #
def test_opportunities(client, account):
    assert client.get("/api/opportunities/fields").status_code == 200
    assert client.get("/api/opportunities").status_code == 200
    assert client.get("/api/opportunities/application-guide").status_code == 200


def test_advisor_replies_and_stores_history(client, account):
    reply = client.post("/api/chatbot/message", json={"message": "Which certifications are valuable?"})
    assert reply.status_code == 200
    assert reply.json()["reply"].strip()

    history = client.get("/api/chatbot/history").json()["history"]
    assert len(history) >= 2


def test_reports_generate(client, account):
    assert client.get("/api/reports/improved-cv").status_code == 200

    pdf = client.get("/api/reports/improved-cv-pdf")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"

    roadmap_pdf = client.get("/api/reports/roadmap-pdf")
    assert roadmap_pdf.status_code == 200
    assert roadmap_pdf.content[:4] == b"%PDF"


# --------------------------------------------------------------------------- #
# Sign-out last: it ends the shared session.
# --------------------------------------------------------------------------- #
def test_wrong_password_is_rejected(client, account):
    response = client.post(
        "/api/auth/login",
        json={"email": account["email"], "password": "definitely-not-the-password"},
    )
    assert response.status_code == 401


def test_sign_out_then_sign_in_again(client, account):
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/dashboard", follow_redirects=False).status_code in (302, 307)

    again = client.post(
        "/api/auth/login",
        json={"email": account["email"], "password": account["password"]},
    )
    assert again.status_code == 200
    assert client.get("/dashboard").status_code == 200
