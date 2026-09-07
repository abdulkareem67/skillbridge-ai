import io
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..auth import get_current_user_id
from ..database import get_db
from ..skills_data import is_valid_role
from ..skills_engine import analyze_gap, build_roadmap, categorize_all, generate_improved_cv

router = APIRouter(prefix="/api/reports", tags=["reports"])


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

    story.append(Paragraph(name, styles["Title"]))
    if user and user["target_role"]:
        story.append(Paragraph(f"Target Role: {user['target_role']}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Professional Summary", styles["Heading2"]))
    story.append(Paragraph(cv["summary"], styles["Normal"]))
    story.append(Spacer(1, 12))

    def skill_section(title, items):
        if not items:
            return
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(", ".join(items), styles["Normal"]))
        story.append(Spacer(1, 10))

    skill_section("Technical Skills", cv["technical_skills"])
    skill_section("Tools & Technologies", cv["tools"])
    skill_section("Soft Skills", cv["soft_skills"])
    skill_section("Certifications", cv["certifications"])

    if cv["project_suggestions"]:
        story.append(Paragraph("Suggested Projects to Add", styles["Heading2"]))
        for tip in cv["project_suggestions"]:
            story.append(Paragraph(f"- {tip}", styles["Normal"]))
        story.append(Spacer(1, 10))

    story.append(Paragraph("AI Recommendations to Strengthen This CV", styles["Heading2"]))
    for tip in cv["recommendations"]:
        story.append(Paragraph(f"- {tip}", styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SkillBridge_Improved_CV_{name.replace(' ', '_')}.pdf"},
    )


@router.get("/roadmap-pdf")
def roadmap_pdf(role: str | None = None, user_id: int = Depends(get_current_user_id), db: sqlite3.Connection = Depends(get_db)):
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

    story.append(Paragraph("SkillBridge AI — Career Roadmap Report", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Candidate: {user['name'] if user else ''}", styles["Normal"]))
    story.append(Paragraph(f"Target Role: {target}", styles["Normal"]))
    story.append(Paragraph(f"Skill Match Score: {gap['match_percent']}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Skill Gap Analysis", styles["Heading2"]))
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

    story.append(Paragraph("Learning Roadmap", styles["Heading2"]))
    for phase_name in ("beginner", "intermediate", "advanced"):
        phase = roadmap[phase_name]
        story.append(Paragraph(f"{phase_name.capitalize()} Phase ({phase['duration']})", styles["Heading3"]))
        for topic in phase["topics"]:
            status = "(already have)" if topic["already_have"] else ""
            story.append(Paragraph(f"- {topic['skill']} {status}", styles["Normal"]))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;Course: {topic['resource']['course']}", styles["Normal"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SkillBridge_Roadmap_{target.replace(' ', '_')}.pdf"},
    )
