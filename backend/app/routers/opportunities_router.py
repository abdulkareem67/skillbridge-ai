import sqlite3

from fastapi import APIRouter, Depends

from ..auth import get_current_user_id
from ..database import get_db
from ..skills_data import get_fields
from ..skills_engine import application_strategy, match_opportunities

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


def _matched(db: sqlite3.Connection, user_id: int, include_other_fields: bool = False):
    user = db.execute("SELECT location, target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    rows = db.execute("SELECT skill_name FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    user_skills = [r["skill_name"] for r in rows]
    location = user["location"] if user else None
    target_role = user["target_role"] if user else None
    return match_opportunities(user_skills, location, target_role, include_other_fields)


@router.get("/fields")
def fields():
    return {"fields": get_fields()}


@router.get("")
def opportunities(
    include_other_fields: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db),
):
    return {"opportunities": _matched(db, user_id, include_other_fields)}


@router.get("/application-guide")
def application_guide(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    matched = _matched(db, user_id)
    return application_strategy(matched)
