"""
JOB HUNTER - Streamlit Web App powered by JobSpy.
Interactive job scraper with a clean UI for searching multiple job boards.
"""

import subprocess
import sys
from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
import streamlit as st

# Ensure jobspy is available
try:
    from jobspy import scrape_jobs
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-jobspy", "-q"])
    from jobspy import scrape_jobs

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Job Hunter",
    page_icon="🔍",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .main-header h1 {
        color: #1f77b4;
        margin-bottom: 0;
    }
    .main-header p {
        color: #888;
        font-size: 1.1rem;
    }
    .job-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        background: #fafafa;
    }
    .job-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 2px 8px rgba(31,119,180,0.10);
    }
    .job-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .job-company {
        font-size: 0.95rem;
        color: #555;
    }
    .job-meta {
        font-size: 0.85rem;
        color: #888;
        margin-top: 0.3rem;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .badge-green { background: #d4edda; color: #155724; }
    .badge-yellow { background: #fff3cd; color: #856404; }
    .badge-gray { background: #e9ecef; color: #495057; }
    .badge-blue { background: #cce5ff; color: #004085; }
    .stat-box {
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        background: #f0f7ff;
    }
    .stat-box h2 { color: #1f77b4; margin: 0; }
    .stat-box p { color: #666; margin: 0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ────────────────────────────────────────────────────────────────

VALID_SITES = ["linkedin", "indeed", "google", "glassdoor", "zip_recruiter", "naukri"]
SITE_LABELS = {
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "google": "Google Jobs",
    "glassdoor": "Glassdoor",
    "zip_recruiter": "ZipRecruiter",
    "naukri": "Naukri",
}
JOB_TYPES = ["fulltime", "parttime", "internship", "contract"]
HOURS_OPTIONS = {
    "Last 24 hours": 24,
    "Last 48 hours": 48,
    "Last 3 days": 72,
    "Last week": 168,
    "Last month": 720,
}

# ── Helpers ──────────────────────────────────────────────────────────────────


def age_label(date_posted):
    """Return human-readable age and freshness category."""
    if pd.isna(date_posted):
        return "Unknown", "gray"
    try:
        if isinstance(date_posted, str):
            date_posted = pd.to_datetime(date_posted)
        now = datetime.now(timezone.utc) if (hasattr(date_posted, "tzinfo") and date_posted.tzinfo) else datetime.now()
        hours = (now - date_posted).total_seconds() / 3600
    except Exception:
        return str(date_posted), "gray"

    if hours < 1:
        return "< 1 hr ago", "green"
    elif hours < 24:
        return f"{int(hours)} hrs ago", "green"
    elif hours < 48:
        return "1 day ago", "yellow"
    elif hours < 72:
        return f"{int(hours // 24)} days ago", "yellow"
    else:
        return f"{int(hours // 24)} days ago", "gray"


def relevance_score(title, search_term):
    title_lower = (title or "").lower()
    return sum(1 for w in search_term.lower().split() if w in title_lower)


def deduplicate(df):
    if df.empty:
        return df, 0
    key_cols = [c for c in ["company_name", "title", "location"] if c in df.columns]
    if not key_cols:
        return df, 0
    before = len(df)
    df = df.drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)
    return df, before - len(df)


def format_salary(row):
    salary_min = row.get("min_amount")
    salary_max = row.get("max_amount")
    curr = row.get("currency", "")
    if pd.notna(salary_min) and pd.notna(salary_max):
        return f"{curr}{int(salary_min):,} - {curr}{int(salary_max):,}"
    elif pd.notna(salary_min):
        return f"{curr}{int(salary_min):,}+"
    elif pd.notna(salary_max):
        return f"Up to {curr}{int(salary_max):,}"
    return None


def to_csv_bytes(df):
    buf = BytesIO()
    cols = [c for c in df.columns if not c.startswith("_")]
    df[cols].to_csv(buf, index=False)
    return buf.getvalue()


# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🔍 Job Hunter</h1>
    <p>Powered by JobSpy — scrape LinkedIn, Indeed, Google, Glassdoor, Naukri &amp; more</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: Search Parameters ───────────────────────────────────────────────

with st.sidebar:
    st.header("Search Parameters")

    search_term = st.text_input("Job title / search term", placeholder="e.g. Software Engineer")
    location = st.text_input("Location", value="Remote", placeholder="e.g. Bangalore, India")

    col1, col2 = st.columns(2)
    with col1:
        job_type = st.selectbox("Job type", JOB_TYPES, index=0)
    with col2:
        is_remote = st.checkbox("Remote only")

    hours_label = st.selectbox("Posted within", list(HOURS_OPTIONS.keys()), index=2)
    hours_old = HOURS_OPTIONS[hours_label]

    results_wanted = st.slider("Results per site", min_value=5, max_value=100, value=25, step=5)

    sites = st.multiselect(
        "Sites to scrape",
        options=VALID_SITES,
        default=["linkedin", "indeed", "google"],
        format_func=lambda s: SITE_LABELS.get(s, s),
    )

    country_indeed = st.text_input("Country (for Indeed/Glassdoor)", value="India")
    full_description = st.checkbox("Fetch full descriptions (slower)")

    st.divider()
    search_clicked = st.button("🔍 Search Jobs", type="primary", use_container_width=True)

# ── Main area ────────────────────────────────────────────────────────────────

if search_clicked:
    if not search_term.strip():
        st.error("Please enter a job title or search term.")
        st.stop()
    if not sites:
        st.error("Please select at least one site to scrape.")
        st.stop()

    with st.spinner("Scraping jobs... this may take a minute."):
        try:
            jobs = scrape_jobs(
                site_name=sites,
                search_term=search_term,
                location=location,
                job_type=job_type,
                is_remote=is_remote,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country_indeed,
                full_description=full_description,
            )
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "rate" in err:
                st.error("LinkedIn rate limited. Consider removing LinkedIn from sites or try again later.")
            else:
                st.error(f"Scraping error: {e}")
            st.stop()

    if jobs is None or jobs.empty:
        st.warning("No jobs found. Try broadening your search — increase the time range, add more sites, or use a different location.")
        st.stop()

    # Process results
    jobs, dupes_removed = deduplicate(jobs)
    jobs["_relevance"] = jobs["title"].apply(lambda t: relevance_score(t, search_term))
    if "date_posted" in jobs.columns:
        jobs["date_posted"] = pd.to_datetime(jobs["date_posted"], errors="coerce")
        jobs = jobs.sort_values(by=["date_posted", "_relevance"], ascending=[False, False]).reset_index(drop=True)

    st.session_state["jobs"] = jobs
    st.session_state["search_term"] = search_term

# ── Display results ──────────────────────────────────────────────────────────

if "jobs" in st.session_state:
    jobs = st.session_state["jobs"]
    search_term_display = st.session_state.get("search_term", "")

    # Stats row
    sites_found = jobs["site"].nunique() if "site" in jobs.columns else 0
    salary_count = 0
    if "min_amount" in jobs.columns:
        salary_count = jobs["min_amount"].notna().sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><h2>{len(jobs)}</h2><p>Jobs Found</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><h2>{sites_found}</h2><p>Sources</p></div>', unsafe_allow_html=True)
    with c3:
        fresh = sum(1 for _, r in jobs.iterrows() if age_label(r.get("date_posted"))[1] == "green")
        st.markdown(f'<div class="stat-box"><h2>{fresh}</h2><p>Fresh (< 24h)</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><h2>{salary_count}</h2><p>With Salary</p></div>', unsafe_allow_html=True)

    st.write("")

    # Keyword filter
    keyword = st.text_input("Filter by keyword (searches title, company, description, location)", placeholder="e.g. AI, startup, remote")
    if keyword.strip():
        mask = pd.Series([False] * len(jobs), index=jobs.index)
        for col in ["title", "description", "company_name", "location"]:
            if col in jobs.columns:
                mask |= jobs[col].astype(str).str.contains(keyword, case=False, na=False)
        filtered = jobs[mask].reset_index(drop=True)
        st.info(f"Showing {len(filtered)} of {len(jobs)} jobs matching \"{keyword}\"")
        display_df = filtered
    else:
        display_df = jobs

    # Top 20 job cards
    top = display_df.head(20)

    st.subheader(f"Top {len(top)} Jobs (sorted by recency)")

    for i, (_, row) in enumerate(top.iterrows(), 1):
        title = str(row.get("title", "N/A"))
        company = str(row.get("company_name", "N/A"))
        loc = str(row.get("location", "N/A"))
        jtype = str(row.get("job_type", ""))
        source = str(row.get("site", ""))
        url = row.get("job_url", "")
        salary = format_salary(row)
        posted_label, freshness = age_label(row.get("date_posted"))

        badge_class = f"badge-{freshness}"
        source_badge = f'<span class="badge badge-blue">{SITE_LABELS.get(source, source)}</span>'
        time_badge = f'<span class="badge {badge_class}">{posted_label}</span>'
        type_badge = f'<span class="badge badge-gray">{jtype}</span>' if jtype and jtype != "None" else ""
        salary_html = f' &nbsp;|&nbsp; 💰 {salary}' if salary else ""

        url_html = ""
        if pd.notna(url) and url:
            url_html = f'<a href="{url}" target="_blank">Apply →</a>'

        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{i}. {title} &nbsp;{url_html}</div>
            <div class="job-company">{company} &nbsp;|&nbsp; 📍 {loc}{salary_html}</div>
            <div class="job-meta">{time_badge} {source_badge} {type_badge}</div>
        </div>
        """, unsafe_allow_html=True)

    # Downloads
    st.divider()
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.download_button(
            "📥 Download All Results (CSV)",
            data=to_csv_bytes(jobs),
            file_name="jobs_output.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dcol2:
        st.download_button(
            "📥 Download Top 20 (CSV)",
            data=to_csv_bytes(top),
            file_name="top_20_jobs.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Apply links section
    with st.expander("🔗 Quick Apply Links", expanded=False):
        for i, (_, row) in enumerate(top.iterrows(), 1):
            url = row.get("job_url", "")
            title = str(row.get("title", "N/A"))
            company = str(row.get("company_name", ""))
            if pd.notna(url) and url:
                st.markdown(f"{i}. [{title} — {company}]({url})")
            else:
                st.markdown(f"{i}. {title} — {company} (no link)")

    # Full data table
    with st.expander("📊 Full Data Table"):
        show_cols = [c for c in ["title", "company_name", "location", "job_type", "date_posted",
                                  "site", "min_amount", "max_amount", "currency", "job_url"] if c in display_df.columns]
        st.dataframe(display_df[show_cols], use_container_width=True)
else:
    st.info("👈 Configure your search parameters in the sidebar and click **Search Jobs** to get started.")
