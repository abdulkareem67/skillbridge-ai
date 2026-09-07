import sqlite3
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from ..auth import (
    add_session,
    clear_all_sessions,
    get_active_session,
    hash_password,
    remove_session,
    switch_active_session,
    verify_password,
)
from ..database import get_db
from ..models import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, request: Request, response: Response, db: sqlite3.Connection = Depends(get_db)):
    existing = db.execute("SELECT id FROM users WHERE email = ?", (payload.email,)).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    cur = db.execute(
        "INSERT INTO users (name, email, password_hash, location) VALUES (?, ?, ?, ?)",
        (payload.name, payload.email, hash_password(payload.password), payload.location),
    )
    db.commit()
    user_id = cur.lastrowid
    add_session(request, response, user_id, payload.email)
    return {"id": user_id, "name": payload.name, "email": payload.email}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    add_session(request, response, user["id"], user["email"])
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


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
