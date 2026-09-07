import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user_id
from ..database import get_db
from ..models import ProgressUpdateRequest
from ..skills_data import get_disciplines, get_role_names, is_valid_role
from ..skills_engine import analyze_gap, build_roadmap, categorize_all, recommend_certifications, resume_tips

router = APIRouter(prefix="/api/skills", tags=["skills"])


def _user_skill_names(db: sqlite3.Connection, user_id: int) -> list[str]:
    rows = db.execute("SELECT skill_name FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    return [r["skill_name"] for r in rows]


@router.get("/roles")
def list_roles():
    return {"roles": get_role_names()}


@router.get("/disciplines")
def list_disciplines():
    """Roles grouped by field of study, so the UI can offer a discipline picker."""
    return {"disciplines": get_disciplines()}


@router.get("/categorized")
def categorized(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT skill_name, category FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    return categorize_all([dict(r) for r in rows])


@router.get("/gap-analysis")
def gap_analysis(role: str | None = None, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    target = role or (user["target_role"] if user else None)
    if not target:
        raise HTTPException(status_code=400, detail="No target role set. Choose a role first.")
    if not is_valid_role(target):
        raise HTTPException(status_code=400, detail="Unknown role. Choose one of the supported career tracks.")
    user_skills = _user_skill_names(db, user_id)
    return analyze_gap(user_skills, target)


@router.get("/roadmap")
def roadmap(role: str | None = None, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    target = role or (user["target_role"] if user else None)
    if not target:
        raise HTTPException(status_code=400, detail="No target role set. Choose a role first.")
    if not is_valid_role(target):
        raise HTTPException(status_code=400, detail="Unknown role. Choose one of the supported career tracks.")
    user_skills = _user_skill_names(db, user_id)
    return {"role": target, "roadmap": build_roadmap(user_skills, target)}


@router.get("/progress")
def get_progress(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT skill_name, status FROM skill_progress WHERE user_id = ?", (user_id,)).fetchall()
    return {r["skill_name"]: r["status"] for r in rows}


@router.post("/progress")
def update_progress(payload: ProgressUpdateRequest, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    db.execute(
        """INSERT INTO skill_progress (user_id, skill_name, status) VALUES (?, ?, ?)
           ON CONFLICT(user_id, skill_name) DO UPDATE SET status = excluded.status""",
        (user_id, payload.skill_name, payload.status),
    )
    db.commit()
    return {"skill_name": payload.skill_name, "status": payload.status}


@router.get("/resume-tips")
def get_resume_tips(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT skill_name, category FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    categorized = categorize_all([dict(r) for r in rows])
    user = db.execute("SELECT target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    gap = None
    if user and user["target_role"]:
        gap = analyze_gap(_user_skill_names(db, user_id), user["target_role"])
    return {"tips": resume_tips(categorized, gap)}


@router.get("/certifications")
def get_certifications(role: str | None = None, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    target = role or (user["target_role"] if user else None)
    return {"role": target, "certifications": recommend_certifications(target)}
