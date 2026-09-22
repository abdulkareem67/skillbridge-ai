"""Phase 3: throttling, onboarding, email handling and Google sign-in.

Every test here uses `fresh_client`, its own cookie jar, so signing in as other
people never changes who the rest of the suite is signed in as.
"""
import time
import uuid
from urllib.parse import parse_qs, urlparse

import jwt
import pytest


def _email(tag: str) -> str:
    return f"{tag}-{uuid.uuid4().hex[:10]}@example.com"


def _register(c, email=None, password="a-strong-pw-1"):
    email = email or _email("user")
    r = c.post("/api/auth/register", json={"name": "Test Person", "email": email, "password": password})
    assert r.status_code == 200, r.text
    return email, password, r.json()


# --------------------------------------------------------------------------- #
# Throttling
# --------------------------------------------------------------------------- #
def test_repeated_wrong_passwords_are_throttled(fresh_client):
    from app import rate_limit

    email, _, _ = _register(fresh_client)
    fresh_client.post("/api/auth/logout")

    for _ in range(rate_limit.LOGIN_PER_EMAIL):
        r = fresh_client.post("/api/auth/login", json={"email": email, "password": "wrong-guess"})
        assert r.status_code == 401

    blocked = fresh_client.post("/api/auth/login", json={"email": email, "password": "wrong-guess"})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert "wait" in blocked.json()["detail"].lower()


def test_throttle_blocks_even_the_right_password(fresh_client):
    """Otherwise the lockout is a speed bump: the guess that finally lands wins."""
    from app import rate_limit

    email, password, _ = _register(fresh_client)
    fresh_client.post("/api/auth/logout")
    for _ in range(rate_limit.LOGIN_PER_EMAIL):
        fresh_client.post("/api/auth/login", json={"email": email, "password": "nope"})
    assert fresh_client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 429


def test_one_accounts_lockout_does_not_affect_another(fresh_client):
    from app import rate_limit

    victim, _, _ = _register(fresh_client)
    bystander, bystander_pw, _ = _register(fresh_client)
    fresh_client.post("/api/auth/logout")
    for _ in range(rate_limit.LOGIN_PER_EMAIL):
        fresh_client.post("/api/auth/login", json={"email": victim, "password": "nope"})
    assert fresh_client.post("/api/auth/login", json={"email": bystander, "password": bystander_pw}).status_code == 200


def test_successful_login_resets_the_count(fresh_client):
    from app import rate_limit

    email, password, _ = _register(fresh_client)
    fresh_client.post("/api/auth/logout")
    for _ in range(rate_limit.LOGIN_PER_EMAIL - 1):
        fresh_client.post("/api/auth/login", json={"email": email, "password": "typo"})
    assert fresh_client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200
    fresh_client.post("/api/auth/logout")
    # A fresh allowance: one more typo is not the fifth strike.
    assert fresh_client.post("/api/auth/login", json={"email": email, "password": "typo"}).status_code == 401


def test_attempt_log_never_stores_readable_emails(fresh_client):
    from app.database import connect

    email, _, _ = _register(fresh_client)
    fresh_client.post("/api/auth/logout")
    fresh_client.post("/api/auth/login", json={"email": email, "password": "nope"})
    conn = connect()
    try:
        buckets = [r["bucket"] for r in conn.execute("SELECT bucket FROM login_attempts").fetchall()]
    finally:
        conn.close()
    assert buckets
    assert not any(email.split("@")[0] in b for b in buckets)


# --------------------------------------------------------------------------- #
# Email handling
# --------------------------------------------------------------------------- #
def test_email_is_case_insensitive(fresh_client):
    email, password, _ = _register(fresh_client, email=_email("Mixed.Case").replace("mixed", "Mixed"))
    fresh_client.post("/api/auth/logout")
    assert fresh_client.post("/api/auth/login", json={"email": email.upper(), "password": password}).status_code == 200


def test_same_email_in_different_case_is_a_duplicate(fresh_client):
    email, _, _ = _register(fresh_client)
    r = fresh_client.post("/api/auth/register", json={"name": "Twin", "email": email.upper(), "password": "a-strong-pw-1"})
    assert r.status_code == 400


def test_register_rejects_a_short_password(fresh_client):
    r = fresh_client.post("/api/auth/register", json={"name": "Shorty", "email": _email("short"), "password": "1234567"})
    assert r.status_code == 422


def test_single_part_and_non_latin_names_are_accepted(fresh_client):
    for name in ("Madonna", "محمد علی", "张伟"):
        r = fresh_client.post("/api/auth/register", json={"name": name, "email": _email("name"), "password": "a-strong-pw-1"})
        assert r.status_code == 200, (name, r.text)
        assert r.json()["name"] == name


# --------------------------------------------------------------------------- #
# Onboarding
# --------------------------------------------------------------------------- #
def test_new_user_is_sent_to_onboarding_not_an_empty_dashboard(fresh_client):
    _, _, body = _register(fresh_client)
    assert body["next"] == "/onboarding"
    r = fresh_client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/onboarding"
    assert fresh_client.get("/onboarding").status_code == 200


def test_onboarding_completes_with_role_and_a_skill(fresh_client):
    _register(fresh_client)
    assert fresh_client.post("/api/profile/location", json={"location": "Manchester, United Kingdom"}).status_code == 200
    role = fresh_client.get("/api/skills/roles").json()["roles"][0]
    fresh_client.post("/api/profile/target-role", json={"role": role})
    # A role alone is not enough: the dashboard would still be empty.
    assert fresh_client.get("/dashboard", follow_redirects=False).status_code in (302, 307)

    fresh_client.post("/api/profile/skills/manual", json={"skills": ["Python"]})
    assert fresh_client.get("/dashboard", follow_redirects=False).status_code == 200


def test_login_sends_unfinished_users_back_to_onboarding(fresh_client):
    email, password, _ = _register(fresh_client)
    fresh_client.post("/api/auth/logout")
    r = fresh_client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.json()["next"] == "/onboarding"


def test_location_is_saved_and_steers_job_boards(fresh_client):
    _register(fresh_client)
    fresh_client.post("/api/profile/location", json={"location": "  London,   United Kingdom  "})
    assert fresh_client.get("/api/profile/me").json()["location"] == "London, United Kingdom"
    fresh_client.post("/api/profile/skills/manual", json={"skills": ["Python", "SQL"]})
    links = " ".join(link["url"] for o in fresh_client.get("/api/opportunities").json()["opportunities"] for link in o["apply_links"])
    assert "reed.co.uk" in links


def test_blank_location_is_rejected(fresh_client):
    _register(fresh_client)
    assert fresh_client.post("/api/profile/location", json={"location": "   "}).status_code == 422


def test_onboarding_requires_sign_in(fresh_client):
    assert fresh_client.get("/onboarding", follow_redirects=False).status_code in (302, 307)


# --------------------------------------------------------------------------- #
# Google sign-in
# --------------------------------------------------------------------------- #
@pytest.fixture
def google_on(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")


def _id_token(**overrides):
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "test-client-id.apps.googleusercontent.com",
        "exp": int(time.time()) + 600,
        "email": _email("google"),
        "email_verified": True,
        "name": "Google Person",
    }
    claims.update(overrides)
    return jwt.encode(claims, "irrelevant", algorithm="HS256"), claims


def test_google_button_hidden_when_not_configured(fresh_client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    assert "/api/auth/google/login" not in fresh_client.get("/login").text
    r = fresh_client.get("/api/auth/google/login", follow_redirects=False)
    assert "error=google_unavailable" in r.headers["location"]


def test_google_button_shown_when_configured(fresh_client, google_on):
    assert "/api/auth/google/login" in fresh_client.get("/login").text
    assert "/api/auth/google/login" in fresh_client.get("/register").text


def test_google_login_redirects_to_google_with_state(fresh_client, google_on):
    r = fresh_client.get("/api/auth/google/login", follow_redirects=False)
    target = urlparse(r.headers["location"])
    assert target.netloc == "accounts.google.com"
    q = parse_qs(target.query)
    assert q["client_id"] == ["test-client-id.apps.googleusercontent.com"]
    assert q["state"][0]
    assert "oauth_state" in r.headers["set-cookie"]


def test_google_callback_signs_in_and_creates_account(fresh_client, google_on, monkeypatch):
    from app import google_oauth

    token, claims = _id_token()
    monkeypatch.setattr(google_oauth, "exchange_code", lambda code, uri: google_oauth.verify_claims(token))

    start = fresh_client.get("/api/auth/google/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    r = fresh_client.get("/api/auth/google/callback", params={"code": "abc", "state": state}, follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"].startswith("/onboarding?signed_in=")
    assert fresh_client.get("/api/profile/me").json()["email"] == claims["email"]


def test_google_callback_links_to_an_existing_account(fresh_client, google_on, monkeypatch):
    from app import google_oauth

    email, _, body = _register(fresh_client)
    fresh_client.post("/api/auth/logout")
    token, _ = _id_token(email=email)
    monkeypatch.setattr(google_oauth, "exchange_code", lambda code, uri: google_oauth.verify_claims(token))

    start = fresh_client.get("/api/auth/google/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    fresh_client.get("/api/auth/google/callback", params={"code": "abc", "state": state}, follow_redirects=False)
    assert fresh_client.get("/api/profile/me").json()["id"] == body["id"]


def test_google_callback_rejects_a_forged_state(fresh_client, google_on, monkeypatch):
    """Without this check, an attacker's callback link logs you into their account."""
    from app import google_oauth

    called = []
    monkeypatch.setattr(google_oauth, "exchange_code", lambda code, uri: called.append(1))
    fresh_client.get("/api/auth/google/login", follow_redirects=False)
    r = fresh_client.get("/api/auth/google/callback", params={"code": "abc", "state": "attacker"}, follow_redirects=False)
    assert "error=google_state" in r.headers["location"]
    assert not called, "the code must not be exchanged when state doesn't match"


def test_google_cancel_is_handled(fresh_client, google_on):
    r = fresh_client.get("/api/auth/google/callback", params={"error": "access_denied"}, follow_redirects=False)
    assert "error=google_cancelled" in r.headers["location"]


@pytest.mark.parametrize(
    "override, reason",
    [
        ({"aud": "someone-elses-app"}, "different application"),
        ({"iss": "https://evil.example"}, "not issued by Google"),
        ({"email_verified": False}, "isn't verified"),
        ({"exp": int(time.time()) - 60}, "expired"),
    ],
)
def test_bad_identity_tokens_are_refused(google_on, override, reason):
    from app import google_oauth

    token, _ = _id_token(**override)
    with pytest.raises(google_oauth.GoogleSignInError, match=reason):
        google_oauth.verify_claims(token)
