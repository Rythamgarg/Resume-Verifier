"""
ATS keyword matching and scoring engine.

Extracts meaningful keywords from a job description and computes a
deterministic match score against the resume text.
"""

import re

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Ensure required NLTK data is available
for _res in ("punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger",
             "averaged_perceptron_tagger_eng"):
    try:
        nltk.data.find(f"tokenizers/{_res}" if "punkt" in _res else f"taggers/{_res}"
                       if "tagger" in _res else f"corpora/{_res}")
    except LookupError:
        nltk.download(_res, quiet=True)

# Additional domain-agnostic filler words to ignore
_EXTRA_STOP = {
    "experience", "ability", "including", "strong", "work", "working",
    "using", "understanding", "knowledge", "skills", "role", "team",
    "etc", "e.g", "must", "also", "well", "years", "year",
    "preferred", "required", "requirements", "responsibilities",
    "qualifications", "description", "job", "position", "candidate",
}


def _get_stop_words() -> set[str]:
    stops = set(stopwords.words("english"))
    stops.update(_EXTRA_STOP)
    return stops


def extract_keywords(text: str, top_n: int = 50) -> list[str]:
    """Extract the most relevant keywords from *text*.

    Strategy:
      1. Tokenize and POS-tag.
      2. Keep nouns (NN*), adjectives (JJ*), and foreign words (FW).
      3. Filter out stop words and very short tokens.
      4. Return unique keywords ordered by first appearance, capped at *top_n*.
    """
    stops = _get_stop_words()
    tokens = word_tokenize(text.lower())
    tagged = nltk.pos_tag(tokens)

    seen: set[str] = set()
    keywords: list[str] = []
    keep_tags = {"NN", "NNS", "NNP", "NNPS", "JJ", "JJR", "JJS", "FW"}

    for word, tag in tagged:
        # Keep only alphabetic tokens (allows hyphens inside words)
        cleaned = re.sub(r"[^a-z\-]", "", word)
        if len(cleaned) < 3 or cleaned in stops or tag not in keep_tags:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            keywords.append(cleaned)
        if len(keywords) >= top_n:
            break

    return keywords


def compute_ats_score(resume_text: str, jd_keywords: list[str]) -> dict:
    """Compute an ATS match score.

    Args:
        resume_text: Cleaned resume text.
        jd_keywords: Keywords extracted from the job description.

    Returns:
        A dict with keys ``score`` (int 0-100), ``matched`` (list),
        and ``missing`` (list).
    """
    if not jd_keywords:
        return {"score": 0, "matched": [], "missing": []}

    resume_lower = resume_text.lower()

    matched = [kw for kw in jd_keywords if kw in resume_lower]
    missing = [kw for kw in jd_keywords if kw not in resume_lower]

    score = round(len(matched) / len(jd_keywords) * 100)
    return {"score": score, "matched": matched, "missing": missing}
