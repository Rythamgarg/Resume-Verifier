"""
Helper utilities shared across modules.
"""


def score_color(score: int) -> str:
    """Return a CSS-friendly colour string for a score value.

    - Green  (80+)
    - Yellow (60-79)
    - Red    (below 60)
    """
    if score >= 80:
        return "#2e7d32"  # green
    if score >= 60:
        return "#f9a825"  # yellow / amber
    return "#c62828"      # red


def score_label(score: int) -> str:
    """Return a human-readable label for a score range."""
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Moderate"
    return "Needs Work"


def truncate(text: str, max_len: int = 500) -> str:
    """Truncate *text* to *max_len* characters, appending '…' if trimmed."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"
