"""
Role-specific fit scoring models.

Currently supports Consulting, Product, and Analytics role types.
Each model applies rule-based heuristics to score a resume against
role-specific competency dimensions.
"""

import re

# ---------------------------------------------------------------------------
# Shared signal dictionaries
# ---------------------------------------------------------------------------

PROBLEM_SOLVING_VERBS = {
    "analyzed", "assessed", "audited", "benchmarked", "diagnosed",
    "evaluated", "forecasted", "hypothesized", "identified", "investigated",
    "mapped", "modeled", "optimized", "prioritized", "quantified",
    "recommended", "resolved", "restructured", "scoped", "simulated",
    "solved", "synthesized", "validated",
}

LEADERSHIP_VERBS = {
    "advised", "aligned", "championed", "coached", "coordinated", "delegated",
    "directed", "drove", "established", "guided", "hired", "influenced",
    "initiated", "inspired", "led", "managed", "mentored", "mobilized",
    "orchestrated", "oversaw", "shaped", "spearheaded", "supervised",
    "trained",
}

CLIENT_SIGNALS = {
    "client", "stakeholder", "engagement", "customer", "partner", "executive",
    "board", "c-suite", "cxo", "sponsor", "account",
}

PRODUCT_SIGNALS = {
    "roadmap", "backlog", "sprint", "user story", "a/b test", "conversion",
    "retention", "onboarding", "feature", "mvp", "product-market",
    "prioritization", "okr", "kpi", "user research", "persona",
}

ANALYTICS_SIGNALS = {
    "sql", "python", "tableau", "power bi", "dashboard", "etl", "pipeline",
    "regression", "clustering", "segmentation", "cohort", "statistical",
    "hypothesis", "experiment", "a/b", "bigquery", "redshift", "spark",
    "pandas", "scikit",
}

# Regex for quantified impact (numbers with $, %, or large figures)
_QUANT_RE = re.compile(
    r"(\$\s?\d[\d,]*)"       # dollar amounts
    r"|(\d+\s?%)"             # percentages
    r"|(\d{2,}[\d,]*\+?)"    # large numbers (2+ digits)
)


def _signal_count(text: str, signals: set[str]) -> int:
    """Count how many distinct signals appear in *text*."""
    lower = text.lower()
    return sum(1 for s in signals if s in lower)


def _dimension_score(hits: int, scale: int = 25) -> int:
    """Map a hit count to a 0–*scale* score with diminishing returns."""
    if hits == 0:
        return 0
    if hits >= 5:
        return scale
    return round(scale * (hits / 5))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_consulting_fit(resume_text: str) -> dict:
    """Score a resume for consulting-role fit (0-100).

    Dimensions (each 0-25):
      - Problem Solving
      - Leadership
      - Stakeholder Exposure
      - Business Impact (quantified results)
    """
    ps = _signal_count(resume_text, PROBLEM_SOLVING_VERBS)
    ld = _signal_count(resume_text, LEADERSHIP_VERBS)
    cl = _signal_count(resume_text, CLIENT_SIGNALS)
    qi = len(_QUANT_RE.findall(resume_text))

    breakdown = {
        "Problem Solving": _dimension_score(ps),
        "Leadership": _dimension_score(ld),
        "Stakeholder Exposure": _dimension_score(cl),
        "Business Impact": _dimension_score(qi),
    }
    total = sum(breakdown.values())
    return {"score": total, "breakdown": breakdown}


def score_product_fit(resume_text: str) -> dict:
    """Score a resume for product-management fit (0-100)."""
    ps = _signal_count(resume_text, PROBLEM_SOLVING_VERBS)
    ld = _signal_count(resume_text, LEADERSHIP_VERBS)
    pm = _signal_count(resume_text, PRODUCT_SIGNALS)
    qi = len(_QUANT_RE.findall(resume_text))

    breakdown = {
        "Strategic Thinking": _dimension_score(ps),
        "Leadership": _dimension_score(ld),
        "Product Sense": _dimension_score(pm),
        "Business Impact": _dimension_score(qi),
    }
    total = sum(breakdown.values())
    return {"score": total, "breakdown": breakdown}


def score_analytics_fit(resume_text: str) -> dict:
    """Score a resume for analytics-role fit (0-100)."""
    ps = _signal_count(resume_text, PROBLEM_SOLVING_VERBS)
    an = _signal_count(resume_text, ANALYTICS_SIGNALS)
    qi = len(_QUANT_RE.findall(resume_text))
    cl = _signal_count(resume_text, CLIENT_SIGNALS)

    breakdown = {
        "Analytical Thinking": _dimension_score(ps),
        "Technical Skills": _dimension_score(an),
        "Quantitative Impact": _dimension_score(qi),
        "Stakeholder Communication": _dimension_score(cl),
    }
    total = sum(breakdown.values())
    return {"score": total, "breakdown": breakdown}


# Dispatch map for the UI
ROLE_SCORERS = {
    "Consulting": score_consulting_fit,
    "Product": score_product_fit,
    "Analytics": score_analytics_fit,
}
