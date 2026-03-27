"""
Workday career page scraper.

How to add a new company:
  1. Visit the company's careers page in your browser (e.g. careers.boozallen.com).
  2. It will redirect to a Workday URL like:
       https://<tenant>.wd<n>.myworkdayjobs.com/<SITE_NAME>/...
  3. Run the verifier to confirm the path works:
       python verify_workday.py <tenant> <wdN> <SITE_NAME>
     Example: python verify_workday.py boozallen wd1 EXP
  4. If it prints OK, add the entry to WORKDAY_COMPANIES below.
"""

import time
import requests
import requests.exceptions
from filters import is_entry_level, is_cybersecurity

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Format: "company_name": ("tenant", "wd_number", "site_path")
# wd_number already includes the "wd" prefix, e.g. "wd5"
WORKDAY_COMPANIES = {
    # --- Verified working ---
    "CrowdStrike":        ("crowdstrike", "wd5", "crowdstrikecareers"),
    "MITRE":              ("mitre",       "wd5", "MITRE"),
    "Booz Allen Hamilton":("bah",         "wd1", "BAH_Jobs"),

    # --- Confirmed via career page inspection ---
    "T-Mobile":           ("tmobile",     "wd1", "External"),
    "Comcast":            ("comcast",     "wd5", "Comcast_Careers"),
    "Target":             ("target",      "wd5", "targetcareers"),
    "Dell":               ("dell",        "wd1", "External"),
    "Walmart":            ("walmart",     "wd5", "WalmartExternal"),

    # Note: Palo Alto uses TalentBrew, Lockheed uses BrassRing,
    # Northrop uses Eightfold, ManTech uses Avature — not Workday.
    # Add more verified companies with: python verify_workday.py <tenant> <wdN> <site>
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security"]


def _build_api_url(tenant, wd_num, site):
    # wd_num already includes the "wd" prefix (e.g. "wd5"), so don't add it again
    return (
        f"https://{tenant}.{wd_num}.myworkdayjobs.com"
        f"/wday/cxs/{tenant}/{site}/jobs"
    )


def scrape_workday(company_name, tenant, wd_num, site):
    """Query a company's Workday jobs API for cybersecurity openings."""
    api_url = _build_api_url(tenant, wd_num, site)
    base_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/{site}"

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    try:
        session.get(base_url, timeout=15)
    except Exception:
        pass

    csrf_token = session.cookies.get("XSRF-TOKEN", "")

    post_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": f"https://{tenant}.{wd_num}.myworkdayjobs.com",
        "Referer": base_url,
    }
    if csrf_token:
        post_headers["X-XSRF-TOKEN"] = csrf_token

    results = []
    seen = set()

    for term in SEARCH_TERMS:
        offset = 0
        while True:
            payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": offset,
                "searchText": term,
            }
            try:
                resp = session.post(api_url, headers=post_headers, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.HTTPError as e:
                print(f"[!] Workday error for {company_name} ({term}): {e.response.status_code}")
                break
            except Exception as e:
                print(f"[!] Workday error for {company_name} ({term}): {e}")
                break

            postings = data.get("jobPostings", [])
            if not postings:
                break

            for job in postings:
                title = job.get("title", "")
                job_url = base_url + job.get("externalPath", "")

                if job_url in seen:
                    continue
                seen.add(job_url)

                if is_cybersecurity(title) and is_entry_level(title, ""):
                    results.append({
                        "company": company_name,
                        "title": title,
                        "location": job.get("locationsText", "N/A"),
                        "url": job_url,
                        "source": "workday",
                    })

            total = data.get("total", 0)
            offset += len(postings)
            if offset >= total:
                break

            time.sleep(0.3)

    return results


def scrape_all_workday():
    all_jobs = []
    for company_name, (tenant, wd_num, site) in WORKDAY_COMPANIES.items():
        print(f"    -> {company_name}")
        jobs = scrape_workday(company_name, tenant, wd_num, site)
        all_jobs.extend(jobs)
        time.sleep(1)
    return all_jobs
