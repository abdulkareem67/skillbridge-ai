import sqlite3

from fastapi import APIRouter, Depends

from .. import rate_limit
from ..auth import get_current_user_id
from ..database import get_db
from ..models import ChatRequest
from ..skills_engine import analyze_gap, chatbot_reply

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


@router.post("/message")
def send_message(payload: ChatRequest, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    rate_limit.guard_user_action(db, "advisor", user_id, rate_limit.ADVISOR_MESSAGES_PER_USER, "messages")
    user = db.execute("SELECT target_role, location FROM users WHERE id = ?", (user_id,)).fetchone()
    rows = db.execute("SELECT skill_name FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    user_skills = [r["skill_name"] for r in rows]
    role = user["target_role"] if user else None
    gap = analyze_gap(user_skills, role) if role else None

    reply = chatbot_reply(payload.message, user_skills, role, gap, user["location"] if user else None)

    db.execute("INSERT INTO chat_history (user_id, role, message) VALUES (?, 'user', ?)", (user_id, payload.message))
    db.execute("INSERT INTO chat_history (user_id, role, message) VALUES (?, 'assistant', ?)", (user_id, reply))
    db.commit()
    return {"reply": reply}


@router.get("/history")
def history(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT role, message, created_at FROM chat_history WHERE user_id = ? ORDER BY id ASC", (user_id,)
    ).fetchall()
    return {"history": [dict(r) for r in rows]}


@router.delete("/history")
def clear_history(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    """Delete this user's advisor conversation for good."""
    db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    db.commit()
    return {"ok": True}
