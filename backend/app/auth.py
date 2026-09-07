import json
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status

SECRET_KEY = os.environ.get("SKILLBRIDGE_SECRET", "skillbridge-ai-dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7
TOKEN_MAX_AGE_SECONDS = 60 * 60 * TOKEN_EXPIRE_HOURS
SECURE_COOKIES = os.environ.get("SKILLBRIDGE_SECURE_COOKIES", "false").lower() == "true"

# Every account logged into this browser lives in one cookie, keyed by user id,
# so a second login doesn't sign the first account out. ACTIVE_COOKIE just
# points at which one the current tab should use.
SESSIONS_COOKIE = "sessions"
ACTIVE_COOKIE = "active_uid"
MAX_ACCOUNTS = 5


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")


def _read_raw_sessions(request: Request) -> list[dict]:
    raw = request.cookies.get(SESSIONS_COOKIE)
    if not raw:
        return []
    try:
        sessions = json.loads(raw)
    except ValueError:
        return []
    return sessions if isinstance(sessions, list) else []


def _write_sessions(response: Response, sessions: list[dict]) -> None:
    response.set_cookie(
        SESSIONS_COOKIE,
        json.dumps(sessions),
        httponly=True,
        samesite="lax",
        secure=SECURE_COOKIES,
        max_age=TOKEN_MAX_AGE_SECONDS,
    )


def _set_active_cookie(response: Response, user_id: int) -> None:
    # Not httponly: a small bit of page JS reads this to notice when another
    # tab switched the active account and reclaim this tab's own account.
    response.set_cookie(
        ACTIVE_COOKIE,
        str(user_id),
        httponly=False,
        samesite="lax",
        secure=SECURE_COOKIES,
        max_age=TOKEN_MAX_AGE_SECONDS,
    )


def add_session(request: Request, response: Response, user_id: int, email: str) -> str:
    """Log this account into the browser's session list without signing out any others already there."""
    token = create_token(user_id, email)
    sessions = [s for s in _read_raw_sessions(request) if s.get("uid") != user_id]
    sessions.append({"uid": user_id, "email": email, "token": token})
    sessions = sessions[-MAX_ACCOUNTS:]
    _write_sessions(response, sessions)
    _set_active_cookie(response, user_id)
    return token


def list_sessions(request: Request) -> list[dict]:
    """Accounts currently logged into this browser, dropping any with an expired token."""
    valid = []
    for s in _read_raw_sessions(request):
        try:
            decode_token(s.get("token", ""))
        except HTTPException:
            continue
        valid.append(s)
    return valid


def get_active_session(request: Request) -> dict | None:
    sessions = list_sessions(request)
    if not sessions:
        return None
    active = request.cookies.get(ACTIVE_COOKIE)
    for s in sessions:
        if str(s["uid"]) == active:
            return s
    return sessions[0]


def switch_active_session(request: Request, response: Response, user_id: int) -> bool:
    """Point this tab's active-account cookie at an account already logged into the browser."""
    if not any(s["uid"] == user_id for s in list_sessions(request)):
        return False
    _set_active_cookie(response, user_id)
    return True


def remove_session(request: Request, response: Response, user_id: int) -> dict | None:
    """Sign one account out of this browser. Returns the account that's now active, if any remain."""
    sessions = [s for s in _read_raw_sessions(request) if s.get("uid") != user_id]
    _write_sessions(response, sessions)
    if not sessions:
        response.delete_cookie(SESSIONS_COOKIE)
        response.delete_cookie(ACTIVE_COOKIE)
        return None
    new_active = sessions[-1]
    _set_active_cookie(response, new_active["uid"])
    return new_active


def clear_all_sessions(response: Response) -> None:
    response.delete_cookie(SESSIONS_COOKIE)
    response.delete_cookie(ACTIVE_COOKIE)


def get_current_user_id(request: Request) -> int:
    session = get_active_session(request)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return int(session["uid"])
