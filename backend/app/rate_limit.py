"""Throttling for sign-in and sign-up.

Counts live in the database, not in memory. On a serverless host every instance
has its own memory and new ones start constantly, so an in-process counter would
reset whenever traffic moved to a fresh instance — an attacker would simply get a
new allowance. The table is shared by all of them.

Attempts are grouped into buckets. A failed sign-in counts against both the
email it targeted and the address it came from:

- per email, so one account can't be guessed at from many addresses;
- per IP, so one address can't sweep through many accounts.

The IP limits are deliberately loose. Students often share a single public
address across a whole campus or computer lab, and a tight per-IP limit would
lock out a classroom because one person mistyped their password.
"""
import hashlib
import time

from fastapi import HTTPException, Request

WINDOW_SECONDS = 15 * 60

# Failed sign-ins before a pause.
LOGIN_PER_EMAIL = 5
LOGIN_PER_IP = 50
# Accounts created from one address in a window.
REGISTER_PER_IP = 30

# Per-user throttles on the heavier authenticated endpoints, so one signed-in
# account can't hammer CV parsing or the advisor. Counted per user id, which is
# already an opaque number, not personal data.
CV_UPLOADS_PER_USER = 20
ADVISOR_MESSAGES_PER_USER = 40


def client_ip(request: Request) -> str:
    """The caller's address. On Vercel the platform sets x-forwarded-for."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


def _digest(value: str) -> str:
    # Buckets are hashed so this table never holds a readable list of the email
    # addresses people have tried to sign in with.
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:32]


def email_bucket(email: str) -> str:
    return "login-email:" + _digest(email)


def user_bucket(action: str, user_id: int) -> str:
    return f"{action}-user:{user_id}"


def guard_user_action(db, action: str, user_id: int, limit: int, what: str) -> None:
    """Enforce and then record one use of a per-user endpoint, in one call."""
    bucket = user_bucket(action, user_id)
    enforce(db, [(bucket, limit)], what)
    record(db, bucket)
    db.commit()


def ip_bucket(action: str, request: Request) -> str:
    return f"{action}-ip:" + _digest(client_ip(request))


def seconds_until_allowed(db, limits: list[tuple[str, int]]) -> int:
    """0 if every bucket is under its limit, otherwise how long to wait."""
    now = int(time.time())
    since = now - WINDOW_SECONDS
    wait = 0
    for bucket, limit in limits:
        rows = db.execute(
            "SELECT attempted_at FROM login_attempts WHERE bucket = ? AND attempted_at > ? ORDER BY attempted_at",
            (bucket, since),
        ).fetchall()
        if len(rows) >= limit:
            # The count drops back under the limit once this attempt ages out.
            unlock_at = rows[len(rows) - limit]["attempted_at"] + WINDOW_SECONDS
            wait = max(wait, unlock_at - now)
    return max(wait, 0)


def enforce(db, limits: list[tuple[str, int]], what: str) -> None:
    """Raise 429 with Retry-After if any bucket is over its limit."""
    wait = seconds_until_allowed(db, limits)
    if wait:
        minutes = max(1, -(-wait // 60))  # round up: "try again in 0 minutes" helps nobody
        raise HTTPException(
            status_code=429,
            detail=f"Too many {what}. Please wait {minutes} minute{'s' if minutes != 1 else ''} and try again.",
            headers={"Retry-After": str(wait)},
        )


def record(db, *buckets: str) -> None:
    now = int(time.time())
    for bucket in buckets:
        db.execute("INSERT INTO login_attempts (bucket, attempted_at) VALUES (?, ?)", (bucket, now))
    # Anything outside the window can never count again, so drop it. Cheap: the
    # table only ever holds the last fifteen minutes of failures.
    db.execute("DELETE FROM login_attempts WHERE attempted_at <= ?", (now - WINDOW_SECONDS,))


def clear(db, bucket: str) -> None:
    db.execute("DELETE FROM login_attempts WHERE bucket = ?", (bucket,))
