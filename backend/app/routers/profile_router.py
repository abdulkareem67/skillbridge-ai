import sqlite3

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import get_current_user_id
from ..database import get_db
from ..models import ManualSkillsRequest, TargetRoleRequest
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
        raise HTTPException(status_code=400, detail=str(e))

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
def remove_skill(skill_name: str, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
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
