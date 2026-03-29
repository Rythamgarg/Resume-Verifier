"""
ResumeATS — AI-powered ATS resume checker for MBA placements.

Main Streamlit application. Run with:
    streamlit run app.py
"""

import time

import streamlit as st

from parser import extract_text_from_pdf, extract_bullets
from ats_scorer import compute_ats_score
from role_scorer import ROLE_SCORERS
from utils import score_color, score_label

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(page_title="ResumeATS", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("ResumeATS")
st.sidebar.caption("AI-powered resume checker for MBA placements")

# Groq API key — try secrets first, then manual input
groq_key = ""
try:
    groq_key = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    pass

if not groq_key:
    groq_key = st.sidebar.text_input(
        "Groq API Key (optional)", type="password",
        help="Enables Deep Analysis and Bullet Rewriter tabs. "
             "Leave blank to use deterministic scoring only.",
    )

llm_available = bool(groq_key and groq_key != "your-groq-api-key-here")

role_type = st.sidebar.selectbox("Role Type", list(ROLE_SCORERS.keys()))

with st.sidebar.expander("About"):
    st.markdown(
        "**ResumeATS** scores your resume against a job description using:\n\n"
        "- Deterministic ATS scoring (always available)\n"
        "- Role-specific fit rubrics for Consulting & PM\n"
        "- LLM-powered deep analysis & bullet rewriting (requires Groq API key)"
    )

# ---------------------------------------------------------------------------
# Main area — inputs
# ---------------------------------------------------------------------------
st.title("ResumeATS")

col_resume, col_jd = st.columns(2)

with col_resume:
    st.subheader("Resume")
    resume_file = st.file_uploader("Upload resume PDF", type=["pdf"])

with col_jd:
    st.subheader("Job Description")
    jd_text = st.text_area("Paste the job description", height=250)

analyze_btn = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
if analyze_btn:
    # --- Validate inputs ------------------------------------------------
    if resume_file is None:
        st.error("Please upload a resume PDF.")
        st.stop()
    if not jd_text.strip():
        st.error("Please paste a job description.")
        st.stop()

    # --- Parse resume ---------------------------------------------------
    with st.spinner("Parsing resume…"):
        try:
            resume_text = extract_text_from_pdf(resume_file)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

    bullets = extract_bullets(resume_text)

    # --- Deterministic scores ------------------------------------------
    with st.spinner("Computing ATS score…"):
        ats = compute_ats_score(resume_text, jd_text, bullets)

    with st.spinner(f"Computing {role_type} fit…"):
        role_result = ROLE_SCORERS[role_type](resume_text)

    # --- LLM analysis (optional) ---------------------------------------
    deep_analysis = None
    if llm_available:
        with st.spinner("Running LLM deep analysis…"):
            try:
                from llm_analyzer import analyze
                deep_analysis = analyze(resume_text, jd_text, role_type, groq_key)
            except Exception as exc:
                exc_name = type(exc).__name__
                if "RateLimit" in exc_name:
                    st.warning(
                        "Deep analysis temporarily unavailable due to high usage. "
                        "Your ATS score and role-fit score are still available above. "
                        "Try again in a few minutes."
                    )
                else:
                    st.warning(f"Deep analysis unavailable: {exc}")
                deep_analysis = None

    # ===================================================================
    # RESULTS
    # ===================================================================
    st.divider()

    # --- Tabs ----------------------------------------------------------
    tab_names = ["ATS Score", "Role Fit"]
    if llm_available:
        tab_names += ["Deep Analysis", "Bullet Improver"]
    tabs = st.tabs(tab_names)

    # --- Tab 1: ATS Score ----------------------------------------------
    with tabs[0]:
        # Overall metric
        c1, c2 = st.columns([1, 2])
        with c1:
            color = score_color(ats.overall_score)
            st.markdown(
                f"<h1 style='color:{color};'>{ats.overall_score}</h1>"
                f"<p style='color:{color};'>{score_label(ats.overall_score)}</p>",
                unsafe_allow_html=True,
            )
            st.caption("ATS Score (0–100)")

        # Component breakdown
        with c2:
            st.markdown("**Score Breakdown**")
            components = [
                ("Keyword Match (40%)", ats.keyword.score),
                ("Section Structure (20%)", ats.section.score),
                ("Quantification (20%)", ats.quantification.score),
                ("Skills Alignment (20%)", ats.skills.score),
            ]
            for label, val in components:
                st.progress(min(val / 100, 1.0), text=f"{label}: {val:.0f}")

        # Keywords
        col_match, col_miss = st.columns(2)
        with col_match:
            with st.expander(f"✅ Matched Keywords ({len(ats.keyword.matched)})"):
                if ats.keyword.matched:
                    st.write(", ".join(ats.keyword.matched))
                else:
                    st.write("None")
                if ats.keyword.matched_phrases:
                    st.markdown("**Matched phrases:** " + ", ".join(ats.keyword.matched_phrases))

        with col_miss:
            with st.expander(f"❌ Missing Keywords ({len(ats.keyword.missing)})"):
                if ats.keyword.missing:
                    st.write(", ".join(ats.keyword.missing))
                else:
                    st.success("All keywords matched!")

        # Sections
        with st.expander("📋 Section Check"):
            s1, s2 = st.columns(2)
            with s1:
                st.markdown("**Found:** " + ", ".join(ats.section.found) if ats.section.found else "**Found:** None")
            with s2:
                st.markdown("**Missing:** " + ", ".join(ats.section.missing) if ats.section.missing else "**Missing:** None")

        # Quantification details
        with st.expander("📊 Quantification"):
            st.write(
                f"{ats.quantification.quantified_count} of "
                f"{ats.quantification.total_bullets} bullets are quantified "
                f"({ats.quantification.ratio:.0%})"
            )

        # Skills
        if ats.skills.matched or ats.skills.missing:
            with st.expander("🛠 Skills Alignment"):
                sk1, sk2 = st.columns(2)
                with sk1:
                    st.markdown("**Matched:** " + ", ".join(ats.skills.matched) if ats.skills.matched else "**Matched:** None")
                with sk2:
                    st.markdown("**Missing:** " + ", ".join(ats.skills.missing) if ats.skills.missing else "**Missing:** None")

    # --- Tab 2: Role Fit -----------------------------------------------
    with tabs[1]:
        c1, c2 = st.columns([1, 2])
        with c1:
            color = score_color(role_result.overall_score)
            st.markdown(
                f"<h1 style='color:{color};'>{role_result.overall_score}</h1>"
                f"<p style='color:{color};'>{score_label(role_result.overall_score)}</p>",
                unsafe_allow_html=True,
            )
            st.caption(f"{role_type} Fit (0–100)")

        with c2:
            st.markdown("**Dimension Breakdown**")
            for dim in role_result.dimensions:
                st.progress(min(dim.score / 100, 1.0), text=f"{dim.name}: {dim.score}")

        col_str, col_gap = st.columns(2)
        with col_str:
            st.markdown("**💪 Strengths**")
            for s in role_result.strengths:
                st.write(f"- {s}")
            if not role_result.strengths:
                st.write("No strong dimensions detected.")

        with col_gap:
            st.markdown("**⚠️ Gaps**")
            for g in role_result.gaps:
                st.write(f"- {g}")
            if not role_result.gaps:
                st.success("No significant gaps!")

        # Show matched signals per dimension
        with st.expander("Signal Details"):
            for dim in role_result.dimensions:
                if dim.matched_signals:
                    st.markdown(f"**{dim.name}:** {', '.join(dim.matched_signals)}")
                else:
                    st.markdown(f"**{dim.name}:** no signals detected")

    # --- Tab 3: Deep Analysis (LLM) -----------------------------------
    if llm_available and len(tabs) > 2:
        with tabs[2]:
            if deep_analysis is None:
                st.info(
                    "Deep analysis was unavailable for this run. "
                    "Check your API key or try again shortly."
                )
            else:
                if deep_analysis.overall_assessment:
                    st.markdown("### Overall Assessment")
                    st.info(deep_analysis.overall_assessment)

                da_col1, da_col2 = st.columns(2)
                with da_col1:
                    st.markdown("### Strengths")
                    for s in deep_analysis.strengths:
                        st.write(f"✅ {s}")
                with da_col2:
                    st.markdown("### Gaps")
                    for g in deep_analysis.gaps:
                        st.write(f"❌ {g}")

                if deep_analysis.keywords_to_add:
                    st.markdown("### Keywords to Add")
                    st.write(", ".join(deep_analysis.keywords_to_add))

                if deep_analysis.narrative_feedback:
                    st.markdown("### Career Narrative")
                    st.write(deep_analysis.narrative_feedback)

    # --- Tab 4: Bullet Improver (LLM) ---------------------------------
    if llm_available and len(tabs) > 3:
        with tabs[3]:
            if not bullets:
                st.info("No bullet points detected in the resume.")
            else:
                st.markdown(f"**{len(bullets)} bullets extracted.** Click Rewrite to improve individual bullets.")

                for i, bullet in enumerate(bullets):
                    with st.container():
                        st.markdown(f"**Bullet {i + 1}**")
                        st.text(bullet)
                        if st.button("Rewrite", key=f"rewrite_{i}"):
                            with st.spinner("Rewriting…"):
                                try:
                                    from bullet_rewriter import rewrite_bullet
                                    time.sleep(1)  # rate-limit courtesy delay
                                    improved = rewrite_bullet(
                                        bullet, jd_text, role_type, groq_key,
                                    )
                                    st.success(improved)
                                except Exception as exc:
                                    exc_name = type(exc).__name__
                                    if "RateLimit" in exc_name:
                                        st.warning(
                                            "Rate limit reached. Try again in a few minutes."
                                        )
                                    else:
                                        st.warning(f"Rewrite failed: {exc}")
                        st.divider()

    # --- No API key message on missing tabs ----------------------------
    if not llm_available:
        st.divider()
        st.info(
            "💡 **Deep analysis unavailable.** Add a Groq API key in the sidebar "
            "for LLM-powered insights and bullet rewriting."
        )
