"""
Resume–JD Matcher — Streamlit application.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from parser import extract_text_from_pdf, normalize_text, extract_bullets
from scoring import extract_keywords, compute_ats_score
from consulting_model import ROLE_SCORERS
from bullet_rewriter import rewrite_bullet

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Resume–JD Matcher", layout="wide")
st.title("Resume–JD Matcher")
st.markdown(
    "Upload your resume and a job description to see how well they align, "
    "get missing-keyword insights, and receive bullet-point improvement suggestions."
)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Inputs")

resume_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

jd_input_mode = st.sidebar.radio(
    "Job Description Input", ["Paste Text", "Upload PDF"]
)

jd_text = ""
if jd_input_mode == "Paste Text":
    jd_text = st.sidebar.text_area("Paste Job Description", height=250)
else:
    jd_file = st.sidebar.file_uploader("Upload JD (PDF)", type=["pdf"], key="jd_pdf")
    if jd_file is not None:
        jd_text = extract_text_from_pdf(jd_file)

role_type = st.sidebar.selectbox("Role Type", list(ROLE_SCORERS.keys()))

evaluate = st.sidebar.button("Evaluate Resume", type="primary")

# ---------------------------------------------------------------------------
# Main evaluation flow
# ---------------------------------------------------------------------------
if evaluate:
    # --- Validate inputs ------------------------------------------------
    if resume_file is None:
        st.error("Please upload a resume PDF.")
        st.stop()
    if not jd_text.strip():
        st.error("Please provide a job description.")
        st.stop()

    # --- Parse resume ---------------------------------------------------
    with st.spinner("Parsing resume…"):
        resume_text = extract_text_from_pdf(resume_file)
        if not resume_text:
            st.error(
                "Could not extract text from the resume PDF. "
                "Please ensure the file is not image-only."
            )
            st.stop()

    jd_clean = normalize_text(jd_text)

    # --- ATS scoring ----------------------------------------------------
    with st.spinner("Computing ATS score…"):
        jd_keywords = extract_keywords(jd_clean)
        ats = compute_ats_score(resume_text, jd_keywords)

    # --- Role-fit scoring -----------------------------------------------
    with st.spinner(f"Computing {role_type} fit score…"):
        scorer = ROLE_SCORERS[role_type]
        role_fit = scorer(resume_text)

    # --- Bullet extraction & rewriting ----------------------------------
    with st.spinner("Extracting bullets and generating suggestions…"):
        bullets = extract_bullets(resume_text)
        suggestions = [rewrite_bullet(b, jd_clean) for b in bullets]

    # --- Display results ------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ATS Match Score")
        st.metric(label="Score", value=f"{ats['score']} / 100")

    with col2:
        st.subheader(f"{role_type} Fit Score")
        st.metric(label="Score", value=f"{role_fit['score']} / 100")

    # Role-fit breakdown
    st.subheader(f"{role_type} Fit Breakdown")
    breakdown_df = pd.DataFrame(
        [{"Dimension": dim, "Score": val}
         for dim, val in role_fit["breakdown"].items()]
    )
    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    # Missing keywords
    st.subheader("Missing Keywords")
    if ats["missing"]:
        st.write(", ".join(ats["missing"]))
    else:
        st.success("All major keywords matched!")

    # Bullet suggestions
    st.subheader("Bullet Improvement Suggestions")
    if bullets:
        bullet_df = pd.DataFrame({
            "Original Bullet": bullets,
            "Suggested Improvement": suggestions,
        })
        st.dataframe(bullet_df, use_container_width=True, hide_index=True)
    else:
        st.info("No bullet points detected in the resume.")
