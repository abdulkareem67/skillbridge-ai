"""Phase 5: CV parsing, throttling of heavy endpoints, GDPR, and validation."""
import io

import pytest
from docx import Document
from pypdf import PdfWriter

from app.resume_parser import CVParseError, extract_skills_from_text, extract_text


# --------------------------------------------------------------------------- #
# CV parsing
# --------------------------------------------------------------------------- #
def test_docx_skills_in_a_table_are_read():
    doc = Document()
    doc.add_paragraph("Sam Lee — Engineer")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Skills"
    table.rows[0].cells[1].text = "Python, Docker, Kubernetes"
    buffer = io.BytesIO()
    doc.save(buffer)

    skills = {s["skill_name"] for s in extract_skills_from_text(extract_text("cv.docx", buffer.getvalue()))}
    assert {"Python", "Docker", "Kubernetes"} <= skills


def test_scanned_pdf_gives_a_helpful_message():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)  # a page, but no text layer
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(CVParseError, match="scanned image"):
        extract_text("scan.pdf", buffer.getvalue())


def test_empty_docx_is_reported():
    buffer = io.BytesIO()
    Document().save(buffer)
    with pytest.raises(CVParseError, match="couldn't find any text"):
        extract_text("empty.docx", buffer.getvalue())


def test_corrupt_pdf_is_reported():
    with pytest.raises(CVParseError, match="couldn't open this PDF"):
        extract_text("broken.pdf", b"%PDF-1.4 not really a pdf")


def test_unsupported_type_is_reported():
    with pytest.raises(CVParseError, match="isn't supported"):
        extract_text("cv.doc", b"anything")


def test_scanned_pdf_upload_returns_400_not_zero_skills(client, account):
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = io.BytesIO()
    writer.write(buffer)
    r = client.post("/api/profile/cv-upload", files={"file": ("scan.pdf", buffer.getvalue(), "application/pdf")})
    assert r.status_code == 400
    assert "scanned image" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# Per-user throttling of heavy endpoints
# --------------------------------------------------------------------------- #
def test_advisor_is_throttled_per_user(fresh_client):
    from app import rate_limit

    fresh_client.post("/api/auth/register", json={"name": "Chatty", "email": "chatty@example.com", "password": "a-strong-pw-1"})
    ok = 0
    for _ in range(rate_limit.ADVISOR_MESSAGES_PER_USER + 3):
        r = fresh_client.post("/api/chatbot/message", json={"message": "What should I learn?"})
        if r.status_code == 200:
            ok += 1
        else:
            assert r.status_code == 429
            assert int(r.headers["retry-after"]) > 0
            break
    else:
        pytest.fail("advisor was never throttled")
    assert ok == rate_limit.ADVISOR_MESSAGES_PER_USER


def test_secrets_never_reach_the_rendered_pages(fresh_client, monkeypatch):
    """A configured Google secret and the session secret must stay server-side."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "public-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "super-secret-value-xyz")
    for path in ("/", "/login", "/register"):
        body = fresh_client.get(path).text
        assert "super-secret-value-xyz" not in body


# --------------------------------------------------------------------------- #
# GDPR: export and delete
# --------------------------------------------------------------------------- #
def test_export_returns_all_data_but_no_password(fresh_client):
    fresh_client.post("/api/auth/register", json={"name": "Export Me", "email": "exp@example.com", "password": "a-strong-pw-1"})
    fresh_client.post("/api/profile/skills/manual", json={"skills": ["Python"]})

    r = fresh_client.get("/api/profile/export")
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    data = r.json()
    assert data["account"]["email"] == "exp@example.com"
    assert any(s["skill_name"] == "Python" for s in data["skills"])
    # The hash must never be handed back.
    assert "password" not in str(data).lower() or "password_hash" not in str(data)
    assert "password_hash" not in data["account"]


def test_delete_requires_the_matching_email(fresh_client):
    fresh_client.post("/api/auth/register", json={"name": "Keep Me", "email": "keep@example.com", "password": "a-strong-pw-1"})
    r = fresh_client.post("/api/profile/delete", json={"confirm_email": "someone-else@example.com"})
    assert r.status_code == 400
    assert fresh_client.get("/api/profile/me").status_code == 200  # still there


def test_delete_removes_the_account_and_its_data(fresh_client):
    from app.database import connect

    reg = fresh_client.post("/api/auth/register", json={"name": "Bye", "email": "bye@example.com", "password": "a-strong-pw-1"})
    user_id = reg.json()["id"]
    fresh_client.post("/api/profile/skills/manual", json={"skills": ["Python", "SQL"]})
    fresh_client.post("/api/skills/progress", json={"skill_name": "Python", "status": "completed"})

    r = fresh_client.post("/api/profile/delete", json={"confirm_email": "bye@example.com"})
    assert r.status_code == 200
    # Signed out, and the account is gone.
    assert fresh_client.get("/dashboard", follow_redirects=False).status_code in (302, 307)

    conn = connect()
    try:
        assert conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None
        # The cascade took the dependent rows too.
        assert conn.execute("SELECT 1 FROM skills WHERE user_id = ?", (user_id,)).fetchone() is None
        assert conn.execute("SELECT 1 FROM skill_progress WHERE user_id = ?", (user_id,)).fetchone() is None
    finally:
        conn.close()


def test_export_and_delete_require_sign_in(fresh_client):
    assert fresh_client.get("/api/profile/export").status_code == 401
    assert fresh_client.post("/api/profile/delete", json={"confirm_email": "x@example.com"}).status_code == 401


def test_settings_page_requires_sign_in(fresh_client):
    assert fresh_client.get("/settings", follow_redirects=False).status_code in (302, 307)


def test_register_page_has_a_real_consent_checkbox(client):
    body = client.get("/register").text
    assert 'id="reg-consent"' in body
    assert 'type="checkbox"' in body


# --------------------------------------------------------------------------- #
# Validation bounds
# --------------------------------------------------------------------------- #
def test_oversized_role_query_is_rejected(client, account):
    r = client.get("/api/skills/gap-analysis", params={"role": "x" * 200})
    assert r.status_code == 422  # rejected by the length bound, before any lookup
