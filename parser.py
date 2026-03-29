"""
Resume and job description parsing utilities.

Handles PDF text extraction and text normalization for downstream analysis.
"""

import re

from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract and clean text from an uploaded PDF file.

    Args:
        uploaded_file: A file-like object (e.g., Streamlit UploadedFile).

    Returns:
        Cleaned text string, or empty string if extraction fails.
    """
    try:
        reader = PdfReader(uploaded_file)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return normalize_text("\n".join(pages))
    except Exception:
        return ""


def normalize_text(text: str) -> str:
    """Normalize text by collapsing whitespace and stripping edges."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_bullets(resume_text: str) -> list[str]:
    """Extract bullet points from resume text.

    Detects lines that start with common bullet markers (-, *, •, ▪, ►)
    as well as lines that begin with a strong action verb (heuristic for
    experience-section bullets that lack an explicit marker).

    Returns:
        A list of bullet-point strings.
    """
    bullets: list[str] = []

    # Common action verbs that typically start experience bullets
    action_verbs = {
        "achieved", "administered", "analyzed", "automated", "built",
        "conducted", "contributed", "coordinated", "created", "delivered",
        "designed", "developed", "directed", "drove", "enabled", "engineered",
        "established", "evaluated", "executed", "expanded", "facilitated",
        "generated", "grew", "guided", "identified", "implemented", "improved",
        "increased", "influenced", "initiated", "integrated", "launched", "led",
        "leveraged", "managed", "mentored", "modeled", "negotiated", "optimized",
        "orchestrated", "oversaw", "partnered", "performed", "planned",
        "presented", "produced", "provided", "published", "recommended",
        "reduced", "researched", "resolved", "revamped", "secured",
        "spearheaded", "streamlined", "strengthened", "supported", "trained",
        "transformed", "utilized",
    }

    for line in resume_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Lines with explicit bullet markers
        if re.match(r"^[-*•▪►]\s+", stripped):
            bullets.append(re.sub(r"^[-*•▪►]\s+", "", stripped))
            continue

        # Lines starting with an action verb (likely experience bullets)
        first_word = stripped.split()[0].lower().rstrip(",;:")
        if first_word in action_verbs and len(stripped) > 20:
            bullets.append(stripped)

    return bullets
