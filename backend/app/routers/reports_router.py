import io
import re
import sqlite3
from urllib.parse import quote
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..auth import get_current_user_id
from ..database import get_db
from ..skills_data import is_valid_role
from ..skills_engine import analyze_gap, build_roadmap, categorize_all, generate_improved_cv

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _para(text, style) -> Paragraph:
    """A Paragraph of plain text.

    ReportLab reads Paragraph text as markup, so a name like "Ali <b" or a skill
    containing "&" broke the PDF with a 500. Everything we put on the page is
    data, never formatting, so it is always escaped.
    """
    return Paragraph(escape(str(text)), style)


def _download_headers(stem: str) -> dict:
    """Content-Disposition that works for any name.

    HTTP headers are Latin-1, so an Urdu or Arabic name in the filename raised
    UnicodeEncodeError and the download failed. Browsers read the UTF-8
    `filename*` form; the plain `filename` is an ASCII-only fallback.
    """
    ascii_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_") or "SkillBridge"
    utf8_name = quote(stem.replace("/", "-") + ".pdf", safe="")
    return {"Content-Disposition": f"attachment; filename=\"{ascii_stem}.pdf\"; filename*=UTF-8''{utf8_name}"}


def _load_cv_context(db: sqlite3.Connection, user_id: int):
    user = db.execute("SELECT name, target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    rows = db.execute("SELECT skill_name, category FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    categorized = categorize_all([dict(r) for r in rows])
    user_skills = [r["skill_name"] for r in rows]
    gap = analyze_gap(user_skills, user["target_role"]) if user and user["target_role"] else None
    cv = generate_improved_cv(user["name"] if user else "", categorized, user["target_role"] if user else None, gap)
    return user, cv


@router.get("/improved-cv")
def improved_cv_preview(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user, cv = _load_cv_context(db, user_id)
    return {"name": user["name"] if user else "", "target_role": user["target_role"] if user else None, "cv": cv}


@router.get("/improved-cv-pdf")
def improved_cv_pdf(user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user, cv = _load_cv_context(db, user_id)
    name = user["name"] if user else "Candidate"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(_para(name, styles["Title"]))
    if user and user["target_role"]:
        story.append(_para(f"Target Role: {user['target_role']}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(_para("Professional Summary", styles["Heading2"]))
    story.append(_para(cv["summary"], styles["Normal"]))
    story.append(Spacer(1, 12))

    def skill_section(title, items):
        if not items:
            return
        story.append(_para(title, styles["Heading2"]))
        story.append(_para(", ".join(items), styles["Normal"]))
        story.append(Spacer(1, 10))

    skill_section("Technical Skills", cv["technical_skills"])
    skill_section("Tools & Technologies", cv["tools"])
    skill_section("Soft Skills", cv["soft_skills"])
    skill_section("Certifications", cv["certifications"])

    if cv["project_suggestions"]:
        story.append(_para("Suggested Projects to Add", styles["Heading2"]))
        for tip in cv["project_suggestions"]:
            story.append(_para(f"- {tip}", styles["Normal"]))
        story.append(Spacer(1, 10))

    story.append(_para("AI Recommendations to Strengthen This CV", styles["Heading2"]))
    for tip in cv["recommendations"]:
        story.append(_para(f"- {tip}", styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers=_download_headers(f"SkillBridge_Improved_CV_{name.replace(' ', '_')}"),
    )


@router.get("/roadmap-pdf")
def roadmap_pdf(role: str | None = Query(default=None, max_length=100), user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT name, target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    target = role or (user["target_role"] if user else None)
    if not target:
        raise HTTPException(status_code=400, detail="No target role set")
    if not is_valid_role(target):
        raise HTTPException(status_code=400, detail="Unknown role. Choose one of the supported career tracks.")

    rows = db.execute("SELECT skill_name FROM skills WHERE user_id = ?", (user_id,)).fetchall()
    user_skills = [r["skill_name"] for r in rows]

    gap = analyze_gap(user_skills, target)
    roadmap = build_roadmap(user_skills, target)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(_para("SkillBridge AI — Career Roadmap Report", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(_para(f"Candidate: {user['name'] if user else ''}", styles["Normal"]))
    story.append(_para(f"Target Role: {target}", styles["Normal"]))
    story.append(_para(f"Skill Match Score: {gap['match_percent']}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(_para("Skill Gap Analysis", styles["Heading2"]))
    data = [["Matched Skills", "Missing Skills"]]
    max_len = max(len(gap["matched_skills"]), len(gap["missing_skills"]), 1)
    matched, missing = gap["matched_skills"], gap["missing_skills"]
    for i in range(max_len):
        data.append([
            matched[i] if i < len(matched) else "",
            missing[i] if i < len(missing) else "",
        ])
    table = Table(data, colWidths=[8 * cm, 8 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    story.append(_para("Learning Roadmap", styles["Heading2"]))
    course_style = ParagraphStyle("course", parent=styles["Normal"], leftIndent=14)
    for phase_name in ("beginner", "intermediate", "advanced"):
        phase = roadmap[phase_name]
        story.append(_para(f"{phase_name.capitalize()} Phase ({phase['duration']})", styles["Heading3"]))
        for topic in phase["topics"]:
            status = "(already have)" if topic["already_have"] else ""
            story.append(_para(f"- {topic['skill']} {status}", styles["Normal"]))
            story.append(_para(f"Course: {topic['resource']['course']}", course_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers=_download_headers(f"SkillBridge_Roadmap_{target.replace(' ', '_')}"),
    )
