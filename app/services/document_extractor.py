import base64
import json
import re
from pathlib import Path

from app.config import settings
from app.services.documents import save_document
from app.services.profile_extended import patch_profile


def _upload_dir(plan_id: int) -> Path:
    path = settings.upload_dir / str(plan_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _extract_text(content: bytes, filename: str, mime_type: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf") or mime_type == "application/pdf":
        try:
            import pdfplumber
            import io

            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        except Exception:
            return content.decode("utf-8", errors="ignore")
    if lower.endswith(".docx"):
        try:
            import io
            from docx import Document

            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return content.decode("utf-8", errors="ignore")
    return content.decode("utf-8", errors="ignore")


def _build_outline(doc_type: str, text: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    sections = []
    key_skills = []
    for ln in lines[:80]:
        if re.match(r"^(education|experience|skills|projects|research|work|summary)", ln, re.I):
            sections.append(ln)
        if re.search(r"\b(python|java|react|sql|machine learning|ai|data)\b", ln, re.I):
            key_skills.append(ln[:80])
    years = 0
    month_match = re.findall(r"(\d+)\s*(?:years?|yrs?)", text, re.I)
    if month_match:
        years = max(int(m) for m in month_match)
    return {
        "doc_type": doc_type,
        "sections": sections[:12] or ["Education", "Skills", "Experience"],
        "key_skills": list(dict.fromkeys(key_skills))[:10],
        "years_experience": years,
        "line_count": len(lines),
    }


def analyze_and_store(
    plan_id: int,
    doc_type: str,
    content_b64: str,
    filename: str,
    mime_type: str = "application/pdf",
) -> dict:
    raw = base64.b64decode(content_b64)
    upload_path = _upload_dir(plan_id) / filename
    upload_path.write_bytes(raw)

    text = _extract_text(raw, filename, mime_type)
    outline = _build_outline(doc_type, text)

    save_document(plan_id, doc_type, text[:50000], format="raw", target_university=None)

    if doc_type == "resume":
        patch_profile(plan_id, resume_outline_json=outline)
    elif doc_type == "transcript":
        patch_profile(plan_id, transcript_outline_json=outline)

    return {
        "status": "analyzed",
        "outline": outline,
        "stored_path": str(upload_path),
        "message": f"{doc_type.title()} processed. Continue to next stage.",
    }
