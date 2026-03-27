"""
Oracle Cloud HCM scraper.

Oracle Fusion Cloud HCM is used by JPMorgan Chase, Oracle, and many other
Fortune 500 companies. The candidate experience page can be scraped for
job listings using the public-facing REST API.

API pattern:
  GET https://{tenant}.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions
      ?expand=requisitionList&onlyData=true&q=Title%3D*cybersecurity*&limit=25&offset=0
"""

import time
import requests
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Format: "company_name": ("tenant", "datacenter", "site_code")
# tenant:     subdomain before .fa.
# datacenter: region like "us2", "us6", or "" for dedicated instances
# site_code:  the CX site code used in the candidate portal URL (CX_1001, etc.)
ORACLE_CLOUD_COMPANIES = {
    "JPMorgan Chase": ("jpmc", "", "CX_1001"),
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security"]


def _base_url(tenant, datacenter):
    if datacenter:
        return f"https://{tenant}.fa.{datacenter}.oraclecloud.com"
    return f"https://{tenant}.fa.oraclecloud.com"


def scrape_oracle_cloud(company_name, tenant, datacenter, site_code):
    """Scrape Oracle Cloud HCM candidate experience for job listings."""
    base = _base_url(tenant, datacenter)
    results = []
    seen = set()

    for term in SEARCH_TERMS:
        offset = 0
        limit = 25

        while True:
            url = (
                f"{base}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
                f"?expand=requisitionList&onlyData=true&limit={limit}&offset={offset}"
                f"&q=Title%3D*{requests.utils.quote(term)}*"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[!] Oracle Cloud error for {company_name} ({term}): {e}")
                break

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                req_list = item.get("requisitionList", [])
                for job in req_list:
                    req_id = str(job.get("Id", job.get("requisitionId", "")))
                    if req_id in seen:
                        continue
                    seen.add(req_id)

                    title = job.get("Title", job.get("requisitionTitle", ""))
                    if is_cybersecurity(title) and is_entry_level(title, ""):
                        loc = job.get("PrimaryLocation", job.get("primaryLocation", "N/A"))
                        job_url = (
                            f"{base}/hcmUI/CandidateExperience/en/sites/{site_code}"
                            f"/requisitions/preview/{req_id}"
                        )
                        results.append({
                            "company": company_name,
                            "title": title,
                            "location": loc,
                            "url": job_url,
                            "source": "oracle_cloud",
                        })

            total = data.get("count", 0)
            offset += limit
            if offset >= total:
                break
            time.sleep(0.3)

    return results


def scrape_all_oracle_cloud():
    all_jobs = []
    for company_name, (tenant, datacenter, site_code) in ORACLE_CLOUD_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_oracle_cloud(company_name, tenant, datacenter, site_code))
        time.sleep(1)
    return all_jobs
