"""
Oracle Cloud HCM scraper.

Oracle Fusion Cloud HCM candidate experience REST API.

Correct query format (discovered via browser network inspection):
  GET https://{tenant}.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions
      ?onlyData=true
      &expand=requisitionList
      &finder=findReqs;siteNumber={site_code},keyword="{term}",limit=25,offset=0,sortBy=RELEVANCY
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
    # Format: "company_name": ("tenant", "site_code")
    # Verify new entries with:
    #   curl "https://{tenant}.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber={site_code},keyword=%22security%22,limit=1"
    "JPMorgan Chase": ("jpmc", "CX_1001"),
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security"]


def scrape_oracle_cloud(company_name, tenant, site_code):
    """Scrape Oracle Cloud HCM candidate experience for job listings."""
    base = f"https://{tenant}.fa.oraclecloud.com"
    api_url = f"{base}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    results = []
    seen = set()

    for term in SEARCH_TERMS:
        offset = 0
        limit = 25

        while True:
            # Use the finder parameter format the Oracle HCM UI actually uses
            finder = (
                f"findReqs;siteNumber={site_code},"
                f'keyword="{requests.utils.quote(term)}",'
                f"limit={limit},offset={offset},sortBy=RELEVANCY"
            )
            params = {
                "onlyData": "true",
                "expand": "requisitionList",
                "finder": finder,
            }
            try:
                resp = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[!] Oracle Cloud error for {company_name} ({term}): {e}")
                break

            items = data.get("items", [])
            if not items:
                break

            req_list = items[0].get("requisitionList", [])
            if not req_list:
                break

            for job in req_list:
                req_id = str(job.get("Id", ""))
                if not req_id or req_id in seen:
                    continue
                seen.add(req_id)

                title = job.get("Title", "")
                if is_cybersecurity(title) and is_entry_level(title, ""):
                    loc = job.get("PrimaryLocation", "N/A")
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
    for company_name, (tenant, site_code) in ORACLE_CLOUD_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_oracle_cloud(company_name, tenant, site_code))
        time.sleep(1)
    return all_jobs
