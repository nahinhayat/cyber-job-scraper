"""
Taleo (Oracle) ATS scraper.

Taleo is Oracle's legacy ATS, used by many large enterprises.
Note: Oracle itself uses Oracle Cloud HCM (not Taleo) — see oracle_cloud.py.

REST API pattern:
  GET https://{tenant}.taleo.net/careersection/rest/jobboard/searchjobs
      ?multilineEnabled=false&searchByKeyword=1&keyword=cybersecurity&rows=25&start=0
"""

import time
import requests
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Format: "company_name": ("taleo_tenant", "career_section_name")
TALEO_COMPANIES = {
    # All previously tested tenants returned DNS failures — {tenant}.taleo.net
    # subdomains did not resolve, indicating companies have migrated away from Taleo.
    # To add a company, first verify: curl -I https://{tenant}.taleo.net
    # (should return 200/400, not a connection error)
    # Oracle uses Oracle Cloud HCM — handled in oracle_cloud.py
    # Lockheed Martin uses BrassRing — not covered here
    # Northrop Grumman uses Eightfold — not covered here
}


def scrape_taleo(company_name, tenant, section):
    """Query Taleo REST API for cybersecurity job listings."""
    results = []
    seen = set()
    search_terms = ["cybersecurity", "security analyst", "information security"]

    for term in search_terms:
        start = 0
        rows = 25

        while True:
            url = (
                f"https://{tenant}.taleo.net/careersection/rest/jobboard/searchjobs"
                f"?multilineEnabled=false&searchByKeyword=1"
                f"&keyword={requests.utils.quote(term)}&rows={rows}&start={start}"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[!] Taleo error for {company_name} ({term}): {e}")
                break

            jobs = data.get("requisitionList", [])
            if not jobs:
                break

            for job in jobs:
                req_id = str(job.get("contestNo", ""))
                if req_id in seen:
                    continue
                seen.add(req_id)

                title = job.get("title", "")
                if is_cybersecurity(title) and is_entry_level(title, ""):
                    location_parts = [
                        job.get("city", ""),
                        job.get("stateShortName", ""),
                        job.get("countryName", ""),
                    ]
                    location = ", ".join(p for p in location_parts if p) or "N/A"
                    results.append({
                        "company": company_name,
                        "title": title,
                        "location": location,
                        "url": f"https://{tenant}.taleo.net/careersection/{section}/jobdetail.ftl?job={req_id}",
                        "source": "taleo",
                    })

            total = data.get("pagingData", {}).get("totalCount", 0)
            start += rows
            if start >= total:
                break
            time.sleep(0.3)

    return results


def scrape_all_taleo():
    all_jobs = []
    for company_name, (tenant, section) in TALEO_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_taleo(company_name, tenant, section))
        time.sleep(1)
    return all_jobs
