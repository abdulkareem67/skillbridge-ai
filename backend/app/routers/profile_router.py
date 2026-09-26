import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Path, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .. import rate_limit
from ..auth import clear_all_sessions, get_current_user_id, remove_session
from ..database import get_db
from ..models import DeleteAccountRequest, LocationRequest, ManualSkillsRequest, TargetRoleRequest
from ..resume_parser import extract_skills_from_text, extract_text
from ..skills_data import SKILL_DICTIONARY, get_role_names

router = APIRouter(prefix="/api/profile", tags=["profile"])

MAX_CV_SIZE_BYTES = 5 * 1024 * 1024


@router.get("/me")
def me(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT id, name, email, location, target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    skills = db.execute("SELECT skill_name, category, source FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "location": user["location"],
        "target_role": user["target_role"],
        "skills": [dict(s) for s in skills],
    }


@router.post("/cv-upload")
async def upload_cv(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db),
):
    rate_limit.guard_user_action(db, "cv-upload", user_id, rate_limit.CV_UPLOADS_PER_USER, "CV uploads")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    chunks = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > MAX_CV_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")
        chunks.append(chunk)
    content = b"".join(chunks)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    try:
        text = extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    extracted = extract_skills_from_text(text)
    db.execute("DELETE FROM skills WHERE user_id = ? AND source = 'cv'", (user_id,))
    for item in extracted:
        db.execute(
            "INSERT OR IGNORE INTO skills (user_id, skill_name, category, source) VALUES (?, ?, ?, 'cv')",
            (user_id, item["skill_name"], item["category"]),
        )
    db.commit()
    return {"extracted_count": len(extracted), "skills": extracted}


@router.post("/skills/manual")
def add_manual_skills(
    payload: ManualSkillsRequest,
    user_id: int = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db),
):
    added = []
    for raw in payload.skills:
        name = raw.strip()
        if not name:
            continue
        category = "technical"
        for canonical, (cat, aliases) in SKILL_DICTIONARY.items():
            if name.lower() == canonical.lower() or name.lower() in aliases:
                name, category = canonical, cat
                break
        db.execute(
            "INSERT OR IGNORE INTO skills (user_id, skill_name, category, source) VALUES (?, ?, ?, 'manual')",
            (user_id, name, category),
        )
        added.append(name)
    db.commit()
    return {"added": added}


@router.delete("/skills/{skill_name}")
def remove_skill(skill_name: str = Path(max_length=80), user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM skills WHERE user_id = ? AND skill_name = ?", (user_id, skill_name))
    db.commit()
    return {"ok": True}


@router.delete("/skills")
def clear_all_skills(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM skills WHERE user_id = ?", (user_id,))
    db.commit()
    return {"ok": True}


@router.post("/target-role")
def set_target_role(payload: TargetRoleRequest, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    if payload.role not in get_role_names():
        raise HTTPException(status_code=400, detail="Unknown role. Choose one of the supported career tracks.")
    db.execute("UPDATE users SET target_role = ? WHERE id = ?", (payload.role, user_id))
    db.commit()
    return {"target_role": payload.role}


@router.post("/location")
def set_location(payload: LocationRequest, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE users SET location = ? WHERE id = ?", (payload.location, user_id))
    db.commit()
    return {"location": payload.location}


@router.get("/export")
def export_my_data(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    """Everything we hold about this account, as a JSON file they can download.

    The GDPR right to data portability, and also just a decent thing to offer.
    Passwords are excluded: we only ever store a one-way hash, so it is neither
    portable nor safe to hand back.
    """
    user = db.execute(
        "SELECT name, email, location, target_role, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    skills = db.execute("SELECT skill_name, category, source FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    progress = db.execute("SELECT skill_name, status FROM skill_progress WHERE user_id = ?", (user_id,)).fetchall()
    chats = db.execute(
        "SELECT role, message, created_at FROM chat_history WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()

    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "account": {k: user[k] for k in ("name", "email", "location", "target_role", "created_at")},
        "skills": [dict(s) for s in skills],
        "progress": [dict(p) for p in progress],
        "advisor_messages": [dict(c) for c in chats],
    }
    # jsonable_encoder, not the raw dict: Postgres hands timestamps back as
    # datetime objects (SQLite gives strings), which json.dumps can't encode.
    return JSONResponse(
        content=jsonable_encoder(data),
        headers={"Content-Disposition": 'attachment; filename="skillbridge-my-data.json"'},
    )


@router.post("/delete")
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    response: Response,
    user_id: int = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db),
):
    """Delete the account and everything attached to it, for good.

    The foreign keys cascade, so removing the user row also removes their skills,
    progress and advisor history. Then this account is signed out of the browser.
    """
    user = db.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.confirm_email.strip().lower() != user["email"].strip().lower():
        raise HTTPException(status_code=400, detail="The email you typed doesn't match this account.")

    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    # Drop just this account from the browser's session list; any other accounts
    # signed in here stay signed in.
    if remove_session(request, response, user_id) is None:
        clear_all_sessions(response)
    return {"ok": True}
