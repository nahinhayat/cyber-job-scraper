"""
Workday career page scraper.

Only companies whose Workday tenant publicly exposes the CXS jobs API
are listed here. Companies with internal-only Workday tenants (blank page
when visited in browser) are handled in playwright_scraper.py instead.

How to verify a new company before adding:
  python verify_workday.py <tenant> <wdN> <SITE_NAME>
"""

import time
import requests
import requests.exceptions
from filters import is_entry_level, is_cybersecurity

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Only companies CONFIRMED to return 200 from the CXS API without auth.
# Test with: python verify_workday.py <tenant> <wdN> <site>
WORKDAY_COMPANIES = {

    # ── Technology ────────────────────────────────────────────────────────────
    "Cisco":              ("cisco",         "wd5", "Cisco_Careers"),
    "Intel":              ("intel",         "wd1", "External"),
    "Dell":               ("dell",          "wd1", "External"),
    "HP Inc":             ("hp",            "wd5", "ExternalCareerSite"),
    "Nvidia":             ("nvidia",        "wd5", "nvidiaexternalcareersite"),
    "Broadcom":           ("broadcom",      "wd1", "External_Career"),

    # ── Cybersecurity ─────────────────────────────────────────────────────────
    "CrowdStrike":        ("crowdstrike",   "wd5", "crowdstrikecareers"),
    "MITRE":              ("mitre",         "wd5", "MITRE"),

    # ── Defense / Government Contractors ─────────────────────────────────────
    "Booz Allen Hamilton": ("bah",          "wd1", "BAH_Jobs"),
    "Leidos":             ("leidos",        "wd5", "external"),
    "CACI":               ("caci",          "wd1", "External"),

    # ── Telecom ───────────────────────────────────────────────────────────────
    "T-Mobile":           ("tmobile",       "wd1", "External"),
    "Comcast":            ("comcast",       "wd5", "Comcast_Careers"),

    # ── Retail ────────────────────────────────────────────────────────────────
    "Walmart":            ("walmart",       "wd5", "WalmartExternal"),
    "Target":             ("target",        "wd5", "targetcareers"),
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security"]


def _build_api_url(tenant, wd_num, site):
    return (
        f"https://{tenant}.{wd_num}.myworkdayjobs.com"
        f"/wday/cxs/{tenant}/{site}/jobs"
    )


def scrape_workday(company_name, tenant, wd_num, site):
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
            payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": term}
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
        all_jobs.extend(scrape_workday(company_name, tenant, wd_num, site))
        time.sleep(1)
    return all_jobs
