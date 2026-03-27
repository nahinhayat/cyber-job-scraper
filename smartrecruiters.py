"""
SmartRecruiters ATS scraper.

SmartRecruiters exposes a fully public REST API — no auth, no browser needed.
Used by many Fortune 500 companies including Visa, Unilever, LinkedIn, and others.

API: GET https://api.smartrecruiters.com/v1/companies/{slug}/postings?q=cybersecurity
"""

import time
import requests
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CyberJobScraper/1.0)",
    "Accept": "application/json",
}

# Format: "company_name": "smartrecruiters_slug"
# Find slug by visiting jobs.smartrecruiters.com/<slug> or the company's careers page
SMARTRECRUITERS_COMPANIES = {
    "Visa":             "Visa-2",
    "McDonald's":       "McDonalds",
    "Starbucks":        "Starbucks",
    "Pfizer":           "Pfizer",
    "Johnson & Johnson":"JohnsonJohnson",
    "Unilever":         "Unilever",
    "Bosch":            "BoschGroup",
    "Adidas":           "adidas",
    "IKEA":             "IKEA-Group",
    "Ericsson":         "Ericsson",
}


def scrape_smartrecruiters(company_name, slug):
    """Query SmartRecruiters public API."""
    results = []
    seen = set()
    offset = 0
    limit = 100

    while True:
        url = (
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
            f"?q=cybersecurity+security&limit={limit}&offset={offset}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[!] SmartRecruiters error for {company_name}: {e}")
            break

        postings = data.get("content", [])
        if not postings:
            break

        for job in postings:
            job_id = job.get("id", "")
            if job_id in seen:
                continue
            seen.add(job_id)

            title = job.get("name", "")
            location = job.get("location", {})
            location_str = ", ".join(filter(None, [
                location.get("city", ""),
                location.get("region", ""),
                location.get("country", ""),
            ])) or "N/A"

            if is_cybersecurity(title) and is_entry_level(title, job.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", "")):
                results.append({
                    "company": company_name,
                    "title": title,
                    "location": location_str,
                    "url": f"https://jobs.smartrecruiters.com/{slug}/{job_id}",
                    "source": "smartrecruiters",
                })

        total = data.get("totalFound", 0)
        offset += len(postings)
        if offset >= total:
            break
        time.sleep(0.3)

    return results


def scrape_all_smartrecruiters():
    all_jobs = []
    for company_name, slug in SMARTRECRUITERS_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_smartrecruiters(company_name, slug))
        time.sleep(1)
    return all_jobs
