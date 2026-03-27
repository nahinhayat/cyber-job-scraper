"""
Workday career page scraper.

Many large companies (CrowdStrike, Palo Alto Networks, Raytheon, etc.) host
their jobs on Workday. Each company's Workday instance exposes a public JSON
API that can be queried directly — no browser or login required.

How to find a company's Workday tenant:
  1. Go to the company's careers page and click any job listing.
  2. The URL will look like:
       https://<tenant>.wd<n>.myworkdayjobs.com/<site>/job/<job-title>/<job-id>
  3. Copy the <tenant> and <n> values into WORKDAY_COMPANIES below.
"""

import time
import requests
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CyberJobScraper/1.0)",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Format: "company_name": ("tenant", "wd_number", "site_path")
# site_path is the path segment after myworkdayjobs.com/ in the job board URL
WORKDAY_COMPANIES = {
    "CrowdStrike":        ("crowdstrike",         "wd5", "crowdstrikecareers"),
    "Palo Alto Networks": ("paloaltonetworks",     "wd1", "external"),
    "Booz Allen Hamilton":("boozallen",            "wd1", "EXP"),
    "Lockheed Martin":    ("lmcocareers",          "wd1", "LMCareers"),
    "Raytheon":           ("rtx",                  "wd1", "RTX"),
    "Northrop Grumman":   ("ngc",                  "wd1", "NGC_External_Site"),
    "MITRE":              ("mitre",                "wd5", "MITRE"),
    "Leidos":             ("leidos",               "wd1", "Leidos"),
    "ManTech":            ("mantech",              "wd1", "mantech"),
    "CACI":               ("caci",                 "wd1", "CACI"),
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security"]


def _build_api_url(tenant: str, wd_num: str, site: str) -> str:
    return (
        f"https://{tenant}.wd{wd_num}.myworkdayjobs.com"
        f"/wday/cxs/{tenant}/{site}/jobs"
    )


def scrape_workday(company_name: str, tenant: str, wd_num: str, site: str) -> list[dict]:
    """Query a company's Workday jobs API for cybersecurity openings."""
    url = _build_api_url(tenant, wd_num, site)
    base_url = f"https://{tenant}.wd{wd_num}.myworkdayjobs.com/{site}"
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
                resp = requests.post(url, headers=HEADERS, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
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


def scrape_all_workday() -> list[dict]:
    all_jobs = []
    for company_name, (tenant, wd_num, site) in WORKDAY_COMPANIES.items():
        print(f"    -> {company_name}")
        jobs = scrape_workday(company_name, tenant, wd_num, site)
        all_jobs.extend(jobs)
        time.sleep(1)
    return all_jobs
