"""
Role-specific scoring rubrics for Consulting and Product Management.

Each rubric scores four dimensions (0-100 each, equally weighted)
using keyword/phrase detection. Fully deterministic — no API needed.
"""

import re
from dataclasses import dataclass, field


@dataclass
class DimensionScore:
    """Score for a single rubric dimension."""
    name: str
    score: int
    matched_signals: list[str] = field(default_factory=list)


@dataclass
class RoleResult:
    """Full role-fit scoring output."""
    role: str
    overall_score: int
    dimensions: list[DimensionScore] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Signal dictionaries
# ---------------------------------------------------------------------------

_CONSULTING_SIGNALS: dict[str, list[str]] = {
    "Problem Solving": [
        "analyzed", "optimized", "modeled", "framework", "structured",
        "diagnosed", "assessed", "evaluated", "solved",
        "identified root cause", "hypothesis", "data-driven",
        "synthesized", "recommended", "insights", "benchmarked",
    ],
    "Leadership": [
        "led", "managed", "mentored", "spearheaded", "drove",
        "built team", "coordinated", "oversaw", "directed", "supervised",
        "founded", "initiated", "championed", "mobilized",
        "cross-functional team",
    ],
    "Client/Stakeholder Exposure": [
        "client", "stakeholder", "c-suite", "executive", "presented to",
        "client-facing", "engagement", "advisory",
        "recommended to leadership", "board", "partner", "external",
        "vendor management", "relationship management",
    ],
    "Business Impact": [
        "%", "$", "revenue", "cost reduction", "growth", "efficiency",
        "savings", "roi", "margin", "conversion", "retention",
    ],
}

_PM_SIGNALS: dict[str, list[str]] = {
    "Product Thinking": [
        "roadmap", "prioritization", "user stories", "backlog", "mvp",
        "product strategy", "feature", "requirements", "prd",
        "sprint planning", "product-market fit", "discovery",
        "user needs", "jobs to be done",
    ],
    "Technical Acumen": [
        "api", "sql", "a/b testing", "data pipeline", "engineering",
        "technical specifications", "system design", "architecture",
        "sprint", "agile", "scrum", "ci/cd", "analytics",
        "instrumentation",
    ],
    "User Centricity": [
        "user research", "customer interviews", "usability", "personas",
        "journey map", "nps", "csat", "feedback loop", "user testing",
        "empathy", "customer insight", "pain point", "experience design",
    ],
    "Execution & Metrics": [
        "shipped", "launched", "increased", "reduced", "okrs", "kpis",
        "north star metric", "conversion rate", "retention", "dau", "mau",
        "engagement", "velocity", "iteration",
    ],
}


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _match_signals(text: str, signals: list[str]) -> list[str]:
    """Return the subset of *signals* found in *text* (case-insensitive)."""
    lower = text.lower()
    return [s for s in signals if s.lower() in lower]


def _dimension_score(matched_count: int, threshold: int = 8) -> int:
    """Map a match count to 0-100, capped at *threshold* hits."""
    return min(round(matched_count / threshold * 100), 100)


def _derive_strengths_and_gaps(
    dimensions: list[DimensionScore],
) -> tuple[list[str], list[str]]:
    """Pick top 3 strengths (highest scores) and top 3 gaps (lowest)."""
    sorted_dims = sorted(dimensions, key=lambda d: d.score, reverse=True)
    strengths = [
        f"{d.name} ({d.score}/100)" for d in sorted_dims[:3] if d.score > 0
    ]
    gaps = [
        f"{d.name} ({d.score}/100)" for d in sorted_dims if d.score < 75
    ][:3]
    return strengths, gaps


def _score_role(
    resume_text: str,
    role_name: str,
    signal_map: dict[str, list[str]],
    impact_dimension: str = "Business Impact",
    impact_threshold: int = 5,
) -> RoleResult:
    """Generic scorer that applies a signal map to resume text."""
    dimensions: list[DimensionScore] = []

    for dim_name, signals in signal_map.items():
        matched = _match_signals(resume_text, signals)
        # Business-impact / execution dimensions use a lower threshold
        thresh = impact_threshold if dim_name == impact_dimension else 8
        score = _dimension_score(len(matched), thresh)
        dimensions.append(DimensionScore(dim_name, score, matched))

    overall = round(sum(d.score for d in dimensions) / len(dimensions))
    strengths, gaps = _derive_strengths_and_gaps(dimensions)

    return RoleResult(
        role=role_name,
        overall_score=overall,
        dimensions=dimensions,
        strengths=strengths,
        gaps=gaps,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_consulting(resume_text: str) -> RoleResult:
    """Score resume for Consulting role fit."""
    return _score_role(
        resume_text,
        role_name="Consulting",
        signal_map=_CONSULTING_SIGNALS,
        impact_dimension="Business Impact",
        impact_threshold=5,
    )


def score_product_management(resume_text: str) -> RoleResult:
    """Score resume for Product Management role fit."""
    return _score_role(
        resume_text,
        role_name="Product Management",
        signal_map=_PM_SIGNALS,
        impact_dimension="Execution & Metrics",
        impact_threshold=5,
    )


ROLE_SCORERS = {
    "Consulting": score_consulting,
    "Product Management": score_product_management,
}
