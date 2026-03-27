"""
SAP SuccessFactors ATS scraper.

SuccessFactors is SAP's ATS, used by many Fortune 500 companies including
large manufacturers, energy companies, and conglomerates.

Public API:
  GET https://{tenant}.jobs.erp.sap/api/jobs?keyword=cybersecurity&limit=25&offset=0
  or
  GET https://{tenant}.wd3.myworkdayjobs.com  (some use Workday via SAP)
"""

import time
import requests
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Format: "company_name": "sf_tenant"
# Find by visiting the company's careers page and looking for sap.com or successfactors.com
SUCCESSFACTORS_COMPANIES = {
    # All previously tested companies returned DNS failures — {tenant}.jobs.erp.sap
    # is not the correct hostname for SAP SuccessFactors public job APIs.
    # SuccessFactors instances are hosted at {tenant}.successfactors.com with
    # company-specific configurations that require per-tenant research.
    # Note: ExxonMobil, Chevron, ConocoPhillips are also covered in workday.py
    # (many energy companies use Workday, not SuccessFactors, for US hiring).
}


def scrape_successfactors(company_name, tenant):
    """Query SAP SuccessFactors careers API."""
    results = []
    seen = set()
    search_terms = ["cybersecurity", "security", "information security"]

    for term in search_terms:
        offset = 0
        limit = 25

        while True:
            # SuccessFactors REST API
            url = (
                f"https://{tenant}.jobs.erp.sap/api/jobs"
                f"?keyword={requests.utils.quote(term)}&limit={limit}&offset={offset}"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[!] SuccessFactors error for {company_name} ({term}): {e}")
                break

            jobs = data.get("value", []) or data.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                job_id = str(job.get("jobReqId", job.get("id", "")))
                if job_id in seen:
                    continue
                seen.add(job_id)

                title = job.get("jobTitle", job.get("title", ""))
                if is_cybersecurity(title) and is_entry_level(title, job.get("jobDescription", "")):
                    results.append({
                        "company": company_name,
                        "title": title,
                        "location": job.get("locationName", job.get("location", "N/A")),
                        "url": f"https://{tenant}.jobs.erp.sap/job/{job_id}",
                        "source": "successfactors",
                    })

            total = data.get("count", data.get("total", 0))
            offset += limit
            if offset >= total:
                break
            time.sleep(0.3)

    return results


def scrape_all_successfactors():
    all_jobs = []
    for company_name, tenant in SUCCESSFACTORS_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_successfactors(company_name, tenant))
        time.sleep(1)
    return all_jobs
