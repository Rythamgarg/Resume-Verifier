"""
LLM-powered deep analysis via Groq API.

Provides rich qualitative feedback by sending the resume + JD to
Llama 3.1 70B via the Groq SDK. Gracefully degrades when the API key
is missing or rate limits are hit.
"""

import json
import time
from dataclasses import dataclass, field

from groq import Groq


@dataclass
class DeepAnalysis:
    """Structured output from LLM deep analysis."""
    overall_assessment: str = ""
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    keywords_to_add: list[str] = field(default_factory=list)
    narrative_feedback: str = ""


def analyze(
    resume_text: str,
    jd_text: str,
    role_type: str,
    api_key: str,
) -> DeepAnalysis:
    """Run LLM deep analysis on the resume against the JD.

    Args:
        resume_text: Cleaned resume text.
        jd_text: Cleaned job description text.
        role_type: "Consulting" or "Product Management".
        api_key: Groq API key.

    Returns:
        DeepAnalysis dataclass.

    Raises:
        RateLimitError: Re-raised so the caller can show a friendly message.
        Exception: Any other Groq/network error.
    """
    client = Groq(api_key=api_key)

    prompt = (
        f"You are an expert resume reviewer specializing in {role_type} roles.\n\n"
        f"Resume text:\n{resume_text}\n\n"
        f"Job description:\n{jd_text}\n\n"
        "Analyze this resume against the job description and return a JSON response with:\n"
        '1. "overall_assessment": 2-3 sentence summary of fit\n'
        '2. "strengths": list of 3-5 specific strengths with evidence from the resume\n'
        '3. "gaps": list of 3-5 specific gaps or missing elements\n'
        '4. "keywords_to_add": list of 5-10 specific keywords/phrases from the JD '
        "that should be incorporated\n"
        '5. "narrative_feedback": 2-3 sentences on whether the resume tells a '
        f"coherent career story for a {role_type} role\n\n"
        "Return ONLY valid JSON, no markdown formatting, no backticks."
    )

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if the model added them despite instructions
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]  # remove opening fence line
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: treat entire response as the assessment
        return DeepAnalysis(overall_assessment=raw)

    return DeepAnalysis(
        overall_assessment=data.get("overall_assessment", ""),
        strengths=data.get("strengths", []),
        gaps=data.get("gaps", []),
        keywords_to_add=data.get("keywords_to_add", []),
        narrative_feedback=data.get("narrative_feedback", ""),
    )
