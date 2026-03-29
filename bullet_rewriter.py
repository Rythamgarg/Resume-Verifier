"""
Bullet point improvement suggestions.

Provides a stub rewriter that returns template-based suggestions.
The ``rewrite_bullet`` function is designed to be swapped with an
LLM-backed implementation once an API key is available.
"""


def rewrite_bullet(bullet: str, job_description: str) -> str:
    """Return an improved version of *bullet* aligned with *job_description*.

    This is a **placeholder** implementation.  To integrate a real LLM:

        1. Import your preferred SDK (e.g., ``openai``, ``anthropic``).
        2. Build a prompt that includes the bullet and JD context.
        3. Return the model's rewritten bullet.

    The current stub applies simple heuristic improvements so the UI
    has something meaningful to display.
    """
    return _heuristic_rewrite(bullet, job_description)


def _heuristic_rewrite(bullet: str, job_description: str) -> str:
    """Apply lightweight heuristic improvements to a bullet."""
    improved = bullet.strip()

    # Ensure the bullet starts with a strong action verb (capitalize first word)
    if improved and improved[0].islower():
        improved = improved[0].upper() + improved[1:]

    # If no quantified result is present, append a coaching hint
    has_number = any(ch.isdigit() for ch in improved)
    if not has_number:
        improved += " [Add measurable impact: %, $, or numeric result]"

    # If the bullet is very short, flag it
    if len(improved.split()) < 6:
        improved += " [Expand with context and outcome]"

    return improved


# ------------------------------------------------------------------
# LLM integration template (uncomment and configure when ready)
# ------------------------------------------------------------------
#
# import anthropic
#
# _CLIENT = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
#
# def rewrite_bullet_llm(bullet: str, job_description: str) -> str:
#     prompt = (
#         "You are a resume-writing expert. Rewrite the following bullet "
#         "point so it better aligns with the job description. Use strong "
#         "action-result format with quantified impact.\n\n"
#         f"Bullet: {bullet}\n\n"
#         f"Job description:\n{job_description}\n\n"
#         "Improved bullet:"
#     )
#     message = _CLIENT.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=256,
#         messages=[{"role": "user", "content": prompt}],
#     )
#     return message.content[0].text.strip()
