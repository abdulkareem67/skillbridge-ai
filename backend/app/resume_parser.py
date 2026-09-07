import io
import re

from pypdf import PdfReader
from docx import Document

from .skills_data import SKILL_DICTIONARY


def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if lower.endswith(".docx"):
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def extract_skills_from_text(text: str) -> list[dict]:
    """Match resume text against the skill dictionary and return categorized hits."""
    lowered = text.lower()
    found = []
    for canonical, (category, aliases) in SKILL_DICTIONARY.items():
        for alias in aliases:
            pattern = r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])"
            if re.search(pattern, lowered):
                found.append({"skill_name": canonical, "category": category})
                break
    return found
