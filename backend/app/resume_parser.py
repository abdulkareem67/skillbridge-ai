"""Pull text out of an uploaded CV, then match it against the skill dictionary.

The goal is to fail *informatively*. A CV that is a scanned image, is password
protected, or is genuinely empty each needs a different thing from the person, so
each raises a distinct message rather than silently returning nothing — which
used to surface as a confusing "0 skills found".
"""
import io
import re

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .skills_data import SKILL_DICTIONARY

# Below this many characters we treat a PDF as having no real text layer — almost
# always a scan (an image of a page) rather than a document.
_MIN_MEANINGFUL_CHARS = 25


class CVParseError(ValueError):
    """A CV we understood the format of but couldn't get usable text from.

    Subclasses ValueError so existing 400 handling keeps working; the message is
    written to be shown straight to the person.
    """


def _read_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
    except (PdfReadError, OSError, ValueError) as exc:
        raise CVParseError("We couldn't open this PDF. It may be corrupted — try re-exporting it, or upload a DOCX.") from exc

    if reader.is_encrypted:
        # A blank owner password is common and lets us in; a real one does not.
        try:
            opened = reader.decrypt("")
        except Exception:
            opened = 0
        if not opened:
            raise CVParseError("This PDF is password-protected. Remove the password (or export a fresh copy) and upload it again.")

    parts = []
    for page in reader.pages:
        try:
            # "layout" keeps words in reading order on two-column CVs, so skills
            # in a side column aren't run into the main text as one blob.
            parts.append(page.extract_text(extraction_mode="layout") or "")
        except Exception:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
    text = "\n".join(parts)

    if len(text.strip()) < _MIN_MEANINGFUL_CHARS and len(reader.pages) > 0:
        raise CVParseError(
            "This looks like a scanned image with no selectable text, so we can't read the skills from it. "
            "Upload a DOCX, or a PDF exported from Word or Google Docs (where the text can be selected)."
        )
    return text


def _read_docx(content: bytes) -> str:
    try:
        doc = Document(io.BytesIO(content))
    except (PackageNotFoundError, KeyError, OSError, ValueError) as exc:
        raise CVParseError("We couldn't open this DOCX. Make sure it's a real Word file (not a renamed PDF) and try again.") from exc

    parts = [p.text for p in doc.paragraphs]
    # Many CVs lay skills out in a table; reading paragraphs only would miss them.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    parts.append(cell.text)

    text = "\n".join(parts)
    if not text.strip():
        raise CVParseError("We couldn't find any text in this document. If it's mostly images, add your skills manually instead.")
    return text


def extract_text(filename: str, content: bytes) -> str:
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        return _read_pdf(content)
    if lower.endswith(".docx"):
        return _read_docx(content)
    # .doc (old Word), .pages, images, etc. — we can't read these.
    raise CVParseError("That file type isn't supported. Please upload a PDF or DOCX file.")


# Aliases that are fine when someone types them as a skill ("rest" -> REST APIs)
# but are ordinary words or unrelated abbreviations in running CV text: "the
# rest of the team", "lean", "tax", "DL" (a driving licence). Matching them in
# prose invented skills the person never claimed.
_AMBIGUOUS_IN_PROSE = {
    "rest", "lean", "tax", "dl", "tf", "py", "od", "dynamics", "express",
    "spring", "automation", "comptia", "estimation",
}

# Acronyms that only mean the skill when written in capitals: "ML" is machine
# learning, "ml" is millilitres; "TS" is TypeScript.
_UPPERCASE_ONLY = {"ml", "ts"}


def extract_skills_from_text(text: str) -> list[dict]:
    """Match resume text against the skill dictionary and return categorized hits.

    The dictionary is English, so a CV written in another language will match few
    skills even when the text was read perfectly. The caller turns "text read,
    nothing matched" into advice to add skills manually.
    """
    lowered = text.lower()
    found = []
    for canonical, (category, aliases) in SKILL_DICTIONARY.items():
        for alias in aliases:
            alias = alias.lower()
            if alias in _AMBIGUOUS_IN_PROSE:
                continue
            if alias in _UPPERCASE_ONLY:
                hit = re.search(r"(?<![A-Za-z0-9])" + re.escape(alias.upper()) + r"(?![A-Za-z0-9])", text)
            else:
                hit = re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", lowered)
            if hit:
                found.append({"skill_name": canonical, "category": category})
                break
    return found
