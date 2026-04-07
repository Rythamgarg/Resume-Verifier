#!/usr/bin/env python3
"""
JOB HUNTER - Interactive command-line job scraper powered by JobSpy.
Scrapes multiple job boards and presents results in a clean, ranked format.
"""

import subprocess
import sys
from datetime import datetime, timezone


def ensure_installed(package, import_name=None):
    """Auto-install a package if not available."""
    try:
        __import__(import_name or package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])


ensure_installed("python-jobspy", "jobspy")
ensure_installed("pandas")
ensure_installed("tabulate")
ensure_installed("colorama")

import pandas as pd
from colorama import Fore, Style, init as colorama_init
from jobspy import scrape_jobs
from tabulate import tabulate

colorama_init(autoreset=True)

VALID_SITES = ["linkedin", "indeed", "google", "glassdoor", "zip_recruiter", "naukri"]
VALID_JOB_TYPES = ["fulltime", "parttime", "internship", "contract"]
VALID_HOURS = [24, 48, 72, 168, 720]

JOBTYPE_MAP = {
    "fulltime": "fulltime",
    "parttime": "parttime",
    "internship": "internship",
    "contract": "contract",
}


def print_banner():
    print(f"\n{Fore.CYAN}{'=' * 48}")
    print(f"   {Fore.GREEN}JOB HUNTER {Fore.WHITE}- Powered by JobSpy")
    print(f"{Fore.CYAN}{'=' * 48}{Style.RESET_ALL}\n")


def get_input(prompt, default=None, choices=None):
    """Get user input with optional default and validation."""
    if default is not None:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "

    while True:
        value = input(display).strip()
        if not value and default is not None:
            return default
        if not value and default is None:
            print(f"{Fore.RED}  This field is required.{Style.RESET_ALL}")
            continue
        if choices and value.lower() not in [str(c).lower() for c in choices]:
            print(f"{Fore.RED}  Invalid choice. Options: {', '.join(str(c) for c in choices)}{Style.RESET_ALL}")
            continue
        return value


def get_yes_no(prompt, default="n"):
    val = get_input(prompt + " (y/n)", default=default, choices=["y", "n"])
    return val.lower() == "y"


def gather_inputs():
    """Interactively gather all search parameters from the user."""
    params = {}

    params["search_term"] = get_input("Enter job title/search term")
    params["location"] = get_input("Enter location", default="Remote")

    jt = get_input(
        f"Job type ({'/'.join(VALID_JOB_TYPES)})",
        default="fulltime",
        choices=VALID_JOB_TYPES,
    )
    params["job_type"] = JOBTYPE_MAP[jt.lower()]

    params["is_remote"] = get_yes_no("Remote only?", default="n")

    hours = get_input(
        f"Max hours old ({'/'.join(str(h) for h in VALID_HOURS)})",
        default="72",
        choices=[str(h) for h in VALID_HOURS],
    )
    params["hours_old"] = int(hours)

    results = get_input("Results per site", default="25")
    params["results_wanted"] = int(results)

    sites_raw = get_input(
        f"Sites to scrape ({','.join(VALID_SITES)})",
        default="linkedin,indeed,google",
    )
    sites = [s.strip().lower() for s in sites_raw.split(",") if s.strip().lower() in VALID_SITES]
    if not sites:
        print(f"{Fore.YELLOW}  No valid sites entered, defaulting to linkedin,indeed,google{Style.RESET_ALL}")
        sites = ["linkedin", "indeed", "google"]
    params["site_name"] = sites

    params["country_indeed"] = get_input("Country for Indeed/Glassdoor", default="India")
    params["full_description"] = get_yes_no("Fetch full descriptions? (slower)", default="n")

    return params


def colorize_age(date_posted):
    """Return colored age string based on how old the posting is."""
    if pd.isna(date_posted):
        return f"{Style.DIM}Unknown{Style.RESET_ALL}"

    if isinstance(date_posted, str):
        try:
            date_posted = pd.to_datetime(date_posted)
        except Exception:
            return f"{Style.DIM}{date_posted}{Style.RESET_ALL}"

    now = datetime.now()
    if hasattr(date_posted, "tzinfo") and date_posted.tzinfo is not None:
        now = datetime.now(timezone.utc)

    try:
        delta = now - date_posted
        hours = delta.total_seconds() / 3600
    except Exception:
        return f"{Style.DIM}{date_posted}{Style.RESET_ALL}"

    if hours < 1:
        label = "< 1 hr ago"
    elif hours < 24:
        label = f"{int(hours)} hrs ago"
    elif hours < 48:
        label = "1 day ago"
    else:
        label = f"{int(hours // 24)} days ago"

    if hours < 24:
        return f"{Fore.GREEN}{label}{Style.RESET_ALL}"
    elif hours < 72:
        return f"{Fore.YELLOW}{label}{Style.RESET_ALL}"
    else:
        return f"{Fore.WHITE}{label}{Style.RESET_ALL}"


def relevance_score(title, search_term):
    """Simple relevance score: how many search words appear in the title."""
    title_lower = (title or "").lower()
    words = search_term.lower().split()
    return sum(1 for w in words if w in title_lower)


def deduplicate(df):
    """Remove duplicate jobs based on company + title + location."""
    if df.empty:
        return df
    key_cols = []
    for col in ["company_name", "title", "location"]:
        if col in df.columns:
            key_cols.append(col)
    if not key_cols:
        return df

    before = len(df)
    df = df.drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)
    removed = before - len(df)
    if removed > 0:
        print(f"{Fore.YELLOW}  Removed {removed} duplicate job(s).{Style.RESET_ALL}")
    return df


def shorten_url(url, max_len=60):
    """Truncate long URLs for display."""
    if pd.isna(url) or not url:
        return "N/A"
    url = str(url)
    if len(url) <= max_len:
        return url
    return url[:max_len - 3] + "..."


def run_scraper(params):
    """Execute the job scraping with given parameters."""
    print(f"\n{Fore.CYAN}  Scraping jobs... This may take a minute.{Style.RESET_ALL}")

    try:
        jobs = scrape_jobs(
            site_name=params["site_name"],
            search_term=params["search_term"],
            location=params["location"],
            job_type=params["job_type"],
            is_remote=params["is_remote"],
            results_wanted=params["results_wanted"],
            hours_old=params["hours_old"],
            country_indeed=params["country_indeed"],
            full_description=params["full_description"],
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg or "rate" in err_msg:
            print(f"\n{Fore.RED}  LinkedIn rate limited. Consider using proxies or try Indeed/Google instead.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}  Error during scraping: {e}{Style.RESET_ALL}")
        return pd.DataFrame()

    if jobs is None or jobs.empty:
        print(f"\n{Fore.YELLOW}  No jobs found. Try:{Style.RESET_ALL}")
        print("    - Increasing max hours old")
        print("    - Adding more sites")
        print("    - Removing the location filter")
        print("    - Broadening your search term")
        return pd.DataFrame()

    print(f"{Fore.GREEN}  Scraping complete!{Style.RESET_ALL}")
    return jobs


def display_results(df, search_term):
    """Sort, display, and save results."""
    sites_found = df["site"].nunique() if "site" in df.columns else "?"
    print(f"\n{Fore.CYAN}  Found {len(df)} jobs across {sites_found} site(s){Style.RESET_ALL}\n")

    # Deduplicate
    df = deduplicate(df)

    # Sort: date_posted descending, then relevance
    df["_relevance"] = df["title"].apply(lambda t: relevance_score(t, search_term))

    if "date_posted" in df.columns:
        df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")
        df = df.sort_values(
            by=["date_posted", "_relevance"],
            ascending=[False, False],
        ).reset_index(drop=True)

    # Save full CSV
    csv_cols = [c for c in df.columns if not c.startswith("_")]
    df[csv_cols].to_csv("jobs_output.csv", index=False)
    print(f"{Fore.GREEN}  Full results saved to: jobs_output.csv{Style.RESET_ALL}")

    # Top 20
    top = df.head(20).copy()
    top[csv_cols].to_csv("top_20_jobs.csv", index=False)
    print(f"{Fore.GREEN}  Top 20 saved to: top_20_jobs.csv{Style.RESET_ALL}\n")

    # Build display table
    table_rows = []
    for i, (_, row) in enumerate(top.iterrows(), 1):
        title = str(row.get("title", "N/A"))[:40]
        company = str(row.get("company_name", "N/A"))[:20]
        location = str(row.get("location", "N/A"))[:20]
        job_type = str(row.get("job_type", "N/A"))
        posted = colorize_age(row.get("date_posted"))
        source = str(row.get("site", "N/A"))
        salary_min = row.get("min_amount")
        salary_max = row.get("max_amount")
        salary_curr = row.get("currency", "")

        salary = ""
        if pd.notna(salary_min) and pd.notna(salary_max):
            salary = f"{salary_curr}{int(salary_min)}-{int(salary_max)}"
        elif pd.notna(salary_min):
            salary = f"{salary_curr}{int(salary_min)}+"
        elif pd.notna(salary_max):
            salary = f"Up to {salary_curr}{int(salary_max)}"

        table_rows.append([i, title, company, location, job_type, posted, source, salary or "-"])

    headers = ["#", "Title", "Company", "Location", "Type", "Posted", "Source", "Salary"]
    print(f"{Fore.CYAN}Top 20 Jobs (sorted by recency):{Style.RESET_ALL}")
    print(tabulate(table_rows, headers=headers, tablefmt="rounded_grid"))

    # Apply links
    print(f"\n{Fore.CYAN}  Apply Links:{Style.RESET_ALL}")
    for i, (_, row) in enumerate(top.iterrows(), 1):
        url = row.get("job_url", "N/A")
        if pd.isna(url):
            url = "N/A"
        print(f"  {Fore.GREEN}{i}.{Style.RESET_ALL} {url}")

    return df


def keyword_filter(df):
    """Optionally filter results by keyword within descriptions/titles."""
    keyword = input(f"\n{Fore.CYAN}  Filter by keyword? (enter keyword or press Enter to skip): {Style.RESET_ALL}").strip()
    if not keyword:
        return

    search_cols = ["title", "description", "company_name", "location"]
    mask = pd.Series([False] * len(df), index=df.index)
    for col in search_cols:
        if col in df.columns:
            mask |= df[col].astype(str).str.contains(keyword, case=False, na=False)

    filtered = df[mask]
    if filtered.empty:
        print(f"{Fore.YELLOW}  No jobs matching \"{keyword}\".{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}  Found {len(filtered)} jobs matching \"{keyword}\"{Style.RESET_ALL}")
        table_rows = []
        for i, (_, row) in enumerate(filtered.head(20).iterrows(), 1):
            title = str(row.get("title", "N/A"))[:40]
            company = str(row.get("company_name", "N/A"))[:20]
            url = shorten_url(row.get("job_url"))
            table_rows.append([i, title, company, url])
        print(tabulate(table_rows, headers=["#", "Title", "Company", "URL"], tablefmt="rounded_grid"))

        # Save filtered
        csv_cols = [c for c in filtered.columns if not c.startswith("_")]
        filtered[csv_cols].to_csv(f"jobs_filtered_{keyword.lower()}.csv", index=False)
        print(f"{Fore.GREEN}  Filtered results saved to: jobs_filtered_{keyword.lower()}.csv{Style.RESET_ALL}")


def main():
    while True:
        print_banner()
        params = gather_inputs()
        df = run_scraper(params)

        if not df.empty:
            df = display_results(df, params["search_term"])
            keyword_filter(df)

        if not get_yes_no(f"\n{Fore.CYAN}Search again?{Style.RESET_ALL}", default="n"):
            print(f"\n{Fore.GREEN}  Happy job hunting! Good luck!{Style.RESET_ALL}\n")
            break


if __name__ == "__main__":
    main()
