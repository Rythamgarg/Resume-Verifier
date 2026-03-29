"""
LLM-powered bullet point rewriter via Groq API.

Rewrites individual resume bullets to better align with a target
job description, using strong action-result format.
"""

from groq import Groq


def rewrite_bullet(
    bullet: str,
    jd_text: str,
    role_type: str,
    api_key: str,
) -> str:
    """Rewrite a single bullet point using Llama via Groq.

    Args:
        bullet: Original bullet text.
        jd_text: Full job description (truncated to first 500 chars in prompt).
        role_type: "Consulting" or "Product Management".
        api_key: Groq API key.

    Returns:
        The rewritten bullet string.

    Raises:
        Exception: Any Groq/network error — caller should handle gracefully.
    """
    client = Groq(api_key=api_key)

    prompt = (
        f"You are an expert resume writer for {role_type} roles.\n\n"
        f"Original bullet: {bullet}\n"
        f"Job description context: {jd_text[:500]}\n\n"
        "Rewrite this bullet point to:\n"
        "1. Start with a strong action verb\n"
        "2. Include quantified impact where possible\n"
        "3. Align better with the job description\n"
        "4. Follow the format: [Action verb] + [What you did] + [Result/Impact]\n\n"
        "Return ONLY the rewritten bullet, nothing else."
    )

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=256,
    )

    return response.choices[0].message.content.strip()
