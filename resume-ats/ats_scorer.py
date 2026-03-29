"""
Deterministic ATS scoring engine.

Computes a weighted ATS score (0-100) from four components:
  1. Keyword Match      (40%) — TF-IDF cosine similarity + exact phrase matching
  2. Section Structure   (20%) — presence of standard resume sections
  3. Quantification      (20%) — ratio of quantified bullet points
  4. Skills Alignment    (20%) — overlap with a predefined skills taxonomy
"""

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Skills taxonomy used for component 4
# ---------------------------------------------------------------------------
SKILLS_TAXONOMY: list[str] = [
    "Python", "SQL", "Excel", "Tableau", "Power BI", "Financial Modeling",
    "Stakeholder Management", "Project Management", "Data Analysis",
    "Strategy", "Market Research", "Valuation", "Due Diligence", "P&L",
    "Agile", "Product Roadmap", "A/B Testing", "User Research",
    "Wireframing", "JIRA", "Scrum",
]

# Multi-word JD phrases to look for via exact match
_MULTI_WORD_SKILLS: list[str] = [
    "stakeholder management", "financial modeling", "project management",
    "data analysis", "market research", "due diligence", "product roadmap",
    "a/b testing", "user research", "product strategy", "strategic planning",
    "cross-functional", "business development",
]

# Standard resume sections
_SECTION_PATTERNS: dict[str, re.Pattern] = {
    "Education":       re.compile(r"\b(education|academic)\b", re.I),
    "Experience":      re.compile(r"\b(experience|work\s+experience|professional\s+experience|employment)\b", re.I),
    "Skills":          re.compile(r"\b(skills|technical\s+skills|core\s+competencies)\b", re.I),
    "Summary":         re.compile(r"\b(summary|objective|profile|about)\b", re.I),
    "Certifications":  re.compile(r"\b(certification|certifications|licenses)\b", re.I),
    "Projects":        re.compile(r"\b(projects|academic\s+projects)\b", re.I),
    "Leadership":      re.compile(r"\b(leadership|extracurricular|activities)\b", re.I),
}

# Regex for quantified content
_QUANT_RE = re.compile(
    r"(\$\s?\d[\d,]*)"       # dollar amounts
    r"|(\d+\s?%)"             # percentages
    r"|(\d[\d,]*\+?\s*(users|customers|clients|people|employees|members|teams?))"  # counts with context
    r"|(\d+x\b)"             # multipliers
    r"|(#\d+)"               # rankings
    r"|(\d{2,}[\d,]*)"       # large numbers (2+ digits)
)


@dataclass
class KeywordResult:
    """Results from keyword matching."""
    score: float  # 0-100
    cosine_sim: float
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    matched_phrases: list[str] = field(default_factory=list)


@dataclass
class SectionResult:
    """Results from section structure check."""
    score: float
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class QuantResult:
    """Results from quantification analysis."""
    score: float
    quantified_count: int = 0
    total_bullets: int = 0
    ratio: float = 0.0


@dataclass
class SkillsResult:
    """Results from skills alignment."""
    score: float
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class ATSResult:
    """Full ATS scoring output."""
    overall_score: int
    keyword: KeywordResult
    section: SectionResult
    quantification: QuantResult
    skills: SkillsResult


# ---------------------------------------------------------------------------
# Component scorers
# ---------------------------------------------------------------------------

def _score_keywords(resume_text: str, jd_text: str) -> KeywordResult:
    """Component 1: TF-IDF cosine similarity + exact phrase matching (40%)."""
    vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
    try:
        tfidf_matrix = vectorizer.fit_transform([jd_text, resume_text])
    except ValueError:
        return KeywordResult(score=0, cosine_sim=0)

    cos_sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])

    # Extract top 30 JD terms by TF-IDF weight
    feature_names = vectorizer.get_feature_names_out()
    jd_vector = tfidf_matrix[0].toarray().flatten()
    top_indices = jd_vector.argsort()[-30:][::-1]
    jd_keywords = [feature_names[i] for i in top_indices if jd_vector[i] > 0]

    resume_lower = resume_text.lower()
    matched = [kw for kw in jd_keywords if kw in resume_lower]
    missing = [kw for kw in jd_keywords if kw not in resume_lower]

    # Exact phrase matching bonus
    matched_phrases = [
        phrase for phrase in _MULTI_WORD_SKILLS
        if phrase in jd_text.lower() and phrase in resume_lower
    ]
    phrase_bonus = min(len(matched_phrases) * 0.03, 0.15)  # up to 15% bonus

    # Combine cosine similarity with keyword overlap
    keyword_overlap = len(matched) / max(len(jd_keywords), 1)
    raw = (cos_sim * 0.5 + keyword_overlap * 0.5 + phrase_bonus)
    score = min(raw * 100, 100)

    return KeywordResult(
        score=round(score, 1),
        cosine_sim=round(cos_sim, 3),
        matched=matched,
        missing=missing,
        matched_phrases=matched_phrases,
    )


def _score_sections(resume_text: str) -> SectionResult:
    """Component 2: Section structure check (20%)."""
    found, missing = [], []
    for name, pattern in _SECTION_PATTERNS.items():
        if pattern.search(resume_text):
            found.append(name)
        else:
            missing.append(name)

    # Base score: proportion of sections found
    base = len(found) / len(_SECTION_PATTERNS) * 100

    # Heavy penalty for missing Experience or Education
    if "Experience" not in found:
        base = max(base - 30, 0)
    if "Education" not in found:
        base = max(base - 15, 0)

    return SectionResult(score=round(min(base, 100), 1), found=found, missing=missing)


def _score_quantification(bullets: list[str]) -> QuantResult:
    """Component 3: Quantification ratio (20%)."""
    if not bullets:
        return QuantResult(score=0)

    quantified = sum(1 for b in bullets if _QUANT_RE.search(b))
    ratio = quantified / len(bullets)

    # Score: linear up to 50% quantified = 100
    score = min(ratio / 0.5 * 100, 100)

    return QuantResult(
        score=round(score, 1),
        quantified_count=quantified,
        total_bullets=len(bullets),
        ratio=round(ratio, 2),
    )


def _score_skills(resume_text: str, jd_text: str) -> SkillsResult:
    """Component 4: Skills taxonomy alignment (20%)."""
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    # Only consider skills that appear in the JD
    jd_skills = [s for s in SKILLS_TAXONOMY if s.lower() in jd_lower]
    if not jd_skills:
        return SkillsResult(score=50)  # neutral if JD has none of our taxonomy

    matched = [s for s in jd_skills if s.lower() in resume_lower]
    missing = [s for s in jd_skills if s.lower() not in resume_lower]

    score = len(matched) / len(jd_skills) * 100
    return SkillsResult(score=round(score, 1), matched=matched, missing=missing)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ats_score(resume_text: str, jd_text: str, bullets: list[str]) -> ATSResult:
    """Compute the full deterministic ATS score.

    Args:
        resume_text: Cleaned resume text.
        jd_text: Cleaned job description text.
        bullets: List of extracted bullet-point strings.

    Returns:
        ATSResult with overall score and per-component breakdowns.
    """
    kw = _score_keywords(resume_text, jd_text)
    sec = _score_sections(resume_text)
    quant = _score_quantification(bullets)
    skills = _score_skills(resume_text, jd_text)

    overall = (
        kw.score * 0.40
        + sec.score * 0.20
        + quant.score * 0.20
        + skills.score * 0.20
    )

    return ATSResult(
        overall_score=round(overall),
        keyword=kw,
        section=sec,
        quantification=quant,
        skills=skills,
    )
