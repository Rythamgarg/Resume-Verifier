"""
Resume and job description text extraction.

Handles PDF parsing via pdfplumber with robust error handling for
edge cases like scanned/image-based PDFs, empty pages, and
malformed formatting.
"""

import re

import pdfplumber


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract and clean text from an uploaded PDF file.

    Args:
        uploaded_file: A file-like object (Streamlit UploadedFile or similar).

    Returns:
        Cleaned text string.

    Raises:
        ValueError: If the PDF appears to be image-based or yields no text.
    """
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            if not pdf.pages:
                raise ValueError("The uploaded PDF has no pages.")

            pages: list[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

            if not pages:
                raise ValueError(
                    "This PDF appears to be image-based. "
                    "Please upload a text-based PDF."
                )

            return clean_text("\n".join(pages))

    except ValueError:
        raise  # re-raise our own errors
    except Exception as exc:
        raise ValueError(f"Could not read the PDF: {exc}") from exc


def clean_text(text: str) -> str:
    """Normalize whitespace and strip artefacts while keeping bullets and numbers."""
    # Collapse runs of spaces/tabs (but not newlines)
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove non-printable characters except common whitespace
    text = re.sub(r"[^\S \n]+", " ", text)
    return text.strip()


def extract_bullets(resume_text: str) -> list[str]:
    """Extract bullet-point lines from resume text.

    Detects lines starting with common bullet markers (•, -, ▪, ►, ●, ○)
    as well as lines beginning with a strong action verb (heuristic).

    Returns:
        List of bullet-point strings with markers removed.
    """
    _ACTION_VERBS = {
        "accelerated", "achieved", "administered", "analyzed", "architected",
        "automated", "built", "championed", "coached", "conducted",
        "consolidated", "coordinated", "created", "decreased", "delivered",
        "designed", "developed", "directed", "drove", "enabled", "engineered",
        "established", "evaluated", "executed", "expanded", "facilitated",
        "founded", "generated", "grew", "guided", "identified", "implemented",
        "improved", "increased", "influenced", "initiated", "integrated",
        "launched", "led", "leveraged", "managed", "mentored", "migrated",
        "modeled", "negotiated", "optimized", "orchestrated", "oversaw",
        "partnered", "performed", "pioneered", "planned", "presented",
        "produced", "proposed", "provided", "published", "recommended",
        "redesigned", "reduced", "refactored", "researched", "resolved",
        "restructured", "revamped", "scaled", "secured", "shipped",
        "simplified", "spearheaded", "standardized", "streamlined",
        "strengthened", "supervised", "supported", "trained", "transformed",
        "tripled", "utilized",
    }

    bullet_re = re.compile(r"^[\-\*•▪►●○◦‣⁃]\s*")
    bullets: list[str] = []

    for line in resume_text.split("\n"):
        stripped = line.strip()
        if not stripped or len(stripped) < 15:
            continue

        # Explicit bullet marker
        if bullet_re.match(stripped):
            cleaned = bullet_re.sub("", stripped).strip()
            if cleaned:
                bullets.append(cleaned)
            continue

        # Heuristic: line starts with an action verb
        first_word = stripped.split()[0].lower().rstrip(".,;:")
        if first_word in _ACTION_VERBS and len(stripped) > 20:
            bullets.append(stripped)

    return bullets
