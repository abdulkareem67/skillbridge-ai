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


def test_protected_pages_redirect_when_signed_out(fresh_client):
    # fresh_client is guaranteed to have no session, regardless of what the
    # shared client did in other files.
    for path in PROTECTED_PAGES:
        response = fresh_client.get(path, follow_redirects=False)
        assert response.status_code in (302, 307), f"{path} was reachable signed out"


def test_legal_pages_are_public(client):
    for path in ("/privacy", "/terms"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "PLACEHOLDER" in response.text, f"{path} lost its to-fill markers"


def test_pages_carry_meta_and_social_tags(client):
    for path in ("/", "/login", "/register", "/privacy"):
        body = client.get(path).text
        assert 'name="description"' in body, path
        assert 'property="og:image"' in body, path
        assert 'name="twitter:card"' in body, path
        assert 'rel="canonical"' in body, path


def test_every_page_has_exactly_one_h1(client):
    for path in ("/", "/login", "/register", "/privacy", "/terms"):
        assert client.get(path).text.count("<h1") == 1, path


def test_icon_only_buttons_are_labelled(client):
    """An icon with no text needs an accessible name or it is unusable by screen reader."""
    body = client.get("/").text
    assert 'id="theme-toggle"' in body
    assert body.count("aria-label") >= 1
    theme_button = body[body.index('id="theme-toggle"') - 200: body.index('id="theme-toggle"') + 300]
    assert "aria-label" in theme_button


def test_skip_link_present(client):
    assert 'class="skip-link"' in client.get("/").text


def test_landing_stats_come_from_the_data(client):
    """The headline figures must be counted, not typed in — and must not say 'sample'."""
    from app.skills_data import platform_stats

    body = client.get("/").text
    stats = platform_stats()
    assert str(stats["career_tracks"]) in body
    assert str(stats["skills_tracked"]) in body
    assert "sample" not in body.lower()


def test_no_real_employer_names_in_example_roles():
    """Invented vacancies must never be attributed to real companies."""
    from app.skills_data import OPPORTUNITIES

    real_companies = {
        "daraz", "careem", "jazz", "nestlé", "nestle", "hbl", "pwc", "siemens pakistan",
        "bykea", "10pearls", "arbisoft", "k-electric", "nespak", "upwork", "fiverr",
        "systems limited", "techlogix", "netsol", "afiniti", "ptcl", "ufone", "devsinc",
        "folio3", "rewterz", "contour software", "millat", "atlas honda", "nrtc",
    }
    for opportunity in OPPORTUNITIES:
        assert opportunity["company"].lower() not in real_companies, opportunity["company"]


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
        if path == "/dashboard":
            continue  # covered below: a brand-new account is sent to onboarding first
        assert client.get(path, follow_redirects=False).status_code == 200, path


def test_new_account_is_onboarded_before_the_dashboard(client, account):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.headers.get("location") == "/onboarding"


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


def test_dashboard_opens_once_set_up(client, account):
    """By now the account has a role (above) and skills (CV upload)."""
    assert client.get("/dashboard", follow_redirects=False).status_code == 200


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


# --------------------------------------------------------------------------- #
# Market neutrality
# --------------------------------------------------------------------------- #
def test_job_boards_follow_the_candidates_market():
    """A job hunter in London must not be sent to Pakistani job boards."""
    from app.markets import job_board_links, market_for_location

    assert market_for_location("Lahore") == "PK"
    assert market_for_location("London") == "GB"
    assert market_for_location("Dubai") == "AE"
    assert market_for_location(None) == "GLOBAL"
    assert market_for_location("Nairobi") == "GLOBAL"

    uk = " ".join(link["url"] for link in job_board_links("Data Analyst", "Job", "GB"))
    assert "reed.co.uk" in uk
    assert "rozee.pk" not in uk

    pk = " ".join(link["url"] for link in job_board_links("Data Analyst", "Job", "PK"))
    assert "rozee.pk" in pk

    # The fallback must still be usable on its own.
    assert job_board_links("Data Analyst", "Job", None)


def test_engineering_licence_is_localised():
    from app.skills_engine import recommend_certifications

    pk = recommend_certifications("Structural Engineer", "Lahore")
    us = recommend_certifications("Structural Engineer", "Austin")
    assert any("Pakistan Engineering Council" in c for c in pk)
    assert any("Professional Engineer" in c for c in us)
    # The placeholder must always be resolved, never shown raw.
    assert not any("{" in c for c in pk + us)


def test_signup_does_not_assume_a_country(client):
    """Registering without a location must not silently place you in one."""
    import uuid

    email = f"nolocation-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"name": "No Location", "email": email, "password": "another-good-pw-1"},
    )
    assert response.status_code == 200, response.text
    assert client.get("/api/profile/me").json()["location"] is None
