import secrets
import sqlite3
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from .. import google_oauth, rate_limit
from ..auth import (
    SECURE_COOKIES,
    add_session,
    clear_all_sessions,
    get_active_session,
    hash_password,
    remove_session,
    switch_active_session,
    verify_password,
)
from ..database import INTEGRITY_ERRORS, get_db
from ..models import LoginRequest, RegisterRequest
from ..onboarding import next_page

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Checked against when the email is unknown, so a miss costs the same bcrypt
# work as a hit. Otherwise the response time alone would reveal which email
# addresses have accounts.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def _find_user(db, email: str):
    # Addresses are case-insensitive in practice; comparing them exactly let
    # "Ali@x.com" and "ali@x.com" become two accounts, and locked people out
    # for capitalising their own email differently.
    return db.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()


@router.post("/register")
def register(payload: RegisterRequest, request: Request, response: Response, db: sqlite3.Connection = Depends(get_db)):
    ip = rate_limit.ip_bucket("register", request)
    rate_limit.enforce(db, [(ip, rate_limit.REGISTER_PER_IP)], "sign-up attempts")
    rate_limit.record(db, ip)
    db.commit()

    email = payload.email.strip().lower()
    if _find_user(db, email):
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    try:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, location) VALUES (?, ?, ?, ?)",
            (payload.name, email, hash_password(payload.password), payload.location),
        )
        db.commit()
    except INTEGRITY_ERRORS:
        # Two sign-ups for one address raced past the check above; the loser
        # gets the same answer as if it had arrived second.
        raise HTTPException(status_code=400, detail="An account with this email already exists") from None
    user_id = cur.lastrowid
    add_session(request, response, user_id, email)
    return {"id": user_id, "name": payload.name, "email": email, "next": "/onboarding"}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: sqlite3.Connection = Depends(get_db)):
    by_email = rate_limit.email_bucket(payload.email)
    by_ip = rate_limit.ip_bucket("login", request)
    rate_limit.enforce(
        db,
        [(by_email, rate_limit.LOGIN_PER_EMAIL), (by_ip, rate_limit.LOGIN_PER_IP)],
        "sign-in attempts",
    )

    user = _find_user(db, payload.email)
    valid = verify_password(payload.password, user["password_hash"] if user else _DUMMY_HASH)
    if not user or not valid:
        rate_limit.record(db, by_email, by_ip)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # A successful sign-in forgives that account's earlier typos. The per-IP
    # count is left alone, or one valid account would reset an attacker's
    # allowance for guessing at everyone else's.
    rate_limit.clear(db, by_email)
    db.commit()
    add_session(request, response, user["id"], user["email"])
    return {"id": user["id"], "name": user["name"], "email": user["email"], "next": next_page(db, user["id"])}


@router.post("/logout")
def logout(request: Request, response: Response):
    """Sign out only the account active in this tab — any other logged-in accounts stay signed in."""
    active = get_active_session(request)
    if active:
        remove_session(request, response, active["uid"])
    else:
        clear_all_sessions(response)
    return {"ok": True}


@router.post("/logout-all")
def logout_all(response: Response):
    clear_all_sessions(response)
    return {"ok": True}


@router.get("/switch-account/{user_id}")
def switch_account(user_id: int, request: Request):
    dest = "/dashboard"
    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        if parsed.netloc == request.url.netloc and parsed.path:
            dest = parsed.path

    redirect = RedirectResponse(url=dest, status_code=303)
    if not switch_active_session(request, redirect, user_id):
        raise HTTPException(status_code=404, detail="That account isn't logged in on this browser")
    return redirect


# --------------------------------------------------------------------------- #
# Sign in with Google
# --------------------------------------------------------------------------- #
def _login_error(code: str) -> RedirectResponse:
    return RedirectResponse(url="/login?" + urlencode({"error": code}), status_code=303)


@router.get("/google/login")
def google_login(request: Request):
    if not google_oauth.is_enabled():
        return _login_error("google_unavailable")

    # `state` ties the callback to this browser. Without it, an attacker could
    # send someone a callback link carrying the attacker's own code and sign the
    # victim into the attacker's account.
    state = secrets.token_urlsafe(24)
    redirect = RedirectResponse(url=google_oauth.authorization_url(request, state), status_code=303)
    redirect.set_cookie(
        google_oauth.STATE_COOKIE,
        state,
        max_age=google_oauth.STATE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=SECURE_COOKIES,
        path="/api/auth/google",
    )
    return redirect


@router.get("/google/callback", name="google_callback")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
):
    if not google_oauth.is_enabled():
        return _login_error("google_unavailable")
    if error or not code:
        # Most often the person simply pressed "Cancel" on Google's screen.
        return _login_error("google_cancelled")

    expected = request.cookies.get(google_oauth.STATE_COOKIE)
    if not expected or not state or not secrets.compare_digest(expected, state):
        return _login_error("google_state")

    try:
        claims = google_oauth.exchange_code(code, google_oauth.redirect_uri(request))
    except google_oauth.GoogleSignInError:
        return _login_error("google_failed")

    email = claims["email"].strip().lower()
    user = _find_user(db, email)
    if user:
        user_id, email = user["id"], user["email"]
    else:
        name = (claims.get("name") or email.split("@")[0]).strip()[:100] or email.split("@")[0]
        # Google accounts have no password here. Storing a hash of a random value
        # we immediately forget means password sign-in can never succeed for this
        # account until its owner sets one, without needing a nullable column.
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, location) VALUES (?, ?, ?, ?)",
            (name, email, hash_password(secrets.token_urlsafe(32)), None),
        )
        db.commit()
        user_id = cur.lastrowid

    # `signed_in` lets this tab claim the new account; without it the tab would
    # "reclaim" whichever account it had before and undo the sign-in.
    destination = next_page(db, user_id)
    redirect = RedirectResponse(url=f"{destination}?signed_in={user_id}", status_code=303)
    add_session(request, redirect, user_id, email)
    redirect.delete_cookie(google_oauth.STATE_COOKIE, path="/api/auth/google")
    return redirect
